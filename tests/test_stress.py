"""Stress and robustness tests: torture markup, 100-question generated exam,
RNG uniformity, build.py CLI edge cases, and the real ML demo (quiz3)."""

import json
import subprocess
import sys
import time

import pytest

from conftest import LETTERS, ROOT, questions_of, typst_query

STRESS_MARKUP = "tests/stress-markup.typ"
STRESS_BANK = "tests/stress-bank.typ"


def letters_consistent(meta):
    errs = []
    for q in questions_of(meta):
        if q["type"] != "mcq":
            continue
        marked = {q["order"][LETTERS.index(ch)] for ch in q["answer"]}
        if marked != set(q["correct_orig"]):
            errs.append(q["id"])
    return errs


@pytest.fixture(scope="session")
def torture():
    return {s: json.loads(typst_query(s, exam=STRESS_MARKUP)) for s in ("A", "B")}


@pytest.fixture(scope="session")
def bulk():
    return {s: json.loads(typst_query(s, exam=STRESS_BANK)) for s in ("A", "B")}


# ------------------------------------------------------------ torture markup

def test_torture_compiles_both_modes(tmp_path):
    for mode in ("exam", "key"):
        proc = subprocess.run(
            ["typst", "compile", STRESS_MARKUP, str(tmp_path / f"{mode}.pdf"),
             "--root", str(ROOT), "--input", "set=B", "--input", f"mode={mode}"],
            cwd=ROOT, capture_output=True, text=True,
        )
        assert proc.returncode == 0, proc.stderr


def test_torture_structure(torture):
    meta = torture["A"]
    qs = questions_of(meta)
    assert len(qs) == 20
    assert meta["total"] == 31.5  # fractional marks survive
    types = [q["type"] for q in qs]
    assert types.count("mcq") == 15 and types.count("fill_blank") == 2 and types.count("subjective") == 3


def test_three_letter_multiselect_answer(torture):
    for meta in torture.values():
        assert any(len(q["answer"]) == 3 for q in questions_of(meta) if q["type"] == "mcq")


def test_torture_key_consistent_all_sets(torture):
    for set_id, meta in torture.items():
        assert letters_consistent(meta) == [], f"set {set_id}"


def test_blanks_survive_styled_text_and_math(torture):
    answers = {q["answer"] for q in questions_of(torture["A"]) if q["type"] == "fill_blank"}
    assert answers == {"bold answer; n", "Gradient descent"}


def test_both_pinned_options_keep_positions(torture):
    for meta in torture.values():
        pinned = [q for q in questions_of(meta)
                  if q["type"] == "mcq" and len(q["order"]) == 2 and q["marks"] == 1
                  and q["order"] == [1, 2] and q["answer"] == "A"]
        assert pinned, "pin-first/pin question lost its order"


def test_opts_shuffle_false_in_markup(torture):
    for meta in torture.values():
        frozen = [q for q in questions_of(meta) if q.get("order") == [1, 2, 3, 4]]
        assert frozen, "#opts(shuffle: false) question was shuffled"


def test_unicode_survives(torture):
    assert "नमूना" in torture["A"]["title"]


# ------------------------------------------------------------ bulk bank

def test_bulk_pick_100(bulk):
    for meta in bulk.values():
        qs = questions_of(meta)
        assert len(qs) == 100
        ids = {q["id"] for q in qs}
        assert {"max-options", "true-false"} <= ids  # `use` guaranteed under pick
    assert {q["id"] for q in questions_of(bulk["A"])} == {q["id"] for q in questions_of(bulk["B"])}


def test_bulk_key_consistent(bulk):
    for set_id, meta in bulk.items():
        assert letters_consistent(meta) == [], f"set {set_id}"


def test_26_option_question(bulk):
    for meta in bulk.values():
        q = {x["id"]: x for x in questions_of(meta)}["max-options"]
        assert len(q["order"]) == 26
        assert q["answer"] == "Z" and q["order"][-1] == 26  # pinned last


def test_large_compile_under_budget(tmp_path):
    t0 = time.monotonic()
    proc = subprocess.run(
        ["typst", "compile", STRESS_BANK, str(tmp_path / "big.pdf"),
         "--root", str(ROOT), "--input", "set=A", "--input", "mode=key"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert time.monotonic() - t0 < 60, "100-question compile took over a minute"


# ------------------------------------------------------------ RNG quality

def test_rng_position_distribution_roughly_uniform():
    out = subprocess.run(
        ["typst", "query", "tests/rng-dist.typ", "<dist>", "--field", "value", "--one", "--root", str(ROOT)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert out.returncode == 0, out.stderr
    d = json.loads(out.stdout)
    expected = d["trials"] / d["n"]  # 50
    for row in d["counts"]:
        assert sum(row) == d["trials"]
        for cell in row:
            assert 0.5 * expected <= cell <= 1.6 * expected, f"biased cell: {cell} vs {expected}"
    # pin the hash function itself: any change silently reshuffles ALL exams
    assert d["hash-regression"] == 3086405523


# ------------------------------------------------------------ build.py CLI

def test_build_subset_of_sets(tmp_path):
    proc = subprocess.run(
        [sys.executable, "scripts/build.py", "exams/quiz2.typ", "--out", str(tmp_path), "--sets", "A"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    out = tmp_path / "dl-quiz-2"
    assert (out / "set-A.pdf").exists()
    assert not (out / "set-B.pdf").exists()


def test_build_unknown_set_fails(tmp_path):
    proc = subprocess.run(
        [sys.executable, "scripts/build.py", "exams/quiz2.typ", "--out", str(tmp_path), "--sets", "Z"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode != 0
    assert "unknown sets" in proc.stderr


# ------------------------------------------------------------ real ML demo

def test_quiz3_full_build(tmp_path):
    """The ES 335 demo (figures, tables, math blanks) builds with all
    cross-set invariants verified by build.py itself."""
    proc = subprocess.run(
        [sys.executable, "scripts/build.py", "exams/quiz3.typ", "--out", str(tmp_path)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    meta = json.loads(typst_query("C", exam="exams/quiz3.typ"))
    assert meta["total"] == 30
    fib_answers = {q["answer"] for q in questions_of(meta) if q["type"] == "fill_blank"}
    assert "−1; y" in fib_answers  # math blanks extract (unicode minus from $-1$)


# ------------------------------------------------------------ multi-file quiz

def test_include_splits_quiz_across_files():
    """#include'd files are flattened into the question stream."""
    meta = json.loads(typst_query("A", exam="tests/fixtures/markup-include.typ"))
    assert [s["title"] for s in meta["sections"]] == ["Part One", "Part Two"]
    assert len(questions_of(meta)) == 2


# ------------------------------------------------------------ ported 2023 quiz

def test_quiz4_ported_archive_builds(tmp_path):
    """Real 2023 ES 335 questions (tables, quotes, inline code, 0.5-mark
    questions) build with invariants verified."""
    proc = subprocess.run(
        [sys.executable, "scripts/build.py", "exams/quiz4-ml23.typ", "--out", str(tmp_path)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    meta = json.loads(typst_query("D", exam="exams/quiz4-ml23.typ"))
    assert meta["total"] == 9.0
    marks = sorted(q["marks"] for q in questions_of(meta))
    assert marks == [0.5, 1, 1, 1, 1, 1, 1.5, 2]


def test_custom_header_footer():
    """header: none + footer as a function of (exam, set, mode, total)."""
    proc = subprocess.run(
        ["typst", "compile", "tests/fixtures/markup-custom-furniture.typ",
         "/dev/null", "--format", "pdf", "--root", str(ROOT), "--input", "mode=exam"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr


# ------------------------------------------------------------ golden files

def test_golden_csv_quiz1(tmp_path):
    """Byte-stable grading CSV — any change to shuffles, ids, or CSV format
    must be deliberate (regenerate tests/golden/dl-quiz-1.csv and explain)."""
    proc = subprocess.run(
        [sys.executable, "scripts/build.py", "exams/quiz1.typ", "--out", str(tmp_path)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    got = (tmp_path / "dl-quiz-1" / "answer_key.csv").read_text()
    assert got == (ROOT / "tests" / "golden" / "dl-quiz-1.csv").read_text()


def test_golden_question_order_quiz3():
    """Pins the exact realized order of quiz3 set A. Passing on both macOS
    (dev) and Linux (CI) proves cross-platform determinism of the PRNG."""
    meta = json.loads(typst_query("A", exam="exams/quiz3.typ"))
    got = [q["id"] for q in questions_of(meta)]
    expected = json.loads((ROOT / "tests" / "golden" / "quiz3-setA-order.json").read_text())
    assert got == expected


# ------------------------------------------------------------ CSV escaping

def test_csv_survives_commas_and_quotes(tmp_path):
    import csv as csvmod
    proc = subprocess.run(
        [sys.executable, "scripts/build.py", "tests/fixtures/markup-csv-quoting.typ", "--out", str(tmp_path)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    with (tmp_path / "csv-quoting" / "answer_key.csv").open() as f:
        rows = list(csvmod.DictReader(f))
    answers = {r["answer"] for r in rows}
    assert 'comma, "quotes", and; semicolons' in answers


# ------------------------------------------------------------ overflow & floats

def test_overtall_question_breaks_instead_of_overflowing(tmp_path):
    """A question taller than a full page must flow to the next page — an
    unbreakable block would silently truncate in print."""
    opts = "\n".join(
        f"  - {'✓ ' if i == 0 else ''}Option {i} is stretched with plenty of repeated "
        "verbiage so that the option wraps across multiple typeset lines and consumes "
        "real vertical space on the page, again and again, filling the width entirely."
        for i in range(24)
    )
    src = (
        '#import "/quizforge/lib.typ": *\n'
        '#show: quiz.with(id: "overtall-test", sets: ("A",))\n'
        f"+ A question with 24 long options that cannot fit one page?\n{opts}\n"
    )
    f = ROOT / "build" / "snippets" / "overtall.typ"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(src)
    proc = subprocess.run(
        ["typst", "compile", str(f), str(tmp_path / "p{p}.png"),
         "--root", str(ROOT), "--format", "png", "--ppi", "40"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert len(list(tmp_path.glob("p*.png"))) >= 2, "over-tall question did not break across pages"


def test_fractional_marks_totals_display_clean():
    """0.1 + 0.2 must total 0.3, not 0.30000000000000004, on the cover."""
    src = (
        '#import "/quizforge/lib.typ": *\n'
        '#show: quiz.with(id: "float-test", sets: ("A",))\n'
        "+ #m(0.1) Q one?\n  - ✓ a\n  - b\n"
        "+ #m(0.2) Q two?\n  - ✓ a\n  - b\n"
    )
    f = ROOT / "build" / "snippets" / "float-total.typ"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(src)
    meta = json.loads(typst_query("A", exam=str(f.relative_to(ROOT))))
    assert meta["total"] == 0.3
    assert meta["sections"][0]["marks"] == 0.3


# ------------------------------------------------------------ user styling

def test_global_styling_above_quiz_never_changes_realization():
    """#set/#show rules above `#show: quiz` (fonts, heading styles, even a
    two-column wrapper) may change looks but must not affect order/answers."""
    base = (
        '#import "/quizforge/lib.typ": *\n'
        '#show: quiz.with(id: "styled-test", sets: ("A", "B"))\n'
        "= Part\n"
        "+ #m(2) Styled question one?\n  - ✓ a\n  - b\n  - c\n"
        "+ #m(1) The answer is #blank[here].\n"
    )
    # (a columns(2, ..) wrapper is rejected by typst itself: page/document set
    # rules cannot live inside containers — future `columns:` param instead)
    styled = (
        '#set text(size: 12.5pt)\n'
        '#show heading: it => text(fill: blue, it)\n'
        '#show emph: set text(fill: rgb("#333333"))\n'
    )
    d = ROOT / "build" / "snippets"
    d.mkdir(parents=True, exist_ok=True)
    (d / "unstyled.typ").write_text(base)
    (d / "styled.typ").write_text(base.replace("#show: quiz", styled + "#show: quiz", 1))
    plain = typst_query("B", exam="build/snippets/unstyled.typ")
    fancy = typst_query("B", exam="build/snippets/styled.typ")
    assert json.loads(plain)["sections"] == json.loads(fancy)["sections"]


# ------------------------------------------------------------ odd set ids

def test_unicode_and_odd_set_ids_through_build(tmp_path):
    src = (
        '#import "/quizforge/lib.typ": *\n'
        '#show: quiz.with(id: "odd-sets-test", sets: ("1", "क", "MORNING-A"))\n'
        "+ Q?\n  - ✓ a\n  - b\n"
    )
    f = ROOT / "build" / "snippets" / "odd-sets.typ"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(src)
    proc = subprocess.run(
        [sys.executable, "scripts/build.py", str(f.relative_to(ROOT)), "--out", str(tmp_path)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    for s in ("1", "क", "MORNING-A"):
        assert (tmp_path / "odd-sets-test" / f"set-{s}.pdf").exists()
    import csv as csvmod
    with (tmp_path / "odd-sets-test" / "answer_key.csv").open() as fh:
        rows = list(csvmod.DictReader(fh))
    assert {r["set"] for r in rows} == {"1", "क", "MORNING-A"}
