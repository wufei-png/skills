import json
from pathlib import Path


def sample():
    return json.loads((Path(__file__).parent / "docs/review/sample.json").read_text(encoding="utf-8"))
