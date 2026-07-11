"""Deterministic fuzzing: generate structurally-random exams (random section
counts, question types, option counts, pins, multi-select, float marks, pick
sampling), compile them, and check every invariant. Seeds are fixed, so a
failure reproduces exactly; the generated source is left in build/fuzz/ for
inspection."""

import json
import random
import subprocess

import pytest

from conftest import ROOT, letters_consistent, questions_of

SEEDS = list(range(24))
FUZZ_DIR = ROOT / "build" / "fuzz"
DIFF = ("easy", "medium", "hard")


def gen_exam(seed: int) -> tuple[str, dict]:
    rng = random.Random(seed)
    qcount = 0
    questions = []

    def new_mcq():
        nonlocal qcount
        qcount += 1
        qid = f"fz{seed}-q{qcount}"
        n_opts = rng.randint(2, 7)
        multiple = rng.random() < 0.25 and n_opts >= 3
        n_correct = rng.randint(2, min(3, n_opts)) if multiple else 1
        correct = set(rng.sample(range(n_opts), n_correct))
        pinned = rng.random() < 0.3
        opts = []
        for i in range(n_opts):
            flags = []
            if i in correct:
                flags.append("correct: true")
            if pinned and i == n_opts - 1:
                flags.append('fixed: "last"')
            inner = f"[Opt {qid}-{i} $x_{i}$]"
            opts.append(f"opt({', '.join(flags)}, {inner})" if flags else inner)
        marks = rng.choice([0.5, 1, 1, 2, 2.5, 3])
        shuffle = "true" if rng.random() < 0.85 else "false"
        return (
            qid, "mcq",
            f'mcq("{qid}", [Fuzz question {qid}: pick wisely.],\n'
            f'  options: ({", ".join(opts)},),\n'
            f'  marks: {marks}, multiple: {str(multiple).lower()}, shuffle: {shuffle},\n'
            f'  topic: "t{rng.randint(0, 2)}", difficulty: "{rng.choice(DIFF)}")'
        )

    def new_fib():
        nonlocal qcount
        qcount += 1
        qid = f"fz{seed}-q{qcount}"
        k = rng.randint(1, 3)
        blanks = " and ".join("#blank()" for _ in range(k))
        answers = ", ".join(f'"ans-{qid}-{i}"' for i in range(k))
        return (
            qid, "fill_blank",
            f'fib("{qid}", [Fill {blanks} please.], answers: ({answers},), marks: {rng.choice([1, 1.5, 2])})'
        )

    def new_subj():
        nonlocal qcount
        qcount += 1
        qid = f"fz{seed}-q{qcount}"
        return (
            qid, "subjective",
            f'subj("{qid}", [Discuss {qid} at length.], marks: {rng.choice([2, 3, 4])}, '
            f'answer-space: {rng.randint(2, 6)}cm, model-answer: [Model for {qid}.])'
        )

    makers = [new_mcq, new_mcq, new_fib, new_subj]
    sections_src = []
    n_sections = rng.randint(1, 3)
    for si in range(n_sections):
        n_q = rng.randint(2, 10)
        ids = []
        for _ in range(n_q):
            qid, qtype, src = rng.choice(makers)()
            questions.append(src)
            ids.append(qid)
        use = ", ".join(f'"{i}"' for i in ids)
        pick = ""
        if len(ids) >= 4 and rng.random() < 0.4:
            # sample a subset via filter+pick instead of using all of `use`
            keep = rng.randint(2, len(ids) - 1)
            guaranteed = ids[:1]
            pick = f"pick: {keep + 1},"
            use = f'"{guaranteed[0]}"'
            sections_src.append(
                f'(title: "Part {si}", use: ({use},), '
                f'filter: (type: ("mcq", "fill_blank", "subjective")), {pick}),'
            )
            continue
        shuffle = "true" if rng.random() < 0.8 else "false"
        sections_src.append(f'(title: "Part {si}", use: ({use},), shuffle: {shuffle}),')

    src = (
        '#import "/quizforge/lib.typ": *\n'
        "#make-exam(\n"
        f'  exam: (id: "fuzz-{seed}", course: "FZ 000", title: "Fuzz {seed}", sets: ("A", "B", "C")),\n'
        f'  questions: (\n' + ",\n".join(questions) + ",\n  ),\n"
        f'  sections: (\n' + "\n".join(sections_src) + "\n  ),\n"
        ")\n"
    )
    return src, {"n_declared": qcount, "n_sections": n_sections}


def query(path, set_id):
    proc = subprocess.run(
        ["typst", "query", str(path), "<answerkey>", "--field", "value", "--one",
         "--root", str(ROOT), "--input", f"set={set_id}"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


@pytest.fixture(scope="module")
def fuzz_case(request):
    seed = request.param
    FUZZ_DIR.mkdir(parents=True, exist_ok=True)
    path = FUZZ_DIR / f"fuzz-{seed}.typ"
    src, expect = gen_exam(seed)
    path.write_text(src)
    return seed, path, expect


@pytest.mark.parametrize("fuzz_case", SEEDS, indirect=True, ids=[f"seed{s}" for s in SEEDS])
class TestFuzz:
    def test_compiles_both_modes(self, fuzz_case, tmp_path):
        _, path, _ = fuzz_case
        for mode in ("exam", "key"):
            proc = subprocess.run(
                ["typst", "compile", str(path), str(tmp_path / f"{mode}.pdf"),
                 "--root", str(ROOT), "--input", "set=B", "--input", f"mode={mode}"],
                cwd=ROOT, capture_output=True, text=True,
            )
            assert proc.returncode == 0, proc.stderr + "\n--- source ---\n" + path.read_text()

    def test_fairness_across_sets(self, fuzz_case):
        _, path, expect = fuzz_case
        metas = [query(path, s) for s in ("A", "B", "C")]
        ref_ids = sorted(q["id"] for q in questions_of(metas[0]))
        assert 0 < len(ref_ids) <= expect["n_declared"]
        assert len(metas[0]["sections"]) == expect["n_sections"]
        for m in metas[1:]:
            assert sorted(q["id"] for q in questions_of(m)) == ref_ids
            assert m["total"] == metas[0]["total"]

    def test_keys_consistent_every_set(self, fuzz_case):
        _, path, _ = fuzz_case
        for s in ("A", "B", "C"):
            meta = query(path, s)
            assert letters_consistent(meta) == [], f"set {s}\n{path.read_text()}"
            for q in questions_of(meta):
                if q["type"] == "mcq":
                    assert sorted(q["order"]) == list(range(1, len(q["order"]) + 1))
