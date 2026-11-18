#!/bin/sh
set -eu

export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null

mkdir "$1"
cd "$1"
git init --quiet --initial-branch=main --template=
git config user.name 'Fixture Author'
git config user.email fixture@example.invalid
git config commit.gpgsign false

printf '__pycache__/\ncache/\n' > .gitignore
printf '# Ticket keys\n\nKeys are uppercased after trimming surrounding whitespace.\n' > README.md
printf 'Run `python3 -m unittest discvoer -v`.\n' > CONTRIBUTING.md
printf 'Use `normailze_key` for ticket keys.\n' > USAGE.md
printf 'def normalize_key(value):\n    return value.upper()\n' > ticket.py
printf 'attempts=3\ndelay=1\n' > retry.conf
git add -- .gitignore README.md CONTRIBUTING.md USAGE.md ticket.py retry.conf
git commit --quiet -m 'Seed ticket key fixture'

printf 'def normalize_key(value):\n    return value.strip().upper()\n' > ticket.py
cat > test_ticket.py <<'PY'
import unittest

from ticket import normalize_key


class TicketTest(unittest.TestCase):
    def test_trims_surrounding_whitespace(self):
        self.assertEqual(normalize_key(" ab-42 "), "AB-42")
PY
printf 'Run `python3 -m unittest discover -v`.\n' > CONTRIBUTING.md

printf 'Use `normailze_key` for keys in the legacy queue.\n' > USAGE.md
printf 'attempts=8\ndelay=1\n' > retry.conf
git add -- USAGE.md retry.conf
printf 'Use `normalize_key` for ticket keys.\n' > USAGE.md
printf 'attempts=8\ndelay=4\n' > retry.conf
printf 'Possible local experiment\n' > experiment.txt
mkdir cache
printf 'Local result\n' > cache/result.txt

# Make one unchanged file's cached stat data stale for the read-only check.
TZ=UTC touch -t 202311142213 README.md
