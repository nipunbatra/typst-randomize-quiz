# quizforge — Specification

**quizforge** is a Typst package that builds multiple randomized sets of an exam from a
single source document — question order and MCQ option order shuffled deterministically
per set — with auto-generated answer keys and machine-readable grading metadata. This
repository is its development home: package source, build tooling, demo exams, tests.

Version: 3.0 (package + plain-markup front-end) · Typst ≥ 0.13 · Python ≥ 3.10 (tooling only)

Authoring reference and examples live in [`quizforge/README.md`](quizforge/README.md)
(the Typst Universe page). This spec covers design, invariants, and testing.

---

## 1. Goals

1. **The paper setter writes a plain Typst document.** Headings are parts, `+` items
   are questions, `-` items are options, `✓` marks the correct one. No ids, no data
   files, no schemas. Everything else (types, multi-select, pinned "None of the above")
   is inferred. Compiled as-is, the master **is** the answer key.
2. **Deterministic randomization.** Every set is a pure function of
   `(exam id, set id, question identity)`. No clocks, no OS RNG, no package deps —
   a seeded FNV-1a → xorshift32 → Fisher–Yates pipeline in pure Typst. Rebuilds are
   byte-identical (fixed PDF creation timestamp).
3. **Fairness invariants, enforced.** Every set has exactly the same questions and
   total marks; only order differs; section order is fixed. Bank sampling (`pick`)
   seeds *without* the set id, so it can never break fairness.
4. **Correct keys, by construction.** Paper, key PDF, and grading metadata derive from
   one realized structure per set. The build tool *re-verifies* the letter↔option
   mapping anyway and refuses to ship a mismatch.
5. **Validation = compilation.** Structural rules are compile-time asserts naming the
   offending question. No separate validator exists to forget.
6. **Two front-ends, one engine.** Plain markup for "just write the paper"; constructor
   banks (`mcq()/fib()/subj()` + `filter`/`use`/`pick`) for semester-scale reuse.
7. **Distributable.** Universe-grade package (`typst.toml`, MIT, template, thumbnail);
   works standalone via `@local`/`@preview` imports — the Python tooling is optional.

### Non-goals (v3)

OMR/scanner-tuned sheets · auto-grading of scans · parameterized numeric variants ·
per-student papers (a set id is any string; roster integration is out of scope) ·
free content between shuffled questions (rejected at compile time — it cannot move
with a shuffled question).

---

## 2. Architecture

```
quizforge/                        the package (Typst-only, self-contained)
├── typst.toml  LICENSE  README.md  thumbnail.png
├── lib.typ                       public API (re-exports)
├── template/main.typ             `typst init @preview/quizforge` starter
└── src/
    ├── rng.typ                   FNV-1a hash · xorshift32 · shuffle · sample
    ├── base.typ                  states, plaintext() extraction, constants
    ├── model.typ                 constructors + inline markers + validation
    ├── realize.typ               selection, per-set shuffles, <answerkey> data
    ├── render.typ                exam/key rendering, cover, grid, make-exam()
    └── parse.typ                 content-tree walker + quiz() show-rule

scripts/build.py                  compile all sets ∥ → verify invariants → CSV + manifest
exams/ questions/ tests/          demos (markup + banks) and the pytest suite
```

**Flow:** both front-ends produce the same config `(exam, questions, sections)`.
`realize(config, set)` computes pure data — final question order, permuted options,
correct letters. Rendering consumes it, and `meta-of()` embeds its data view as
`#metadata(..) <answerkey>`, which `typst query` exports for tooling. Content values
never enter the metadata; answers never enter the student PDF.

**The markup parser** (`parse.typ`) walks the document's content tree (`.children`,
`.func()`, field access) handed to `#show: quiz`. Level-1 headings open sections;
content before a section's first question becomes its instructions; enum items become
questions; their top-level list items become options. Invisible `metadata` markers
(`#m`, `#qid`, `#opts`, `#explain`, `#answer`, `#blank`, `#section`, `#yes`, `#pin`)
carry structure without affecting rendering; a leading `✓` text node is detected and
stripped (the renderer re-adds key styling). Question type is inferred:
options → `mcq`, blank markers → `fill_blank`, else `subjective`.

### Seed design

| Purpose          | Seed string                          | Consequence |
|------------------|--------------------------------------|-------------|
| Question order   | `{exam_id}\|{set}\|q\|{section idx}` | differs per set; independent of question ids/text |
| Option order     | `{exam_id}\|{set}\|o\|{question id}` | depends only on exam, set, and that question's own identity |
| `pick` sampling  | `{exam_id}\|sample\|{section idx}`   | no set id → identical questions in every set |

**Question identity** (markup mode): explicit `#qid("slug")`, else
`"q" + fnv1a(plaintext(body))`. Consequences: reordering/inserting/deleting questions
never reshuffles others (order permutations are positional); editing a question's
wording reshuffles only its own options. `plaintext()` skips invisible elements
(metadata, state/counter updates, context), so marker edits don't change identity.

---

## 3. Interfaces

### Authoring (see package README for the full marker table)

```typst
#show: quiz.with(id: .., course: .., title: .., date: .., duration: ..,
                 sets: ("A", ..), answer-grid: bool, instructions: (..))
```
Markup master; default mode **key** (the master is the key). Or constructor style:
```typst
#make-exam(exam: (id: .., sets: .., ..), questions: bank,
           sections: ((title: .., use: (..), filter: (type: ..), pick: N, shuffle: bool), ..))
```
Default mode **exam**. Both honor `--input set=<id>` and `--input mode=exam|key`.
(`use` questions are guaranteed; `pick` is the section total; `filter` matches
`type`/`topic`/`difficulty` as value or list. `set`/`include` are Typst keywords —
hence `"set"` quoted in dicts and `use` as the field name.)

### Build tooling

```bash
python3 scripts/build.py exams/quiz2.typ      # or: make build EXAM=...
make watch | watch-key [SET=B]                # live preview
make install-local                            # symlink as @local/quizforge:<ver>
```

Outputs to `build/<exam_id>/`: `set-<S>.pdf`, `set-<S>-key.pdf`,
`answer_key.csv` (`exam_id,set,qno,question_id,type,topic,difficulty,marks,answer,option_order`),
`manifest.json` (per-set question order, SHA-256 of every PDF, typst version).
Answers: MCQ letters (`B`, `AC`), fill-blank text (`; `-joined), `MANUAL` for
subjective. build.py exits non-zero on compile failure or any invariant breach
(question sets/totals differ, non-permutation order, letters ↮ correct options).

---

## 4. Compile-time validation

Constructors: bad id slug · marks ≤ 0 · < 2 options · wrong correct count (unless
`multiple`) · bad `fixed` · empty `answers` · non-length spaces/widths · duplicate ids ·
unknown `use` ids / filter keys · `pick` out of range · empty section · unknown set ·
blank-marker/answer mismatch · answer-less `blank()` outside `fib()`.
Parser: no option marked ✓ · empty option/question body · ✓/`#yes`/`#pin` in a question
body · options + `#blank` in one question · level-≥2 headings · free content between
questions · missing quiz id.

## 5. Testing (490 checks, all deterministic)

- **Compile-error contract:** 37 fixtures fail with their exact message.
- **Property matrix:** every invariant checked on every set of every exam in the repo (tests/test_properties.py); structural fuzzing over 24 seeded random exams (tests/test_fuzz.py); golden CSV + golden question order pin cross-platform determinism.
- **Determinism:** metadata byte-identical across runs; PDF bytes reproducible.
- **Distinctness:** distinct question orders per set; option permutations differ.
- **Fairness:** same id multiset, totals, contiguous qno; `pick` subset identical.
- **Key correctness:** CSV/metadata letters, mapped through each recorded permutation,
  land exactly on the originally-correct options — every set, both front-ends.
- **Markup semantics:** ✓ detection, auto multi-select, NOTA auto-pin, hash + `#qid`
  ids, blank extraction (`2 λ θ; decay`), section shuffle freeze, instructions capture.
- **Outputs:** CSV ↔ metadata field equality; manifest hashes match files.
- **Stress:** torture markup (unicode, code blocks, tables in options, blanks in
  math, pinned+✓), 100-question generated paper under a time budget, RNG
  position-uniformity + hash regression pin, multi-file quizzes via #include,
  ported real 2023 course papers (exams/quiz4-ml23.typ), custom header/footer.

## 6. Operational guidance

Freeze `id` (and add `#qid` where wording may change) once a paper is printed. Archive
`build/<exam_id>/` — the manifest hashes prove what went to print. Grade MCQs by joining
responses with `answer_key.csv` on `(set, qno)`. Publication: copy `quizforge/` into
`typst/packages` as `packages/preview/quizforge/0.1.0` and open a PR; bump versions for
any post-print change, never mutate a published version.

## 7. Roadmap

Single-compile all-sets booklet (per-set page numbering needs counter surgery) ·
parameterized numeric variants · roster-driven per-student sets · OMR sheet ·
Moodle/GIFT export · difficulty-mix targets in `pick`.
