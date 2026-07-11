# typst-randomize-quiz — home of the `quizforge` package

Write an exam as a **plain Typst document**; get N randomized sets (question +
option order shuffled deterministically per set), matching answer keys, and a
grading CSV. Package docs & authoring guide: [`quizforge/README.md`](quizforge/README.md).
Design & invariants: [`SPEC.md`](SPEC.md).

```typst
#import "@local/quizforge:0.1.0": *          // after: make install-local

#show: quiz.with(id: "quiz-1", course: "ES 667", sets: ("A", "B", "C", "D"))

= Multiple Choice
+ #m(2) What does $"softmax" + "cross-entropy"$ give as gradient?
  - ✓ $p - y$
  - $y - p$
  - None of the above
```

That file compiled as-is is the **answer key**; `--input set=B --input mode=exam`
is a randomized student paper; `scripts/build.py` makes everything at once.

## Repo layout & commands

```
quizforge/            the package (Universe-ready: manifest, license, template, thumbnail)
exams/                demos: quiz3.typ (ML, figures+tables) · quiz4-ml23.typ (ported real 2023 papers) · quiz2.typ · quiz1.typ (banks)
questions/            demo banks for the constructor front-end
scripts/build.py      all sets ∥ → invariant checks → answer_key.csv + manifest.json
tests/                78 pytest cases: determinism, fairness, key correctness, error contract
```

```bash
make build [EXAM=exams/quiz2.typ]   # PDFs + keys + CSV + manifest into build/
make test                           # pytest suite
make watch / watch-key [SET=B]      # live preview while authoring
make install-local                  # use @local/quizforge:0.1.0 from any project
```

Requires `typst` ≥ 0.13 and Python 3.10+ (stdlib only, tooling-only).

## Guarantees

Deterministic (pure function of ids — rebuilds byte-identical) · fair (same
questions + totals per set, sampling can't differ across sets) · key-safe
(paper/key/CSV from one structure, independently re-verified) · validated at
compile time (structural mistakes name the question and fail the build) ·
answer-free student PDFs.

⚠️ `id:` (and question wording, unless `#qid`-frozen) seed the shuffles —
freeze them once a paper is printed, and archive `build/<exam_id>/`.

## Publishing to Typst Universe

`quizforge/` is submission-shaped: copy it to `typst/packages` as
`packages/preview/quizforge/0.1.0` and open a PR. After acceptance, imports
become `@preview/quizforge:0.1.0` and `typst init @preview/quizforge`
scaffolds a new exam from the template.
