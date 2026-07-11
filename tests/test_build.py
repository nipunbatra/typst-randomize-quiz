"""System tests for the randomization + build pipeline, run against the demo
exam (exams/quiz1.typ). Everything asserted here is deterministic: the shuffles
are pure functions of (exam id, set id, question ids), so these tests can pin
exact facts and will only break if the demo exam or the seed scheme changes."""

import csv
import hashlib
import json
import subprocess

from conftest import EXAM, LETTERS, ROOT, SETS, TIMESTAMP, mcqs_of, questions_of, typst_query

CONFIG_SUBJ_ORDER = ["subj-overfitting", "subj-cnn-vs-mlp", "subj-forward-backward", "subj-softmax-grad"]


def ids_in_order(meta):
    return [q["id"] for q in questions_of(meta)]


# ------------------------------------------------------------ determinism

def test_same_set_is_byte_identical_metadata():
    assert typst_query("B") == typst_query("B")


def test_default_set_is_first():
    assert json.loads(typst_query(None))["set"] == "A"


def test_pdf_bytes_reproducible(tmp_path):
    outs = []
    for i in range(2):
        out = tmp_path / f"{i}.pdf"
        proc = subprocess.run(
            ["typst", "compile", EXAM, str(out), "--root", str(ROOT),
             "--creation-timestamp", TIMESTAMP, "--input", "set=A"],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr
        outs.append(out.read_bytes())
    assert outs[0] == outs[1]


# ------------------------------------------------------------ randomization

def test_question_order_differs_across_sets(realized):
    orders = {tuple(ids_in_order(m)) for m in realized.values()}
    assert len(orders) == len(SETS), "expected every set to have a distinct question order"


def test_option_order_differs_between_sets(realized):
    a, b = mcqs_of(realized["A"]), mcqs_of(realized["B"])
    assert any(a[i]["order"] != b[i]["order"] for i in a), (
        "no MCQ has a different option permutation between sets A and B"
    )


def test_option_order_is_permutation(realized):
    for meta in realized.values():
        for q in mcqs_of(meta).values():
            assert sorted(q["order"]) == list(range(1, len(q["order"]) + 1))


def test_nota_stays_pinned_last(realized):
    # mcq-conv-output's 4th option is ans(fixed: "last")[None of the above]
    for set_id, meta in realized.items():
        q = mcqs_of(meta)["mcq-conv-output"]
        assert q["order"][-1] == 4, f"set {set_id}: pinned option moved"
        assert q["answer"] == "D", f"set {set_id}: pinned correct option should always be D"


def test_shuffle_false_keeps_author_option_order(realized):
    for meta in realized.values():
        assert mcqs_of(meta)["mcq-activation-statements"]["order"] == [1, 2, 3, 4]


def test_section_shuffle_false_keeps_author_question_order(realized):
    for meta in realized.values():
        subj = [q["id"] for q in meta["sections"][2]["questions"]]
        assert subj == CONFIG_SUBJ_ORDER


# ------------------------------------------------------------ fairness

def test_all_sets_have_same_questions_and_marks(realized):
    ref = realized[SETS[0]]
    for meta in realized.values():
        assert sorted(ids_in_order(meta)) == sorted(ids_in_order(ref))
        assert meta["total"] == ref["total"] == sum(q["marks"] for q in questions_of(meta))
        assert [q["qno"] for q in questions_of(meta)] == list(range(1, len(questions_of(meta)) + 1))


def test_pick_samples_same_subset_in_every_set(realized):
    ref_mcqs = set(mcqs_of(realized[SETS[0]]))
    assert len(ref_mcqs) == 8  # pick: 8 out of 9 in the bank
    assert "mcq-activation-statements" in ref_mcqs  # `use` guarantees it survives pick
    for meta in realized.values():
        assert set(mcqs_of(meta)) == ref_mcqs


# ------------------------------------------------------------ key correctness

def test_answer_letters_point_at_correct_options(realized):
    """The letters printed in the key, mapped through the recorded permutation,
    must land exactly on the originally-correct options — for every set."""
    ref = {q["id"]: q["correct_orig"] for q in mcqs_of(realized[SETS[0]]).values()}
    for set_id, meta in realized.items():
        for q in mcqs_of(meta).values():
            assert q["correct_orig"] == ref[q["id"]], f"{q['id']}: correct options drifted"
            marked = {q["order"][LETTERS.index(ch)] for ch in q["answer"]}
            assert marked == set(q["correct_orig"]), (
                f"set {set_id} {q['id']}: letters {q['answer']!r} != correct {q['correct_orig']}"
            )


def test_multiselect_reports_all_letters(realized):
    for meta in realized.values():
        assert len(mcqs_of(meta)["mcq-adaptive-optimizers"]["answer"]) == 2


def test_fib_multi_blank_answer(realized):
    for meta in realized.values():
        q = {q["id"]: q for q in questions_of(meta)}["fib-shapes"]
        assert q["answer"] == "B; h"


# ------------------------------------------------------------ build outputs

def test_build_produces_all_files(built):
    for s in SETS:
        assert (built / f"set-{s}.pdf").exists()
        assert (built / f"set-{s}-key.pdf").exists()
    assert (built / "answer_key.csv").exists()
    assert (built / "manifest.json").exists()


def test_csv_matches_realized_structure(built, realized):
    with (built / "answer_key.csv").open() as f:
        rows = list(csv.DictReader(f))
    n_questions = len(questions_of(realized[SETS[0]]))
    assert len(rows) == len(SETS) * n_questions
    by_key = {(r["set"], int(r["qno"])): r for r in rows}
    for set_id, meta in realized.items():
        for q in questions_of(meta):
            r = by_key[(set_id, q["qno"])]
            assert r["question_id"] == q["id"]
            assert r["answer"] == q["answer"]
            assert r["marks"] == str(q["marks"])
            expected_order = "|".join(map(str, q.get("order", [])))
            assert r["option_order"] == expected_order


def test_manifest_hashes_match_files(built):
    manifest = json.loads((built / "manifest.json").read_text())
    assert manifest["total_marks"] == 40
    for entry in manifest["sets"].values():
        for fname, digest in entry["sha256"].items():
            actual = hashlib.sha256((built / fname).read_bytes()).hexdigest()
            assert actual == digest, f"{fname}: manifest hash stale"
