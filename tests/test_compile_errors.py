"""Every invalid bank/exam must fail to COMPILE, with a message that tells the
author exactly what to fix. Validation lives in the Typst constructors, so
`typst compile` is the validator — these tests pin that contract."""

import subprocess

import pytest

from conftest import ROOT

CASES = [
    ("one-option.typ", "needs at least 2 options", []),
    ("no-correct.typ", "exactly one option must be correct (got 0)", []),
    ("two-correct.typ", "exactly one option must be correct (got 2)", []),
    ("bad-fixed.typ", 'fixed must be "first" or "last"', []),
    ("zero-marks.typ", "marks must be a positive number", []),
    ("bad-id.typ", "id must be a slug", []),
    ("empty-answers.typ", "needs at least one answer", []),
    ("dup-id.typ", "duplicate question id: q-1", []),
    ("unknown-use.typ", "unknown question id in use: nope", []),
    ("pick-range.typ", "pick 5 out of range", []),
    ("empty-section.typ", "section selects no questions", []),
    ("bad-filter-key.typ", "unknown filter key: tag", []),
    ("blank-mismatch.typ", "body has 1 blank marker(s) but 2 answer(s)", []),
    ("stray-blank.typ", "only valid inside a fib() question body", []),
    ("unknown-set.typ", "unknown set 'Z'", ["--input", "set=Z"]),
    # markup front-end
    ("markup-no-correct.typ", "no option is marked correct", []),
    ("markup-one-option.typ", "needs at least 2 options", []),
    ("markup-stray-content.typ", "free content between questions is not supported", []),
    ("markup-yes-in-body.typ", "belong on options", []),
    ("markup-blank-and-options.typ", "cannot have both options and #blank", []),
    ("markup-no-quiz-id.typ", "give the quiz an id", []),
    ("markup-deep-heading.typ", "only level-1 headings", []),
    ("markup-empty-option.typ", "an option is empty", []),
    ("markup-marker-in-option.typ", "cannot appear inside an option", []),
    ("markup-answer-in-mcq.typ", "is for subjective questions", []),
    ("markup-identical-questions.typ", "are identical (same text or same #qid)", []),
    ("markup-empty-part.typ", "part 'Empty Part' has no questions", []),
    ("markup-sec-in-body.typ", "belongs in a part heading", []),
    ("markup-explain-on-subjective.typ", "only supported on MCQs", []),
    ("too-many-options.typ", "at most 26 options", []),
    ("markup-set-in-body.typ", "move them above the '#show: quiz' line", []),
    ("markup-dedented-option.typ", "indent options two spaces", []),
    ("markup-starred-options.typ", "a ✓ appears in the question text but the question has no options", []),
    ("markup-underscore-blank.typ", "write blanks as #blank[the answer]", []),
    ("markup-stray-marker.typ", "between questions — markers belong inside", []),
    ("markup-double-marks.typ", "#m(...) appears more than once", []),
    ("markup-empty-blank.typ", "blank[] answer must not be empty", []),
    ("empty-fib-answer.typ", "a blank's answer is empty", []),
    ("empty-sets.typ", "exam.sets must not be empty", []),
    ("dup-sets.typ", "exam.sets contains duplicates", []),
]


@pytest.mark.parametrize("fname,expected,extra", CASES, ids=[c[0] for c in CASES])
def test_invalid_input_fails_compile(fname, expected, extra, tmp_path):
    proc = subprocess.run(
        ["typst", "compile", f"tests/fixtures/{fname}", str(tmp_path / "out.pdf"),
         "--root", str(ROOT), *extra],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode != 0, f"{fname} compiled but should have failed"
    assert expected in proc.stderr, (
        f"{fname}: expected error containing {expected!r}, got:\n{proc.stderr}"
    )
