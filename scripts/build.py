#!/usr/bin/env python3
"""Build every set of a Typst exam: student PDFs, answer-key PDFs, grading CSV,
and a manifest with SHA-256 hashes.

    python3 scripts/build.py exams/quiz1.typ
    python3 scripts/build.py exams/quiz1.typ --sets A B --out /tmp/out

The exam file itself is the single source of truth: set membership, question
order, option order, and answers are all derived from its <answerkey> metadata
via `typst query`, produced by the same realize() call that renders the PDFs —
so the CSV cannot disagree with the printed papers.

Exits non-zero if compilation fails or any cross-set fairness invariant breaks
(differing questions/marks between sets, or an inconsistent answer key).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Fixed PDF creation timestamp (2026-01-01 UTC) so rebuilding an unchanged exam
# yields byte-identical PDFs; override with --creation-timestamp.
DEFAULT_TIMESTAMP = 1767225600


def run(cmd: list[str], what: str) -> str:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(f"error: {what} failed\n  $ {' '.join(cmd)}\n{proc.stderr}\n")
        raise SystemExit(1)
    return proc.stdout


def typst_query(typst: str, exam_rel: str, set_id: str | None) -> dict:
    cmd = [typst, "query", exam_rel, "<answerkey>", "--field", "value", "--one", "--root", str(ROOT)]
    if set_id is not None:
        cmd += ["--input", f"set={set_id}"]
    return json.loads(run(cmd, f"typst query (set {set_id or 'default'})"))


def questions_of(meta: dict) -> list[dict]:
    return [q for s in meta["sections"] for q in s["questions"]]


def check_invariants(per_set: dict[str, dict]) -> None:
    """Fail loudly if any fairness or key-consistency invariant breaks."""
    ref_set, ref = next(iter(per_set.items()))
    ref_qs = {q["id"]: q for q in questions_of(ref)}
    for set_id, meta in per_set.items():
        qs = questions_of(meta)
        assert [q["qno"] for q in qs] == list(range(1, len(qs) + 1)), f"set {set_id}: qno not contiguous"
        assert {q["id"] for q in qs} == set(ref_qs), (
            f"sets {ref_set} and {set_id} contain different questions"
        )
        assert meta["total"] == ref["total"], f"sets {ref_set} and {set_id} have different totals"
        assert meta["total"] == sum(q["marks"] for q in qs), f"set {set_id}: total != sum of marks"
        for q in qs:
            r = ref_qs[q["id"]]
            assert q["marks"] == r["marks"], f"{q['id']}: marks differ between sets"
            if q["type"] == "mcq":
                order = q["order"]
                assert sorted(order) == list(range(1, len(order) + 1)), (
                    f"set {set_id} {q['id']}: order is not a permutation"
                )
                assert q["correct_orig"] == r["correct_orig"], (
                    f"{q['id']}: correct options differ between sets"
                )
                # The letters printed in the key must point at exactly the
                # originally-correct options, mapped through the permutation.
                marked = {order[LETTERS.index(ch)] for ch in q["answer"]}
                assert marked == set(q["correct_orig"]), (
                    f"set {set_id} {q['id']}: answer letters {q['answer']!r} "
                    f"do not match correct options {q['correct_orig']}"
                )


def write_csv(path: Path, per_set: dict[str, dict]) -> int:
    rows = 0
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "exam_id", "set", "qno", "question_id", "type", "topic",
            "difficulty", "marks", "answer", "option_order",
        ])
        for set_id in sorted(per_set):
            meta = per_set[set_id]
            for q in questions_of(meta):
                w.writerow([
                    meta["exam_id"], set_id, q["qno"], q["id"], q["type"],
                    q.get("topic") or "", q.get("difficulty") or "", q["marks"],
                    q["answer"], "|".join(map(str, q.get("order", []))),
                ])
                rows += 1
    return rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exam", help="exam file, e.g. exams/quiz1.typ")
    ap.add_argument("--out", default=str(ROOT / "build"), help="output directory (default: build/)")
    ap.add_argument("--sets", nargs="*", help="build only these sets (default: all from exam.sets)")
    ap.add_argument("--typst", default="typst", help="typst binary")
    ap.add_argument("--jobs", type=int, default=8, help="parallel typst processes")
    ap.add_argument("--creation-timestamp", type=int, default=DEFAULT_TIMESTAMP,
                    help="UNIX timestamp embedded in PDFs (fixed for reproducible builds)")
    args = ap.parse_args()

    exam_path = Path(args.exam).resolve()
    try:
        exam_rel = str(exam_path.relative_to(ROOT))
    except ValueError:
        sys.stderr.write(f"error: {exam_path} must live inside the project root {ROOT}\n")
        raise SystemExit(1)

    # Bootstrap query: discovers exam id + set list, and doubles as validation —
    # every constructor assert runs during this compile.
    boot = typst_query(args.typst, exam_rel, None)
    exam_id, all_sets = boot["exam_id"], boot["sets"]
    sets = args.sets or all_sets
    unknown = [s for s in sets if s not in all_sets]
    if unknown:
        sys.stderr.write(f"error: unknown sets {unknown}; exam.sets = {all_sets}\n")
        raise SystemExit(1)

    outdir = Path(args.out) / exam_id
    outdir.mkdir(parents=True, exist_ok=True)

    def compile_pdf(set_id: str, mode: str) -> Path:
        suffix = "-key" if mode == "key" else ""
        pdf = outdir / f"set-{set_id}{suffix}.pdf"
        run([
            args.typst, "compile", exam_rel, str(pdf), "--root", str(ROOT),
            "--creation-timestamp", str(args.creation_timestamp),
            "--input", f"set={set_id}", "--input", f"mode={mode}",
        ], f"compile set {set_id} ({mode})")
        return pdf

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pdf_futs = {(s, m): pool.submit(compile_pdf, s, m) for s in sets for m in ("exam", "key")}
        query_futs = {s: pool.submit(typst_query, args.typst, exam_rel, s) for s in sets}
        pdfs = {k: f.result() for k, f in pdf_futs.items()}
        per_set = {s: f.result() for s, f in query_futs.items()}

    for s, meta in per_set.items():
        assert meta["set"] == s, f"queried set mismatch: asked {s}, got {meta['set']}"
    check_invariants(per_set)

    csv_path = outdir / "answer_key.csv"
    n_rows = write_csv(csv_path, per_set)

    typst_version = run([args.typst, "--version"], "typst --version").strip()
    ref = per_set[sets[0]]
    manifest = {
        "exam_id": exam_id,
        "course": ref["course"],
        "title": ref["title"],
        "source": exam_rel,
        "typst": typst_version,
        "creation_timestamp": args.creation_timestamp,
        "total_marks": ref["total"],
        "n_questions": len(questions_of(ref)),
        "answer_key_csv": csv_path.name,
        "sets": {
            s: {
                "exam_pdf": pdfs[(s, "exam")].name,
                "key_pdf": pdfs[(s, "key")].name,
                "sha256": {
                    pdfs[(s, "exam")].name: sha256(pdfs[(s, "exam")]),
                    pdfs[(s, "key")].name: sha256(pdfs[(s, "key")]),
                },
                "question_order": [q["id"] for q in questions_of(per_set[s])],
            }
            for s in sets
        },
    }
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    print(f"✓ {exam_id}: {len(sets)} sets × (exam + key), {ref['total']} marks, "
          f"{len(questions_of(ref))} questions each")
    print(f"  {outdir}/")
    for s in sets:
        print(f"    set-{s}.pdf  set-{s}-key.pdf")
    print(f"    answer_key.csv ({n_rows} rows)  manifest.json")


if __name__ == "__main__":
    main()
