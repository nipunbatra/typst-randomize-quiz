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


# Every exam in the repo, with its full set list. The property-based suite in
# test_properties.py runs the whole invariant matrix over each (exam, set).
EXAMS = {
    "exams/quiz1.typ": ["A", "B", "C", "D"],
    "exams/quiz2.typ": ["A", "B", "C", "D"],
    "exams/quiz3.typ": ["A", "B", "C", "D"],
    "exams/quiz4-ml23.typ": ["A", "B", "C", "D"],
    "exams/demo-physics.typ": ["A", "B"],
    "exams/demo-chemistry.typ": ["A", "B"],
    "exams/demo-algorithms.typ": ["A", "B"],
    "exams/demo-linear-algebra.typ": ["A", "B"],
    "exams/demo-economics.typ": ["A", "B"],
    "tests/stress-markup.typ": ["A", "B"],
    "tests/stress-bank.typ": ["A", "B"],
    "tests/stress-packages.typ": ["A", "B"],  # needs network for @preview packages
}


def typst_query(set_id=None, exam=EXAM):
    """Raw JSON string of the <answerkey> metadata for one set."""
    cmd = ["typst", "query", exam, "<answerkey>", "--field", "value", "--one", "--root", str(ROOT)]
    if set_id is not None:
        cmd += ["--input", f"set={set_id}"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0 and ("download" in proc.stderr or "failed to load package" in proc.stderr):
        pytest.skip(f"@preview packages unavailable offline: {exam}")
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


_QUERY_CACHE = {}


def realized_meta(exam, set_id):
    """Parsed <answerkey> for (exam, set), cached across the session."""
    key = (exam, set_id)
    if key not in _QUERY_CACHE:
        _QUERY_CACHE[key] = json.loads(typst_query(set_id, exam=exam))
    return _QUERY_CACHE[key]


def letters_consistent(meta):
    """Ids of MCQs whose printed answer letters do NOT land on the
    originally-correct options after the recorded permutation."""
    errs = []
    for q in questions_of(meta):
        if q["type"] != "mcq":
            continue
        marked = {q["order"][LETTERS.index(ch)] for ch in q["answer"]}
        if marked != set(q["correct_orig"]):
            errs.append(q["id"])
    return errs


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
