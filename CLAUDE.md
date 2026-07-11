# typst-randomize-quiz — dev home of the `quizforge` Typst package

Randomized exam sets from one Typst source, two front-ends (plain markup via
`#show: quiz`, constructor banks via `make-exam`), one engine. Design: SPEC.md.
User-facing docs: quizforge/README.md.

## Commands

- `make build [EXAM=exams/quiz2.typ]` — all sets + keys + CSV + manifest
- `make test` — run after ANY change to quizforge/src or scripts/
- `make watch / watch-key [SET=B]` — live preview
- `make install-local` — symlink as `@local/quizforge:<version>`
- Single set: `typst compile exams/quiz2.typ out.pdf --root . --input set=B --input mode=exam`

## Architecture in one breath

`parse.typ` (content-tree walker behind `#show: quiz`) and `model.typ`
constructors both produce `(exam, questions, sections)`; `realize.typ` turns
that + a set id into pure data (order, permutations, letters); `render.typ`
renders it AND embeds `meta-of()` as `<answerkey>` metadata — paper, key, CSV
cannot disagree. `rng.typ` = dependency-free seeded PRNG; every shuffle seeds
from explicit strings (SPEC §2 table).

## Invariants (tests pin all of these)

- Same questions/marks in every set; `pick` seeds exclude the set id on purpose.
- Option seed = `exam|set|o|question-id`; markup ids hash the question's own
  plaintext (invisible elements skipped) — editing one question must never
  reshuffle another.
- No typst packages, clocks, or nondeterminism in quizforge/src — offline,
  reproducible builds are hard requirements.
- Validation is compile-time asserts. New rule ⇒ new fixture in tests/fixtures/
  + a case in test_compile_errors.py CASES.
- Markup masters default to mode=key (master IS the key); make-exam defaults
  to mode=exam.

## Gotchas

- `set`/`include` are Typst keywords → dict key `"set"` quoted, section field
  named `use`.
- In Typst code blocks, statement values JOIN the implicit result — discard
  mutating returns (`let _ = arr.pop()`) or you get "cannot join content with
  dictionary".
- Content-tree facts (verified 0.14): `c.func() == enum.item / list.item /
  heading / metadata` work; markup words split as text+space nodes; repr names
  of invisibles: "counter-update", "state-update", "context", "metadata".
- Editing demo exams changes realized orders → update exact assertions in
  tests/test_build.py / test_markup.py.
- `@word` in question text is Typst reference syntax — quote or escape it.
- Marker collection must walk ALL content fields via `.fields()` — `attach`
  (math scripts), `frac`, figure captions etc. don't use body/children. A
  blank inside `$x^(#blank[..])$` broke the old body/children-only walker.
- `#include`d content arrives as a nested `sequence` — `_flat-children`
  unwraps it; a `#set` in the body arrives as `styled` and is rejected.
- Math `$-1$` extracts via plaintext() as unicode minus "−1", not ASCII "-1".
- Element `.text` fields are NOT always strings: math `op` stores content
  there. Smartquotes need explicit handling in plaintext() or they leak repr.
- Context-based package output (unify qty()) is statically opaque: plaintext
  returns "" — blanks/options must tolerate it (CSV placeholder "(see key)").
- Universe submission: copy quizforge/ to typst/packages as
  packages/preview/quizforge/<version>; never mutate a published version.
