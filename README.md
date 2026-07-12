# quizforge

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
tests/                490 checks: invariant matrix over every exam×set, 24-seed fuzzer, goldens, error contract
```

```bash
make build [EXAM=exams/quiz2.typ]   # PDFs + keys + CSV + manifest into build/
make test                           # pytest suite
make watch / watch-key [SET=B]      # live preview while authoring
make install-local                  # use @local/quizforge:0.1.0 from any project
```

Requires `typst` ≥ 0.14 and Python 3.10+ (stdlib only, tooling-only).

## Editor setup (VS Code)

Open the repo in VS Code and install the recommended
[Tinymist](https://marketplace.visualstudio.com/items?itemName=myriad-dreamin.tinymist)
extension (`.vscode/extensions.json` suggests it) — you get live preview and
quizforge's compile-time validation as inline squiggles pointing at the
offending question. The repo ships:

- **Snippets** — type `qf-` for a full quiz scaffold, MCQs, multi-select,
  blanks, subjective/booklet questions, compact/two-column options, parts,
  and a bank-style exam (all snippet bodies are compile-tested in CI).
- **Tasks** — `⇧⌘B` builds the current exam (all sets + keys + CSV); watch
  tasks live-preview the paper or the key.

Common mistakes fail compilation with messages that say how to fix them:
markdown-style `*` options, `____` underscores instead of `#blank[...]`,
dedented options, a stray `#m(...)` between questions, duplicate questions,
missing ✓, and ~35 more — see `tests/fixtures/` for the full contract.

## Guarantees

Deterministic (pure function of ids — rebuilds byte-identical) · fair (same
questions + totals per set, sampling can't differ across sets) · key-safe
(paper/key/CSV from one structure, independently re-verified) · validated at
compile time (structural mistakes name the question and fail the build) ·
answer-free student PDFs.

⚠️ `id:` (and question wording, unless `#qid`-frozen) seed the shuffles —
freeze them once a paper is printed, and archive `build/<exam_id>/`.

## Typst Universe

Submitted as [typst/packages#5322](https://github.com/typst/packages/pull/5322).
Once merged, imports become `@preview/quizforge:0.1.0` and
`typst init @preview/quizforge` scaffolds a new exam from the template.
Until then, `make install-local` provides `@local/quizforge:0.1.0`.
