"""Markup-mode fuzzing: generate random PLAIN-MARKUP quizzes (the parser's
input language — headings, + items, - options, ✓ marks, blanks, markers) and
verify the parser realizes them correctly: question counts, letters, NOTA
pinning, multi-select inference, and blank export all checked per set."""

import json
import random
import subprocess

import pytest

from conftest import LETTERS, ROOT, letters_consistent, questions_of

SEEDS = list(range(12))
FUZZ_DIR = ROOT / "build" / "fuzz-markup"


def gen_markup(seed: int) -> tuple[str, dict]:
    rng = random.Random(1000 + seed)
    lines = [
        '#import "/quizforge/lib.typ": *',
        f'#show: quiz.with(id: "mfz-{seed}", sets: ("A", "B"), answer-grid: true)',
        "",
    ]
    expect = {"n_questions": 0, "nota_qs": 0, "multi_qs": 0, "fib_answers": set()}
    n_sections = rng.randint(1, 3)
    for si in range(n_sections):
        frozen = rng.random() < 0.25
        lines.append(f"= Part {si}" + (" #section(shuffle: false)" if frozen else ""))
        if rng.random() < 0.5:
            lines.append(f"Instructions for part {si} of quiz {seed}.")
        lines.append("")
        for qi in range(rng.randint(2, 6)):
            expect["n_questions"] += 1
            tag = f"s{seed}p{si}q{qi}"
            kind = rng.choice(["mcq", "mcq", "mcq", "fib", "subj"])
            marks = rng.choice(["1", "2", "1.5"])
            if kind == "mcq":
                n_opts = rng.randint(2, 6)
                multi = rng.random() < 0.25 and n_opts >= 3
                n_correct = rng.randint(2, min(3, n_opts)) if multi else 1
                correct = set(rng.sample(range(n_opts), n_correct))
                if multi:
                    expect["multi_qs"] += 1
                nota = rng.random() < 0.3 and (n_opts - 1) not in correct
                lines.append(f"+ #m({marks}) Markup fuzz question {tag}: choose well?")
                for j in range(n_opts):
                    mark = "✓ " if j in correct else ""
                    if nota and j == n_opts - 1:
                        lines.append("  - None of the above")
                        expect["nota_qs"] += 1
                    else:
                        lines.append(f"  - {mark}Choice {tag}-{j}")
            elif kind == "fib":
                k = rng.randint(1, 2)
                blanks = " and ".join(f"#blank[ans-{tag}-{i}]" for i in range(k))
                lines.append(f"+ #m({marks}) Fill {tag}: {blanks} done.")
                expect["fib_answers"].add("; ".join(f"ans-{tag}-{i}" for i in range(k)))
            else:
                space = rng.choice(["3cm", "none"])
                lines.append(f"+ #m({marks}) Discuss topic {tag} thoroughly.")
                lines.append(f"  #answer({space})[Model answer for {tag}.]")
            lines.append("")
    return "\n".join(lines), expect


def query(path, set_id):
    proc = subprocess.run(
        ["typst", "query", str(path), "<answerkey>", "--field", "value", "--one",
         "--root", str(ROOT), "--input", f"set={set_id}"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr + "\n--- source ---\n" + path.read_text()
    return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def markup_case(request):
    seed = request.param
    FUZZ_DIR.mkdir(parents=True, exist_ok=True)
    path = FUZZ_DIR / f"mfz-{seed}.typ"
    src, expect = gen_markup(seed)
    path.write_text(src)
    return path, expect


@pytest.mark.parametrize("markup_case", SEEDS, indirect=True, ids=[f"seed{s}" for s in SEEDS])
class TestMarkupFuzz:
    def test_compiles_both_modes(self, markup_case, tmp_path):
        path, _ = markup_case
        for mode in ("exam", "key"):
            proc = subprocess.run(
                ["typst", "compile", str(path), str(tmp_path / f"{mode}.pdf"),
                 "--root", str(ROOT), "--input", "set=B", "--input", f"mode={mode}"],
                cwd=ROOT, capture_output=True, text=True,
            )
            assert proc.returncode == 0, proc.stderr + "\n" + path.read_text()

    def test_parser_realizes_expected_structure(self, markup_case):
        path, expect = markup_case
        for s in ("A", "B"):
            meta = query(path, s)
            qs = questions_of(meta)
            assert len(qs) == expect["n_questions"], path.read_text()
            assert letters_consistent(meta) == []
            fibs = {q["answer"] for q in qs if q["type"] == "fill_blank"}
            assert fibs == expect["fib_answers"]
            multi = [q for q in qs if q["type"] == "mcq" and len(q["answer"]) > 1]
            assert len(multi) == expect["multi_qs"]

    def test_nota_options_pinned_in_every_set(self, markup_case):
        path, expect = markup_case
        if expect["nota_qs"] == 0:
            pytest.skip("this seed generated no NOTA options")
        for s in ("A", "B"):
            meta = query(path, s)
            pinned = 0
            for q in questions_of(meta):
                if q["type"] != "mcq":
                    continue
                # a NOTA option was authored last, so its original index is
                # len(order); pinning means it must still be displayed last
                if q["order"][-1] == len(q["order"]):
                    pinned += 1
            assert pinned >= expect["nota_qs"], f"set {s}: NOTA drifted\n{path.read_text()}"
