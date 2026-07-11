import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXAM = "exams/quiz1.typ"
EXAM_ID = "dl-quiz-1"
SETS = ["A", "B", "C", "D"]
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TIMESTAMP = "1767225600"


def typst_query(set_id=None, exam=EXAM):
    """Raw JSON string of the <answerkey> metadata for one set."""
    cmd = ["typst", "query", exam, "<answerkey>", "--field", "value", "--one", "--root", str(ROOT)]
    if set_id is not None:
        cmd += ["--input", f"set={set_id}"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def questions_of(meta):
    return [q for s in meta["sections"] for q in s["questions"]]


def mcqs_of(meta):
    return {q["id"]: q for q in questions_of(meta) if q["type"] == "mcq"}


@pytest.fixture(scope="session")
def realized():
    """Realized (shuffled) exam structure for every set, straight from typst."""
    return {s: json.loads(typst_query(s)) for s in SETS}


@pytest.fixture(scope="session")
def built(tmp_path_factory):
    """Full build.py run into a temp dir; returns the exam output directory."""
    out = tmp_path_factory.mktemp("build")
    proc = subprocess.run(
        [sys.executable, "scripts/build.py", EXAM, "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out / EXAM_ID
