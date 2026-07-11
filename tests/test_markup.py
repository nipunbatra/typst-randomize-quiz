"""System tests for the plain-markup front-end, run against exams/quiz2.typ.

Questions there have no explicit ids (except one #qid), so tests discover
questions by structural properties rather than hardcoding hash ids."""

import csv
import json
import subprocess
import sys

import pytest

from conftest import ROOT, SETS, LETTERS, questions_of, typst_query

EXAM2 = "exams/quiz2.typ"
EXAM2_ID = "dl-quiz-2"


@pytest.fixture(scope="session")
def realized2():
    return {s: json.loads(typst_query(s, exam=EXAM2)) for s in SETS}


@pytest.fixture(scope="session")
def built2(tmp_path_factory):
    out = tmp_path_factory.mktemp("build2")
    proc = subprocess.run(
        [sys.executable, "scripts/build.py", EXAM2, "--out", str(out)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out / EXAM2_ID


def mcqs_of(meta):
    return {q["id"]: q for q in questions_of(meta) if q["type"] == "mcq"}


# ------------------------------------------------------------ parsing

def test_structure_parsed(realized2):
    meta = realized2["A"]
    assert [s["title"] for s in meta["sections"]] == [
        "Multiple Choice", "Fill in the Blanks", "Long Answers ",
    ]
    assert meta["total"] == 19
    types = [q["type"] for q in questions_of(meta)]
    assert types.count("mcq") == 4 and types.count("fill_blank") == 2 and types.count("subjective") == 2


def test_default_mode_is_key():
    # The master compiles without inputs — and identifies as set A of the key.
    out = subprocess.run(
        ["typst", "compile", EXAM2, "/dev/null", "--root", str(ROOT), "--format", "pdf"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr


def test_qid_override_and_hash_ids(realized2):
    for meta in realized2.values():
        ids = {q["id"] for q in questions_of(meta)}
        assert "lr-too-high" in ids  # explicit #qid(...)
        auto = [i for i in ids if i.startswith("q") and i[1:].isdigit()]
        assert len(auto) == 7  # every other question got a stable hash id


def test_determinism():
    assert typst_query("C", exam=EXAM2) == typst_query("C", exam=EXAM2)


# ------------------------------------------------------------ semantics

def test_checkmark_detection_and_letters(realized2):
    for set_id, meta in realized2.items():
        for q in mcqs_of(meta).values():
            marked = {q["order"][LETTERS.index(ch)] for ch in q["answer"]}
            assert marked == set(q["correct_orig"]), f"set {set_id} {q['id']}"


def test_auto_multiselect(realized2):
    for meta in realized2.values():
        multi = [q for q in mcqs_of(meta).values() if len(q["answer"]) > 1]
        assert len(multi) == 1  # the two-✓ overfitting question
        assert len(multi[0]["answer"]) == 2


def test_nota_auto_pinned_last(realized2):
    # The L2-prior question ends with "None of the above" (original option 4,
    # not the correct one). It must sit last in every set.
    always_last = None
    for meta in realized2.values():
        ids = {q["id"] for q in mcqs_of(meta).values() if len(q["order"]) == 4 and q["order"][-1] == 4}
        always_last = ids if always_last is None else always_last & ids
    assert always_last, "no option stayed pinned to the last position in every set"
    for meta in realized2.values():
        for qid_ in always_last:
            assert mcqs_of(meta)[qid_]["correct_orig"] == [1]  # Gaussian is option 1


def test_blank_answers_exported(realized2):
    for meta in realized2.values():
        answers = {q["answer"] for q in questions_of(meta) if q["type"] == "fill_blank"}
        assert answers == {"early stopping", "2 λ θ; decay"}


def test_section_shuffle_false_keeps_subjective_order(realized2):
    orders = {tuple(q["id"] for q in meta["sections"][2]["questions"]) for meta in realized2.values()}
    assert len(orders) == 1  # #section(shuffle: false)


def test_mcq_order_shuffles_between_sets(realized2):
    orders = {tuple(q["id"] for q in meta["sections"][0]["questions"]) for meta in realized2.values()}
    assert len(orders) >= 3


def test_fairness(realized2):
    ref = sorted(q["id"] for q in questions_of(realized2["A"]))
    for meta in realized2.values():
        assert sorted(q["id"] for q in questions_of(meta)) == ref
        assert meta["total"] == 19


# ------------------------------------------------------------ build outputs

def test_build_and_csv(built2):
    for s in SETS:
        assert (built2 / f"set-{s}.pdf").exists()
        assert (built2 / f"set-{s}-key.pdf").exists()
    with (built2 / "answer_key.csv").open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == len(SETS) * 8
    assert {r["answer"] for r in rows if r["type"] == "fill_blank"} == {"early stopping", "2 λ θ; decay"}
