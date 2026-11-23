import json
import os
import shlex
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/engineering/docmate"
INSTALLER = ROOT / "scripts/install-docmate.sh"


def node_path() -> str:
    found = shutil.which("node")
    assert found is not None, "node is required for installer tests"
    return str(Path(found).parent)


def fake_bin(tmp_path: Path, names: List[str]) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    for name in names:
        path = bin_dir / name
        path.write_text("#!/usr/bin/env bash\nexit 0\n")
        path.chmod(0o755)
    curl = bin_dir / "curl"
    curl.write_text(
        "#!/usr/bin/env bash\necho 'Unexpected test download' >&2\nexit 1\n"
    )
    curl.chmod(0o755)
    return bin_dir


def isolated_environment(home: Path) -> dict:
    env = os.environ.copy()
    for key in (
        "XDG_CONFIG_HOME",
        "XDG_STATE_HOME",
        "DOCMATE_REPO",
        "DOCMATE_BRANCH",
        "DOCMATE_SCAN_MAX_DEPTH",
    ):
        env.pop(key, None)
    env["HOME"] = str(home)
    (home / "tmp").mkdir(exist_ok=True)
    env["TMPDIR"] = str(home / "tmp")
    env["DOCMATE_USE_LOCAL_CACHE"] = "true"
    return env


def run_install_args(
    home: Path,
    args: List[str],
    extra_path: Optional[Path] = None,
    input_text: Optional[str] = None,
    timeout: int = 15,
    fake_commands: Optional[List[str]] = None,
    extra_env: Optional[dict] = None,
):
    env = isolated_environment(home)
    if fake_commands is None:
        fake_commands = ["openclaw", "claude", "opencode", "codex", "hermes"]
    bin_dir = fake_bin(home, fake_commands)
    node_executable = Path(node_path()) / "node"
    node_wrapper = bin_dir / "node"
    node_wrapper.write_text(f'#!/usr/bin/env bash\nexec {node_executable} "$@"\n')
    node_wrapper.chmod(0o755)
    if extra_env:
        env.update(extra_env)
    path_entries = [str(bin_dir), "/usr/bin", "/bin"]
    if extra_path:
        path_entries.insert(0, str(extra_path))
    env["PATH"] = ":".join(path_entries)
    return subprocess.run(
        args,
        text=True,
        input=input_text,
        capture_output=True,
        env=env,
        check=False,
        timeout=timeout,
    )


def backup_roots(home: Path) -> List[Path]:
    backup_base = home / ".local" / "state" / "docmate" / "backups"
    if not backup_base.exists():
        return []
    return sorted(backup_base.glob("install-*"))


def seed_legacy_install(target: Path, repository: Path, *, language: str) -> Path:
    references = target / "references"
    references.mkdir(parents=True)
    heading = "必读 Catalog 步骤" if language == "zh" else "Required Catalog Step"
    (target / "SKILL.md").write_text(f"# DocMate\n\n## {heading}\n\nLegacy release.\n")
    catalog = references / "docmate.catalog.json"
    value = {
        "defaults": {"update": {"mode": "off"}},
        "repos": [
            {
                "name": "docs",
                "path": str(repository),
                "aliases": ["文档", "handbook"],
                "description": "Team documentation",
                "baseBranchCandidates": ["docs/release", "main"],
            },
        ],
    }
    catalog.write_text(json.dumps(value, ensure_ascii=False, indent=4) + "\n")
    return catalog


def run_install(
    home: Path,
    repo: Path,
    extra_args: Optional[List[str]] = None,
    path_flag: str = "--repo",
):
    args = [
        "bash",
        str(INSTALLER),
        "--yes",
        path_flag,
        str(repo),
        "--hosts",
        "all",
        "--existing",
        "backup",
    ]
    if extra_args:
        args.extend(extra_args)
    return run_install_args(home, args)


def run_pty_command(command: str, input_text: str, env: dict, timeout: int = 15):
    if shutil.which("script"):
        script_probe = subprocess.run(
            ["script", "-qfec", "true", "/dev/null"],
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
        )
        if script_probe.returncode == 0:
            return subprocess.run(
                ["script", "-qfec", command, "/dev/null"],
                text=True,
                input=input_text,
                capture_output=True,
                env=env,
                check=False,
                timeout=timeout,
            )

    if shutil.which("expect"):
        expect_env = env.copy()
        expect_env["DOCMATE_TEST_PTY_COMMAND"] = command
        expect_env["DOCMATE_TEST_PTY_INPUT"] = input_text
        expect_env["DOCMATE_TEST_PTY_TIMEOUT"] = str(timeout)
        return subprocess.run(
            [
                "expect",
                "-c",
                """
set timeout $env(DOCMATE_TEST_PTY_TIMEOUT)
spawn -noecho /bin/bash -lc $env(DOCMATE_TEST_PTY_COMMAND)
send -- $env(DOCMATE_TEST_PTY_INPUT)
expect eof
set wait_result [wait]
exit [lindex $wait_result 3]
""",
            ],
            text=True,
            capture_output=True,
            env=expect_env,
            check=False,
            timeout=timeout + 5,
        )

    raise unittest.SkipTest(
        "script -qfec or expect is required for pseudo-tty installer test"
    )


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(
            self.enterContext(TemporaryDirectory(prefix="docmate-test-"))
        ).resolve()

    def test_upgrade_keeps_chinese_legacy_catalog_and_shared_links(self):
        home = self.tmp_path / "home"
        target = home / ".agents/skills/docmate"
        catalog = seed_legacy_install(target, self.tmp_path / "docs", language="zh")
        original_catalog = catalog.read_bytes()
        original_skill = (target / "SKILL.md").read_bytes()
        hosts = [home / ".claude/skills/docmate", home / ".openclaw/skills/docmate"]
        for host in hosts:
            host.parent.mkdir(parents=True)
            host.symlink_to(target)

        result = run_install_args(home, ["bash", str(INSTALLER), "--upgrade"])

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(catalog.read_bytes(), original_catalog)
        self.assertFalse(catalog.is_symlink())
        self.assertFalse((home / ".config/docmate/catalog.json").exists())
        for host in hosts:
            self.assertEqual(host.readlink(), target)
        self.assertEqual(
            (target / "SKILL.md").read_bytes(), (SKILL / "SKILL.zh.md").read_bytes()
        )
        self.assertTrue((target / "references/update-workflow.md").is_file())
        self.assertIn(
            "allow_implicit_invocation: false",
            (target / "agents/openai.yaml").read_text(),
        )
        self.assertIn(f"Catalog: {catalog}", result.stdout)
        (backup,) = backup_roots(home)
        self.assertEqual(
            (backup / "canonical-docmate/SKILL.md").read_bytes(), original_skill
        )
        self.assertEqual(
            (backup / "canonical-docmate/references/docmate.catalog.json").read_bytes(),
            original_catalog,
        )

    def test_upgrade_uses_the_selected_single_host_catalog(self):
        home = self.tmp_path / "home"
        target = home / ".openclaw/skills/docmate"
        catalog = seed_legacy_install(target, self.tmp_path / "docs", language="en")
        original_catalog = catalog.read_bytes()
        shared = home / ".agents/skills/docmate"
        shared_catalog = seed_legacy_install(
            shared, self.tmp_path / "shared-docs", language="zh"
        )
        original_shared = shared_catalog.read_bytes()
        original_shared_skill = (shared / "SKILL.md").read_bytes()

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--upgrade",
                "--install-mode",
                "single",
                "--hosts",
                "openclaw",
            ],
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(catalog.read_bytes(), original_catalog)
        self.assertEqual(shared_catalog.read_bytes(), original_shared)
        self.assertEqual((shared / "SKILL.md").read_bytes(), original_shared_skill)
        self.assertEqual(
            (target / "SKILL.md").read_bytes(), (SKILL / "SKILL.md").read_bytes()
        )
        self.assertFalse(target.is_symlink())

    def test_upgrade_rejects_invalid_legacy_catalog_before_any_replacement(self):
        home = self.tmp_path / "home"
        target = home / ".agents/skills/docmate"
        catalog = seed_legacy_install(target, self.tmp_path / "docs", language="en")
        external = home / ".config/docmate/catalog.json"
        external.parent.mkdir(parents=True)
        external.write_bytes(catalog.read_bytes())
        catalog.write_text("{}\n")
        original_skill = (target / "SKILL.md").read_bytes()

        result = run_install_args(home, ["bash", str(INSTALLER), "--upgrade"])

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(catalog.read_text(), "{}\n")
        self.assertEqual((target / "SKILL.md").read_bytes(), original_skill)
        self.assertFalse((target / "agents").exists())
        self.assertEqual(backup_roots(home), [])

    def test_piped_upgrade_stages_remote_assets_from_the_collection(self):
        home = self.tmp_path / "home"
        target = home / ".agents/skills/docmate"
        catalog = seed_legacy_install(target, self.tmp_path / "docs", language="en")
        original_catalog = catalog.read_bytes()
        fake_tools = self.tmp_path / "fake-tools"
        fake_tools.mkdir()
        fake_curl = fake_tools / "curl"
        fake_curl.write_text(
            "#!/usr/bin/env bash\n"
            "base=https://raw.githubusercontent.com/wufei-png/skills/main/skills/engineering/docmate/\n"
            'case "$2" in "$base"*) cp "$DOCMATE_TEST_PAYLOAD/${2#"$base"}" "$4" ;; *) exit 8 ;; esac\n'
        )
        fake_curl.chmod(0o755)

        result = run_install_args(
            home,
            ["bash", "-s", "--", "--upgrade"],
            input_text=INSTALLER.read_text(),
            extra_path=fake_tools,
            extra_env={
                "DOCMATE_TEST_PAYLOAD": str(SKILL),
                "DOCMATE_USE_LOCAL_CACHE": "false",
            },
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(catalog.read_bytes(), original_catalog)
        self.assertEqual(
            (target / "SKILL.md").read_bytes(), (SKILL / "SKILL.md").read_bytes()
        )
        self.assertTrue((target / "references/setup.md").exists())
        self.assertTrue((target / "references/update-workflow.md").is_file())

    def test_piped_installer_without_repo_exits_when_interactive_input_is_unavailable(
        self,
    ):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()

        result = run_install_args(
            home,
            [
                "bash",
            ],
            input_text=INSTALLER.read_text(),
            timeout=5,
        )

        assert result.returncode != 0
        assert "no repositories selected" in result.stderr
        assert "BASH_SOURCE" not in result.stderr
        assert "Invalid choice" not in result.stdout

    def test_global_install_creates_canonical_skill_and_all_host_links(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo)

        assert result.returncode == 0, result.stdout + result.stderr
        canonical = home / ".agents" / "skills" / "docmate"
        assert (canonical / "SKILL.md").exists()
        assert (canonical / "references" / "docmate.catalog.json").exists()
        assert (canonical / "references" / "docmate.catalog.example.json").is_file()
        assert (canonical / "agents" / "openai.yaml").is_file()
        assert (canonical / "LICENSE").read_bytes() == (SKILL / "LICENSE").read_bytes()
        catalog_link = canonical / "references/docmate.catalog.json"
        assert catalog_link.readlink() == home / ".config/docmate/catalog.json"
        assert not (canonical / "references" / "repair-handoff.template.md").exists()
        assert not (canonical / "references" / "docmate_update.sh").exists()

        expected_links = [
            home / ".openclaw" / "skills" / "docmate",
            home / ".claude" / "skills" / "docmate",
            home / ".config" / "opencode" / "skills" / "docmate",
            home / ".hermes" / "skills" / "software-development" / "docmate",
        ]
        for link in expected_links:
            assert link.is_symlink()
            assert link.resolve() == canonical
        assert not (home / ".codex" / "skills" / "docmate").exists()

        catalog = json.loads(
            (canonical / "references" / "docmate.catalog.json").read_text()
        )
        assert sorted(catalog) == ["defaults", "repos"]
        assert catalog["repos"][0]["name"] == "docs-project"
        assert catalog["repos"][0]["path"] == str(repo)
        assert "description" not in catalog["repos"][0]
        assert "aliases" not in catalog["repos"][0]
        assert "update" not in catalog["repos"][0]
        assert "installHosts" not in catalog
        assert catalog["defaults"]["update"]["mode"] == "ask"
        assert "Optional catalog enrichment" in result.stdout
        assert "repos[].description" in result.stdout
        assert "paste it into your own agent" in result.stdout
        assert (
            str(canonical / "references/fill-catalog-descriptions.md") in result.stdout
        )
        assert f"Catalog: {catalog_link.readlink()}" in result.stdout
        assert "repos[].aliases: fill manually" in result.stdout
        assert "repos[].baseBranchCandidates" in result.stdout

    def test_non_interactive_install_defaults_to_english_skill(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo)

        assert result.returncode == 0, result.stdout + result.stderr
        skill = (home / ".agents" / "skills" / "docmate" / "SKILL.md").read_text()
        assert "Required Catalog Step" in skill
        assert "必读 Catalog 步骤" not in skill
        assert "Deployed English DocMate skill." in result.stdout

    def test_non_interactive_language_zh_deploys_chinese_skill(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo, ["--language", "zh"])

        assert result.returncode == 0, result.stdout + result.stderr
        skill = (home / ".agents" / "skills" / "docmate" / "SKILL.md").read_text()
        assert "必读 Catalog 步骤" in skill
        assert "Required Catalog Step" not in skill
        assert "Deployed Chinese DocMate skill." in result.stdout

    def test_yes_without_hosts_uses_global_detected_hosts(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--repo",
                str(repo),
                "--existing",
                "backup",
            ],
            fake_commands=["opencode", "codex"],
        )

        assert result.returncode == 0, result.stdout + result.stderr
        canonical = home / ".agents" / "skills" / "docmate"
        assert (canonical / "SKILL.md").exists()
        assert (home / ".config" / "opencode" / "skills" / "docmate").is_symlink()
        assert not (home / ".openclaw" / "skills" / "docmate").exists()
        assert not (home / ".claude" / "skills" / "docmate").exists()
        assert not (
            home / ".hermes" / "skills" / "software-development" / "docmate"
        ).exists()

        catalog = json.loads(
            (canonical / "references" / "docmate.catalog.json").read_text()
        )
        assert "installHosts" not in catalog

    def test_single_host_install_writes_directly_to_selected_host(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--repo",
                str(repo),
                "--install-mode",
                "single",
                "--hosts",
                "openclaw",
                "--existing",
                "backup",
            ],
        )

        assert result.returncode == 0, result.stdout + result.stderr
        direct_target = home / ".openclaw" / "skills" / "docmate"
        assert (direct_target / "SKILL.md").exists()
        assert not direct_target.is_symlink()
        assert not (home / ".agents" / "skills" / "docmate").exists()

        catalog = json.loads(
            (direct_target / "references" / "docmate.catalog.json").read_text()
        )
        assert "installHosts" not in catalog
        catalog_link = direct_target / "references/docmate.catalog.json"
        assert (
            catalog_link.readlink() == home / ".config/docmate/catalogs/openclaw.json"
        )

    def test_interactive_agent_platform_mode_menu_lists_supported_platforms(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        bin_dir = fake_bin(home, [])
        node_executable = Path(node_path()) / "node"
        node_wrapper = bin_dir / "node"
        node_wrapper.write_text(f'#!/usr/bin/env bash\nexec {node_executable} "$@"\n')
        node_wrapper.chmod(0o755)

        env = isolated_environment(home)
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        env["TERM"] = "xterm"

        command = (
            f"bash {shlex.quote(str(INSTALLER))} "
            f"--repo {shlex.quote(str(repo))} --update-mode ask --existing overwrite"
        )
        result = run_pty_command(command, "\r\r", env)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Skill language / 选择语言" in result.stdout
        assert "Agent platform mode" in result.stdout
        assert "All detected agent platforms (recommended)" in result.stdout
        assert "OpenClaw, Claude Code, OpenCode, Codex, Hermes" in result.stdout

    def test_interactive_single_host_menu_supports_arrow_enter_selection(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        bin_dir = fake_bin(home, [])
        node_executable = Path(node_path()) / "node"
        node_wrapper = bin_dir / "node"
        node_wrapper.write_text(f'#!/usr/bin/env bash\nexec {node_executable} "$@"\n')
        node_wrapper.chmod(0o755)

        env = isolated_environment(home)
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        env["TERM"] = "xterm"

        command = (
            f"bash {shlex.quote(str(INSTALLER))} "
            f"--repo {shlex.quote(str(repo))} --update-mode auto --install-mode single --existing overwrite"
        )
        result = run_pty_command(command, "\r\x1b[B\x1b[B\r", env)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Skill language / 选择语言" in result.stdout
        assert "Use Up/Down to move, Space or Enter to select." in result.stdout
        assert "Select one agent platform" in result.stdout
        assert (
            home / ".config" / "opencode" / "skills" / "docmate" / "SKILL.md"
        ).exists()
        assert not (home / ".openclaw" / "skills" / "docmate").exists()

    def test_interactive_update_mode_menu_writes_global_default(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        bin_dir = fake_bin(home, [])
        node_executable = Path(node_path()) / "node"
        node_wrapper = bin_dir / "node"
        node_wrapper.write_text(f'#!/usr/bin/env bash\nexec {node_executable} "$@"\n')
        node_wrapper.chmod(0o755)

        env = isolated_environment(home)
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        env["TERM"] = "xterm"

        command = (
            f"bash {shlex.quote(str(INSTALLER))} "
            f"--repo {shlex.quote(str(repo))} --hosts codex --existing overwrite"
        )
        result = run_pty_command(command, "\r\r", env)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Skill language / 选择语言" in result.stdout
        assert "Documentation repair mode" in result.stdout
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert catalog["defaults"]["update"]["mode"] == "ask"
        assert "update" not in catalog["repos"][0]

    def _duplicate_repo_names_fail_before_changing_existing_install(
        self, selection, yes
    ):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo_a = tmp_path / "team-a" / "open-webui"
        repo_b = tmp_path / "team-b" / "open-webui"
        repo_a.mkdir(parents=True)
        repo_b.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_a, check=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True)
        canonical = home / ".agents" / "skills" / "docmate"
        canonical.mkdir(parents=True)
        (canonical / "SKILL.md").write_text("existing skill\n")
        (canonical / "references").mkdir()
        (canonical / "references" / "docmate.catalog.json").write_text(
            '{"existing": true}\n'
        )

        selection_args = (
            ["--repo", str(repo_a), "--repo", str(repo_b)]
            if selection == "explicit"
            else ["--auto-scan", "--scan-root", str(tmp_path), "--scan-depth", "3"]
        )

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                *(["--yes"] if yes else []),
                *selection_args,
                "--hosts",
                "codex",
                "--existing",
                "backup",
            ],
        )

        assert result.returncode != 0
        assert "duplicate repository name detected: open-webui" in result.stdout
        assert str(repo_a) in result.stderr and str(repo_b) in result.stderr
        assert "Rename one repository" in result.stderr
        assert (canonical / "SKILL.md").read_text() == "existing skill\n"
        assert (
            canonical / "references" / "docmate.catalog.json"
        ).read_text() == '{"existing": true}\n'
        assert backup_roots(home) == []

    def test_duplicate_repo_names_fail_before_changing_existing_install_explicit_yes(
        self,
    ):
        self._duplicate_repo_names_fail_before_changing_existing_install(
            "explicit", True
        )

    def test_duplicate_repo_names_fail_before_changing_existing_install_explicit_no_tty(
        self,
    ):
        self._duplicate_repo_names_fail_before_changing_existing_install(
            "explicit", False
        )

    def test_duplicate_repo_names_fail_before_changing_existing_install_scan(self):
        self._duplicate_repo_names_fail_before_changing_existing_install("scan", True)

    def _normalized_duplicate_repo_names_fail_before_changing_existing_install(
        self, names
    ):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo_a = tmp_path / "team-a" / names[0]
        repo_b = tmp_path / "team-b" / names[1]
        repo_a.mkdir(parents=True)
        repo_b.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_a, check=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True)
        canonical = home / ".agents" / "skills" / "docmate"
        references = canonical / "references"
        references.mkdir(parents=True)
        (canonical / "SKILL.md").write_text("old skill\n")
        (references / "docmate.catalog.json").write_text('{"old": true}\n')

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--repo",
                str(repo_a),
                "--repo",
                str(repo_b),
                "--hosts",
                "codex",
                "--existing",
                "backup",
            ],
        )

        assert result.returncode != 0
        assert str(repo_a) in result.stderr and str(repo_b) in result.stderr
        assert (canonical / "SKILL.md").read_text() == "old skill\n"
        assert (references / "docmate.catalog.json").read_text() == '{"old": true}\n'
        assert backup_roots(home) == []

    def test_normalized_duplicate_repo_names_fail_before_changing_existing_install_case(
        self,
    ):
        self._normalized_duplicate_repo_names_fail_before_changing_existing_install(
            ("Docs", "docs")
        )

    def test_normalized_duplicate_repo_names_fail_before_changing_existing_install_unicode(
        self,
    ):
        self._normalized_duplicate_repo_names_fail_before_changing_existing_install(
            ("Ｄｏｃｓ", "docs")
        )

    def test_duplicate_repo_name_menu_can_rename_repository(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo_a = tmp_path / "team-a" / "engine-algo-store-service"
        repo_b = tmp_path / "team-b" / "engine-algo-store-service"
        repo_a.mkdir(parents=True)
        repo_b.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_a, check=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True)

        bin_dir = fake_bin(home, [])
        node_executable = Path(node_path()) / "node"
        node_wrapper = bin_dir / "node"
        node_wrapper.write_text(f'#!/usr/bin/env bash\nexec {node_executable} "$@"\n')
        node_wrapper.chmod(0o755)

        env = isolated_environment(home)
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        env["TERM"] = "xterm"

        command = (
            f"bash {shlex.quote(str(INSTALLER))} "
            f"--language en --repo {shlex.quote(str(repo_a))} --repo {shlex.quote(str(repo_b))} "
            "--hosts codex --existing overwrite --update-mode off"
        )
        result = run_pty_command(
            command, "\x1b[B\rcharts-engine-algo-store-service\r", env
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Duplicate repository name action" in result.stdout
        assert "Rename A:" in result.stdout
        assert "Use A (exclude B):" in result.stdout
        assert "Use B (exclude A):" in result.stdout
        assert (
            "Renaming A from engine-algo-store-service to charts-engine-algo-store-service"
            in result.stdout
        )
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert {repo["path"] for repo in catalog["repos"]} == {str(repo_a), str(repo_b)}
        assert {repo["name"] for repo in catalog["repos"]} == {
            "charts-engine-algo-store-service",
            "engine-algo-store-service",
        }

    def test_duplicate_repo_name_menu_can_use_first_repository(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo_a = tmp_path / "team-a" / "engine-algo-store-service"
        repo_b = tmp_path / "team-b" / "engine-algo-store-service"
        repo_a.mkdir(parents=True)
        repo_b.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_a, check=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True)

        bin_dir = fake_bin(home, [])
        node_executable = Path(node_path()) / "node"
        node_wrapper = bin_dir / "node"
        node_wrapper.write_text(f'#!/usr/bin/env bash\nexec {node_executable} "$@"\n')
        node_wrapper.chmod(0o755)

        env = isolated_environment(home)
        env["PATH"] = f"{bin_dir}:/usr/bin:/bin"
        env["TERM"] = "xterm"

        command = (
            f"bash {shlex.quote(str(INSTALLER))} "
            f"--language en --repo {shlex.quote(str(repo_a))} --repo {shlex.quote(str(repo_b))} "
            "--hosts codex --existing overwrite --update-mode off"
        )
        result = run_pty_command(command, "\x1b[B\x1b[B\x1b[B\r", env)

        assert result.returncode == 0, result.stdout + result.stderr
        assert f"Using {repo_a} and excluding {repo_b}" in result.stdout
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert [repo["path"] for repo in catalog["repos"]] == [str(repo_a)]

    def test_existing_host_directory_is_backed_up_before_linking(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        existing = home / ".openclaw" / "skills" / "docmate"
        existing.mkdir(parents=True)
        (existing / "old.txt").write_text("old")
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo)

        assert result.returncode == 0, result.stdout + result.stderr
        roots = backup_roots(home)
        assert len(roots) == 1
        backup = roots[0] / "openclaw-docmate"
        assert backup.exists()
        assert (backup / "old.txt").read_text() == "old"
        assert existing.is_symlink()
        assert str(roots[0]) in result.stdout
        assert not (home / ".openclaw" / "skills" / "docmate_backup_0").exists()

    def test_existing_canonical_directory_is_backed_up_before_reinstall(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        canonical = home / ".agents" / "skills" / "docmate"
        references = canonical / "references"
        references.mkdir(parents=True)
        (references / "docmate.catalog.json").write_text('{"custom": true}\n')
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo)

        assert result.returncode == 0, result.stdout + result.stderr
        roots = backup_roots(home)
        assert len(roots) == 1
        backup = roots[0] / "canonical-docmate"
        assert backup.exists()
        assert (
            backup / "references" / "docmate.catalog.json"
        ).read_text() == '{"custom": true}\n'
        assert (canonical / "SKILL.md").exists()
        assert (canonical / "references" / "docmate.catalog.json").exists()
        assert (canonical / "references" / "docmate.catalog.example.json").is_file()
        assert str(roots[0]) in result.stdout
        assert home / ".local" / "state" in roots[0].parents
        assert not (home / "tmp" / "docmate-skill-backups").exists()
        assert not (home / ".agents" / "skills" / "docmate_backup_0").exists()

    def test_existing_backup_uses_xdg_state_home(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        canonical = home / ".agents" / "skills" / "docmate"
        canonical.mkdir(parents=True)
        (canonical / "SKILL.md").write_text("old skill\n")
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        state_home = tmp_path / "custom-state"

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--repo",
                str(repo),
                "--hosts",
                "codex",
                "--existing",
                "backup",
            ],
            extra_env={"XDG_STATE_HOME": str(state_home)},
        )

        assert result.returncode == 0, result.stdout + result.stderr
        roots = list((state_home / "docmate" / "backups").glob("install-*"))
        assert len(roots) == 1
        assert (
            roots[0] / "canonical-docmate" / "SKILL.md"
        ).read_text() == "old skill\n"
        assert str(roots[0]) in result.stdout

    def test_catalog_generation_failure_preserves_existing_install(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        canonical = home / ".agents" / "skills" / "docmate"
        references = canonical / "references"
        references.mkdir(parents=True)
        (canonical / "SKILL.md").write_text("old skill\n")
        (references / "docmate.catalog.json").write_text('{"old": true}\n')
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        fake_tools = tmp_path / "fake-tools"
        fake_tools.mkdir()
        fake_node = fake_tools / "node"
        real_node = Path(node_path()) / "node"
        fake_node.write_text(
            f"#!/usr/bin/env bash\n"
            f'if [ "$1" = \'-e\' ]; then exec {shlex.quote(str(real_node))} "$@"; fi\n'
            "exit 7\n"
        )
        fake_node.chmod(0o755)

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--repo",
                str(repo),
                "--hosts",
                "codex",
                "--existing",
                "backup",
            ],
            extra_path=fake_tools,
        )

        assert result.returncode == 7, result.stdout + result.stderr
        assert (canonical / "SKILL.md").read_text() == "old skill\n"
        assert (references / "docmate.catalog.json").read_text() == '{"old": true}\n'
        assert not (home / ".config/docmate/catalog.json").exists()
        assert backup_roots(home) == []

    def test_existing_canonical_and_host_directories_share_one_backup_root(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        canonical = home / ".agents" / "skills" / "docmate"
        canonical.mkdir(parents=True)
        (canonical / "old-canonical.txt").write_text("old-canonical")
        openclaw = home / ".openclaw" / "skills" / "docmate"
        openclaw.mkdir(parents=True)
        (openclaw / "old-openclaw.txt").write_text("old-openclaw")
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo)

        assert result.returncode == 0, result.stdout + result.stderr
        roots = backup_roots(home)
        assert len(roots) == 1
        assert (
            roots[0] / "canonical-docmate" / "old-canonical.txt"
        ).read_text() == "old-canonical"
        assert (
            roots[0] / "openclaw-docmate" / "old-openclaw.txt"
        ).read_text() == "old-openclaw"
        assert str(roots[0]) in result.stdout
        assert openclaw.is_symlink()

    def test_existing_host_symlink_is_replaced_without_backup(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        external = tmp_path / "external-docmate"
        external.mkdir()
        (external / "old.txt").write_text("old")
        existing = home / ".openclaw" / "skills" / "docmate"
        existing.parent.mkdir(parents=True)
        existing.symlink_to(external)
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo)

        assert result.returncode == 0, result.stdout + result.stderr
        canonical = home / ".agents" / "skills" / "docmate"
        assert existing.is_symlink()
        assert existing.resolve() == canonical
        assert (external / "old.txt").read_text() == "old"
        assert backup_roots(home) == []

    def test_existing_skip_preserves_symlink_target(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        external = tmp_path / "external-docmate"
        external.mkdir()
        (external / "old.txt").write_text("old")
        canonical = home / ".agents" / "skills" / "docmate"
        canonical.parent.mkdir(parents=True)
        canonical.symlink_to(external)
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--repo",
                str(repo),
                "--hosts",
                "all",
                "--existing",
                "skip",
            ],
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert canonical.is_symlink()
        assert canonical.resolve() == external
        assert (external / "old.txt").read_text() == "old"
        assert backup_roots(home) == []

    def test_existing_skip_preserves_host_symlink_to_canonical_without_partial_install(
        self,
    ):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        canonical = home / ".agents" / "skills" / "docmate"
        host_target = home / ".openclaw" / "skills" / "docmate"
        host_target.parent.mkdir(parents=True)
        host_target.symlink_to(canonical)
        before_inode = host_target.lstat().st_ino
        before_link = host_target.readlink()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--repo",
                str(repo),
                "--install-mode",
                "global",
                "--hosts",
                "openclaw",
                "--existing",
                "skip",
            ],
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Skipping existing host target" in result.stdout
        assert "Removed existing symlink" not in result.stdout
        assert "Backups moved to:" not in result.stdout
        assert "DocMate installed to" not in result.stdout
        assert host_target.is_symlink()
        assert host_target.lstat().st_ino == before_inode
        assert host_target.readlink() == before_link
        assert not canonical.exists()
        assert backup_roots(home) == []

    def test_existing_skip_preserves_host_directory_without_partial_install(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        canonical = home / ".agents" / "skills" / "docmate"
        host_target = home / ".openclaw" / "skills" / "docmate"
        host_target.mkdir(parents=True)
        (host_target / "old.txt").write_text("old")
        before_inode = host_target.lstat().st_ino
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--repo",
                str(repo),
                "--install-mode",
                "global",
                "--hosts",
                "openclaw",
                "--existing",
                "skip",
            ],
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "Skipping existing host target" in result.stdout
        assert "Backups moved to:" not in result.stdout
        assert "DocMate installed to" not in result.stdout
        assert host_target.is_dir()
        assert host_target.lstat().st_ino == before_inode
        assert (host_target / "old.txt").read_text() == "old"
        assert not canonical.exists()
        assert backup_roots(home) == []

    def test_installer_generates_valid_starter_catalog(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "gitlab-docs"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo)
        catalog = (
            home
            / ".agents"
            / "skills"
            / "docmate"
            / "references"
            / "docmate.catalog.json"
        )
        validate = subprocess.run(
            [
                "bash",
                str(ROOT / "skills/engineering/docmate/scripts/validate_catalog.sh"),
                str(catalog),
            ],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "PATH": f"{node_path()}:{os.environ['PATH']}"},
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert validate.returncode == 0, validate.stderr
        generated = json.loads(catalog.read_text())
        assert sorted(generated) == ["defaults", "repos"]
        repo_entry = generated["repos"][0]
        assert "description" not in repo_entry
        assert "aliases" not in repo_entry
        assert "update" not in repo_entry
        assert "installHosts" not in generated
        assert generated["defaults"]["update"]["mode"] == "ask"

    def test_installer_writes_selected_update_mode(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo, ["--update-mode", "auto"])

        assert result.returncode == 0, result.stdout + result.stderr
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert catalog["defaults"]["update"]["mode"] == "auto"
        assert "update" not in catalog["repos"][0]

    def test_installer_uses_local_head_when_remote_default_is_unavailable(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "checkout", "-q", "-b", "develop"], cwd=repo, check=True)

        result = run_install(home, repo)

        assert result.returncode == 0, result.stdout + result.stderr
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert catalog["repos"][0]["baseBranchCandidates"] == ["develop"]
        assert "using local HEAD as an unverified candidate: develop" in result.stderr
        assert "Detected remote default branch" not in result.stderr
        assert "local HEAD or main is an unverified" in result.stdout

    def test_installer_marks_feature_branch_as_unverified_when_remote_is_unreachable(
        self,
    ):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            ["git", "checkout", "-q", "-b", "feature/docs"], cwd=repo, check=True
        )
        subprocess.run(
            ["git", "remote", "add", "origin", str(tmp_path / "missing-remote")],
            cwd=repo,
            check=True,
        )

        result = run_install(home, repo)

        assert result.returncode == 0, result.stdout + result.stderr
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert catalog["repos"][0]["baseBranchCandidates"] == ["feature/docs"]
        assert (
            "using local HEAD as an unverified candidate: feature/docs" in result.stderr
        )
        assert "Detected remote default branch" not in result.stderr

    def test_installer_marks_main_fallback_as_unverified_without_local_branch(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            [
                "git",
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.com",
                "commit",
                "-q",
                "--allow-empty",
                "-m",
                "init",
            ],
            cwd=repo,
            check=True,
        )
        subprocess.run(["git", "checkout", "-q", "--detach"], cwd=repo, check=True)

        result = run_install(home, repo)

        assert result.returncode == 0, result.stdout + result.stderr
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert catalog["repos"][0]["baseBranchCandidates"] == ["main"]
        assert "using fallback main as an unverified candidate" in result.stderr
        assert "Detected remote default branch" not in result.stderr

    def test_installer_uses_glab_for_private_gitlab_default_branch(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        fake_tools = tmp_path / "fake-tools"
        fake_tools.mkdir()
        glab = fake_tools / "glab"
        glab.write_text("#!/usr/bin/env bash\nprintf 'release/docs\\n'\n")
        glab.chmod(0o755)

        repo = tmp_path / "gitlab-docs"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                "https://gitlab.sz.sensetime.com/example/gitlab-docs.git",
            ],
            cwd=repo,
            check=True,
        )

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--repo",
                str(repo),
                "--hosts",
                "all",
                "--existing",
                "backup",
            ],
            extra_path=fake_tools,
        )

        assert result.returncode == 0, result.stdout + result.stderr
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert catalog["repos"][0]["baseBranchCandidates"] == ["release/docs"]
        assert (
            "Detected remote default branch for gitlab-docs: release/docs"
            in result.stderr
        )

    def test_installer_accepts_project_as_backward_compatible_alias(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        repo = tmp_path / "docs-project"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

        result = run_install(home, repo, path_flag="--project")

        assert result.returncode == 0, result.stdout + result.stderr
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert catalog["repos"][0]["path"] == str(repo)

    def test_installer_auto_scan_adds_detected_repositories(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        scan_root = tmp_path / "scan-root"
        repo_a = scan_root / "team-a" / "docs-a"
        repo_b = scan_root / "team-b" / "docs-b"
        repo_a.mkdir(parents=True)
        repo_b.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_a, check=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True)

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--auto-scan",
                "--scan-root",
                str(scan_root),
                "--scan-depth",
                "3",
                "--hosts",
                "all",
                "--existing",
                "backup",
            ],
        )

        assert result.returncode == 0, result.stdout + result.stderr
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert {repo["path"] for repo in catalog["repos"]} == {str(repo_a), str(repo_b)}

    def test_installer_auto_scan_accepts_multiple_scan_roots(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        scan_root_a = tmp_path / "scan-root-a"
        scan_root_b = tmp_path / "scan-root-b"
        repo_a = scan_root_a / "docs-a"
        repo_b = scan_root_b / "docs-b"
        repo_a.mkdir(parents=True)
        repo_b.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_a, check=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True)

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--auto-scan",
                "--scan-root",
                str(scan_root_a),
                "--scan-root",
                str(scan_root_b),
                "--hosts",
                "codex",
                "--existing",
                "backup",
            ],
        )

        assert result.returncode == 0, result.stdout + result.stderr
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert {repo["path"] for repo in catalog["repos"]} == {str(repo_a), str(repo_b)}

    def test_installer_auto_scan_default_depth_is_two(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        scan_root = tmp_path / "scan-root"
        shallow_repo = scan_root / "docs-a"
        deep_repo = scan_root / "team-b" / "docs-b"
        shallow_repo.mkdir(parents=True)
        deep_repo.mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=shallow_repo, check=True)
        subprocess.run(["git", "init", "-q"], cwd=deep_repo, check=True)

        result = run_install_args(
            home,
            [
                "bash",
                str(INSTALLER),
                "--yes",
                "--auto-scan",
                "--scan-root",
                str(scan_root),
                "--hosts",
                "codex",
                "--existing",
                "backup",
            ],
        )

        assert result.returncode == 0, result.stdout + result.stderr
        assert "max depth: 2" in result.stdout
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert [repo["path"] for repo in catalog["repos"]] == [str(shallow_repo)]

    def test_installer_falls_back_to_scanning_when_repo_arg_is_prefix_directory(self):
        tmp_path = self.tmp_path
        home = tmp_path / "home"
        home.mkdir()
        prefix = tmp_path / "prefix"
        repo_a = prefix / "a"
        repo_b = prefix / "b"
        repo_a.mkdir(parents=True)
        repo_b.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo_a, check=True)
        subprocess.run(["git", "init", "-q"], cwd=repo_b, check=True)

        result = run_install(home, prefix)

        assert result.returncode == 0, result.stdout + result.stderr
        assert f"Warning: {prefix} is not a git repository" in result.stdout
        assert "Detected repositories under" in result.stdout
        catalog = json.loads(
            (
                home
                / ".agents"
                / "skills"
                / "docmate"
                / "references"
                / "docmate.catalog.json"
            ).read_text()
        )
        assert {repo["name"] for repo in catalog["repos"]} == {"a", "b"}
