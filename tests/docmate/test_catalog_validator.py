import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]


def run_validator(catalog_path: Path):
    return subprocess.run(
        [
            "bash",
            str(ROOT / "skills/engineering/docmate/scripts/validate_catalog.sh"),
            str(catalog_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def valid_catalog(tmp_path: Path) -> dict:
    docs = tmp_path / "docs"
    runbooks = tmp_path / "runbooks"
    docs.mkdir()
    runbooks.mkdir()
    return {
        "defaults": {
            "update": {
                "mode": "ask",
            }
        },
        "repos": [
            {
                "name": "docs-site",
                "path": str(docs),
                "baseBranchCandidates": ["main"],
            },
            {
                "name": "runbooks",
                "path": str(runbooks),
                "baseBranchCandidates": ["main"],
            },
        ],
    }


def write_catalog(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n")


class CatalogValidatorTests(unittest.TestCase):
    def setUp(self):
        self.tmp_path = Path(
            self.enterContext(TemporaryDirectory(prefix="docmate-test-"))
        ).resolve()

    def test_accepts_valid_catalog_with_multiple_repos(self):
        tmp_path = self.tmp_path
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, valid_catalog(tmp_path))

        result = run_validator(catalog_path)

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "OK"

    def test_accepts_optional_repo_description_and_aliases(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["repos"][0]["description"] = ""
        payload["repos"][0]["aliases"] = ["docs", "site"]
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "OK"

    def test_accepts_legacy_install_hosts(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["installHosts"] = [
            "openclaw",
            "claude-code",
            "opencode",
            "codex",
            "hermes",
        ]
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "OK"

    def test_rejects_unsupported_root_keys(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["metadata"] = {}
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert "root contains unsupported key: metadata" in result.stderr

    def test_rejects_relative_paths(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["repos"][0]["path"] = "docs"
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert "repos[0].path must be an absolute path" in result.stderr

    def test_rejects_duplicate_repo_paths(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["repos"][1]["path"] = payload["repos"][0]["path"]
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert "duplicate repository path" in result.stderr

    def test_rejects_duplicate_aliases(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["repos"][0]["aliases"] = ["docs", "docs"]
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert "duplicate alias" in result.stderr

    def test_rejects_cross_repo_duplicate_aliases(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["repos"][0]["aliases"] = ["docs"]
        payload["repos"][1]["aliases"] = ["docs"]
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert (
            "repos[1].aliases[0] (docs) conflicts with repos[0].aliases[0] (docs)"
            in result.stderr
        )

    def _rejects_cross_repo_normalized_name_conflicts(
        self, first_field, first_value, second_field, second_value
    ):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["repos"][0][first_field] = (
            [first_value] if first_field == "aliases" else first_value
        )
        payload["repos"][1][second_field] = (
            [second_value] if second_field == "aliases" else second_value
        )
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert "repos[0]." in result.stderr
        assert "repos[1]." in result.stderr
        assert first_value in result.stderr and second_value in result.stderr

    def test_rejects_cross_repo_normalized_name_conflicts_name_case(self):
        self._rejects_cross_repo_normalized_name_conflicts(
            "name", "docs-site", "name", "DOCS-SITE"
        )

    def test_rejects_cross_repo_normalized_name_conflicts_name_and_alias(self):
        self._rejects_cross_repo_normalized_name_conflicts(
            "name", "docs-site", "aliases", "DOCS-SITE"
        )

    def test_rejects_cross_repo_normalized_name_conflicts_normalized_alias_and_name(
        self,
    ):
        self._rejects_cross_repo_normalized_name_conflicts(
            "aliases", "Ｄｏｃｓ", "name", "docs"
        )

    def test_rejects_cross_repo_normalized_name_conflicts_alias_case(self):
        self._rejects_cross_repo_normalized_name_conflicts(
            "aliases", "RunBooks", "aliases", "runbooks"
        )

    def test_allows_name_reused_as_alias_within_same_repo(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["repos"][0]["aliases"] = ["DOCS-SITE"]
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode == 0, result.stderr

    def test_rejects_repo_level_update_mode(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["repos"][0]["update"] = {"mode": "ask"}
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert (
            "repos[0].update is not supported; use defaults.update.mode"
            in result.stderr
        )

    def test_rejects_unsupported_default_update_keys(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["defaults"]["update"]["branchPrefix"] = "docmate/"
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert "defaults.update must contain exactly these keys: mode" in result.stderr

    def test_rejects_invalid_update_mode(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["defaults"]["update"]["mode"] = "always"
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert "update.mode must be ask, auto, or off" in result.stderr

    def test_rejects_empty_base_branches_when_update_enabled(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["repos"][0]["baseBranchCandidates"] = []
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode != 0
        assert (
            "baseBranchCandidates must contain at least one branch when updates are enabled"
            in result.stderr
        )

    def test_allows_empty_base_branches_when_update_off(self):
        tmp_path = self.tmp_path
        payload = valid_catalog(tmp_path)
        payload["defaults"]["update"]["mode"] = "off"
        payload["repos"][0]["baseBranchCandidates"] = []
        catalog_path = tmp_path / "docmate.catalog.json"
        write_catalog(catalog_path, payload)

        result = run_validator(catalog_path)

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "OK"
