"""The invariant matrix: every guarantee, checked on every set of every exam
in the repository (demos, real ported papers, stress exams). Parametrized per
(exam, set) so a regression names exactly which paper and which set broke."""

import subprocess

import pytest

from conftest import EXAMS, LETTERS, ROOT, letters_consistent, questions_of, realized_meta

COMBOS = [(e, s) for e, sets in EXAMS.items() for s in sets]
COMBO_IDS = [f"{e.split('/')[-1].removesuffix('.typ')}-{s}" for e, s in COMBOS]
EXAM_IDS = [e.split("/")[-1].removesuffix(".typ") for e in EXAMS]


# ---------------------------------------------------------- per (exam, set)

@pytest.mark.parametrize("exam,set_id", COMBOS, ids=COMBO_IDS)
def test_answer_letters_land_on_correct_options(exam, set_id):
    assert letters_consistent(realized_meta(exam, set_id)) == []


@pytest.mark.parametrize("exam,set_id", COMBOS, ids=COMBO_IDS)
def test_option_orders_are_permutations(exam, set_id):
    for q in questions_of(realized_meta(exam, set_id)):
        if q["type"] == "mcq":
            n = len(q["order"])
            assert sorted(q["order"]) == list(range(1, n + 1)), q["id"]
            assert 2 <= n <= 26, q["id"]


@pytest.mark.parametrize("exam,set_id", COMBOS, ids=COMBO_IDS)
def test_numbering_contiguous_and_totals_add_up(exam, set_id):
    meta = realized_meta(exam, set_id)
    qs = questions_of(meta)
    assert [q["qno"] for q in qs] == list(range(1, len(qs) + 1))
    assert meta["total"] == sum(q["marks"] for q in qs)
    assert meta["total"] == sum(s["marks"] for s in meta["sections"])


@pytest.mark.parametrize("exam,set_id", COMBOS, ids=COMBO_IDS)
def test_marks_positive_everywhere(exam, set_id):
    for q in questions_of(realized_meta(exam, set_id)):
        assert q["marks"] > 0, q["id"]


@pytest.mark.parametrize("exam,set_id", COMBOS, ids=COMBO_IDS)
def test_answers_wellformed(exam, set_id):
    """MCQ answers are non-empty ascending letter strings within range; fib
    answers are non-empty text; subjective rows say MANUAL."""
    for q in questions_of(realized_meta(exam, set_id)):
        if q["type"] == "mcq":
            assert q["answer"], q["id"]
            idx = [LETTERS.index(ch) for ch in q["answer"]]
            assert idx == sorted(idx) and len(set(idx)) == len(idx), q["id"]
            assert all(i < len(q["order"]) for i in idx), q["id"]
        elif q["type"] == "fill_blank":
            assert q["answer"].strip(), q["id"]
        else:
            assert q["answer"] == "MANUAL", q["id"]


@pytest.mark.parametrize("exam,set_id", COMBOS, ids=COMBO_IDS)
def test_ids_unique_within_set(exam, set_id):
    ids = [q["id"] for q in questions_of(realized_meta(exam, set_id))]
    assert len(ids) == len(set(ids))


# ---------------------------------------------------------------- per exam

@pytest.mark.parametrize("exam", EXAMS, ids=EXAM_IDS)
def test_all_sets_share_questions_and_totals(exam):
    sets = EXAMS[exam]
    ref = realized_meta(exam, sets[0])
    ref_ids = sorted(q["id"] for q in questions_of(ref))
    ref_correct = {
        q["id"]: q["correct_orig"] for q in questions_of(ref) if q["type"] == "mcq"
    }
    for s in sets[1:]:
        meta = realized_meta(exam, s)
        assert sorted(q["id"] for q in questions_of(meta)) == ref_ids
        assert meta["total"] == ref["total"]
        for q in questions_of(meta):
            if q["type"] == "mcq":
                assert q["correct_orig"] == ref_correct[q["id"]], q["id"]


@pytest.mark.parametrize("exam", EXAMS, ids=EXAM_IDS)
def test_metadata_deterministic(exam):
    from conftest import typst_query

    s = EXAMS[exam][-1]
    assert typst_query(s, exam=exam) == typst_query(s, exam=exam)


@pytest.mark.parametrize("exam", EXAMS, ids=EXAM_IDS)
def test_key_mode_compiles(exam, tmp_path):
    proc = subprocess.run(
        ["typst", "compile", exam, str(tmp_path / "k.pdf"), "--root", str(ROOT),
         "--input", f"set={EXAMS[exam][0]}", "--input", "mode=key"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0 and "download" in proc.stderr:
        pytest.skip("packages unavailable offline")
    assert proc.returncode == 0, proc.stderr


@pytest.mark.parametrize("exam", EXAMS, ids=EXAM_IDS)
def test_compiles_without_warnings(exam, tmp_path):
    """Deprecations, layout non-convergence, missing fonts etc. all surface as
    typst warnings — none are acceptable in shipped papers."""
    proc = subprocess.run(
        ["typst", "compile", exam, str(tmp_path / "w.pdf"), "--root", str(ROOT),
         "--input", "mode=exam"],
        cwd=ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0 and "download" in proc.stderr:
        pytest.skip("packages unavailable offline")
    assert proc.returncode == 0, proc.stderr
    warnings = [l for l in proc.stderr.splitlines() if "warning:" in l]
    assert warnings == [], proc.stderr


@pytest.mark.parametrize("exam", EXAMS, ids=EXAM_IDS)
def test_question_order_varies_when_shuffling_possible(exam):
    """Across an exam's sets, at least one ordering difference must exist
    (unless every section is shuffle: false, which no repo exam is)."""
    sets = EXAMS[exam]
    orders = {tuple(q["id"] for q in questions_of(realized_meta(exam, s))) for s in sets}
    opt_orders = {
        (q["id"], tuple(q["order"]))
        for s in sets
        for q in questions_of(realized_meta(exam, s))
        if q["type"] == "mcq"
    }
    n_mcq = len({i for i, _ in opt_orders})
    assert len(orders) > 1 or len(opt_orders) > n_mcq, (
        "no question-order or option-order variation across sets"
    )
