#!/usr/bin/env python3
"""Assemble the GitHub Pages site: build every gallery exam, render previews,
and generate one page per exam showing all of its randomized versions.

    python3 scripts/make_site.py --out _site
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (exam file, one-line blurb for the exam page)
GALLERY = [
    ("exams/quiz3.typ", "Native kNN and loss-curve figures, confusion matrix and entropy tables, math blanks."),
    ("exams/quiz4-ml23.typ", "Real 2023 course questions ported verbatim: data tables, block quotes, fractional marks."),
    ("exams/demo-physics.typ", "Projectile figure, unit-heavy numerics, a kinematics derivation."),
    ("exams/demo-chemistry.typ", "Molecular formulas, two-blank equation balancing, booklet-mode Part C (no answer space)."),
    ("exams/demo-algorithms.typ", "Code traces, a true/false pair, master-theorem recurrences, two-column options."),
    ("exams/demo-linear-algebra.typ", "Matrices, a multi-select on invertibility, an eigenvalue proof with rubric."),
    ("exams/demo-economics.typ", "Supply–demand figure, elasticity from a table, an essay — plus a custom footer."),
]

PAGE_CSS = """
  :root { --bg:#fdfdfb; --fg:#1a1a1a; --muted:#55555c; --rule:#c9c9c2;
          --accent:#0a5c2c; --card:#ffffff; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#161615; --fg:#e8e8e4; --muted:#a2a29c; --rule:#3c3c39;
            --accent:#6fbe8b; --card:#1d1d1c; } }
  * { box-sizing:border-box; margin:0; }
  body { background:var(--bg); color:var(--fg);
         font:17px/1.6 "Source Serif 4", Georgia, serif; padding:0 24px; }
  .page { max-width:900px; margin:0 auto; }
  a { color:var(--accent); }
  header { padding:48px 0 10px; border-bottom:2px solid var(--fg); }
  header .crumb { font-family:"Source Sans 3",sans-serif; font-size:.85rem; }
  header .crumb a { text-decoration:none; }
  h1 { font-size:1.9rem; margin-top:6px; }
  .facts { font-family:"Source Sans 3",sans-serif; font-size:.88rem;
           color:var(--muted); margin:10px 0 14px; display:flex; gap:18px; flex-wrap:wrap; }
  p.blurb { margin:22px 0 6px; }
  h2 { font-size:1.15rem; margin:34px 0 12px; padding-bottom:5px;
       border-bottom:1px solid var(--rule); }
  .sets { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
  @media (max-width:820px){ .sets { grid-template-columns:repeat(2,1fr);} }
  figure { border:1px solid var(--rule); background:var(--card); padding:7px; margin:0; }
  figure img { width:100%; display:block; border:1px solid var(--rule); }
  figcaption { font-family:"Source Sans 3",sans-serif; font-size:.82rem; padding-top:7px; }
  figcaption b { font-size:.95rem; }
  figcaption a { text-decoration:none; }
  .keyrow { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
  @media (max-width:700px){ .keyrow { grid-template-columns:1fr; } }
  footer { margin:56px 0 36px; padding-top:10px; border-top:2px solid var(--fg);
           font-family:"Source Sans 3",sans-serif; font-size:.84rem; color:var(--muted); }
"""

FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,700'
    '&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">'
)


def run(cmd, what, ok_fail=False):
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0 and not ok_fail:
        sys.stderr.write(f"error: {what}\n{proc.stderr}\n")
        raise SystemExit(1)
    return proc.returncode == 0


def query_meta(exam):
    proc = subprocess.run(
        ["typst", "query", exam, "<answerkey>", "--field", "value", "--one", "--root", str(ROOT)],
        cwd=ROOT, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise SystemExit(1)
    return json.loads(proc.stdout)


def png(exam, out_pattern, mode, pages, set_id="A", ok_fail=False):
    return run(
        ["typst", "compile", exam, str(out_pattern), "--root", str(ROOT),
         "--format", "png", "--pages", pages, "--ppi", "100",
         "--input", f"set={set_id}", "--input", f"mode={mode}"],
        f"png {exam} {mode} p{pages}", ok_fail=ok_fail,
    )


def exam_page_html(meta, blurb, n_questions):
    eid = meta["exam_id"]
    sets = meta["sets"]
    title = html.escape(meta["title"])
    course = html.escape(meta["course"])
    cards = []
    for s in sets:
        img = f"../assets/{eid}-set-{s}-1.png"
        cards.append(f"""    <figure>
      <a href="../pdf/{eid}-set-{s}.pdf"><img src="{img}" alt="Set {s}, page 1" loading="lazy"></a>
      <figcaption><b>Set {s}</b> ·
        <a href="../pdf/{eid}-set-{s}.pdf">paper</a> ·
        <a href="../pdf/{eid}-set-{s}-key.pdf">key</a></figcaption>
    </figure>""")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — quizforge</title>
{FONTS}
<style>{PAGE_CSS}</style>
</head>
<body><div class="page">
<header>
  <div class="crumb"><a href="../index.html">quizforge</a> / gallery / {eid}</div>
  <h1>{title}</h1>
  <div class="facts">
    <span>{course}</span>
    <span>{n_questions} questions · {meta["total"]} marks</span>
    <span>{len(sets)} randomized sets</span>
    <span><a href="https://github.com/nipunbatra/quizforge/blob/main/{meta["src"]}">source ↗</a></span>
  </div>
</header>
<p class="blurb">{html.escape(blurb)} Every set below contains <em>exactly the same
questions and total marks</em> — only the question order and the MCQ option order
differ, derived deterministically from the exam id and the set id.</p>
<h2>The {len(sets)} versions</h2>
<div class="sets">
{chr(10).join(cards)}
</div>
<h2>Answer key (set A)</h2>
<div class="keyrow">
  <figure><a href="../pdf/{eid}-set-A-key.pdf"><img src="../assets/{eid}-key-1.png" alt="Key page 1" loading="lazy"></a>
    <figcaption>✓ options, filled blanks, model answers · <a href="../pdf/{eid}-set-A-key.pdf">full key PDF</a></figcaption></figure>
</div>
<footer>MIT licensed · <a href="../index.html">back to overview</a> ·
  <a href="https://github.com/nipunbatra/quizforge">github.com/nipunbatra/quizforge</a></footer>
</div></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    args = ap.parse_args()
    out = Path(args.out).resolve()
    (out / "assets").mkdir(parents=True, exist_ok=True)
    (out / "pdf").mkdir(exist_ok=True)
    (out / "exam").mkdir(exist_ok=True)
    shutil.copy(ROOT / "site" / "index.html", out / "index.html")

    for exam, blurb in GALLERY:
        meta = query_meta(exam)
        eid = meta["exam_id"]
        meta["src"] = exam
        sets = meta["sets"]
        n_questions = sum(len(s["questions"]) for s in meta["sections"])

        run([sys.executable, "scripts/build.py", exam], f"build {exam}")
        for s in sets:
            shutil.copy(ROOT / "build" / eid / f"set-{s}.pdf", out / "pdf" / f"{eid}-set-{s}.pdf")
            shutil.copy(ROOT / "build" / eid / f"set-{s}-key.pdf", out / "pdf" / f"{eid}-set-{s}-key.pdf")
            png(exam, out / "assets" / (f"{eid}-set-{s}-{{p}}.png"), "exam", "1", set_id=s)
        # index hero/gallery assets: set-A pages, tolerating short documents
        png(exam, out / "assets" / (f"{eid}-exam-{{p}}.png"), "exam", "1-2", ok_fail=True)
        png(exam, out / "assets" / (f"{eid}-exam-{{p}}.png"), "exam", "1", ok_fail=False)
        png(exam, out / "assets" / (f"{eid}-key-{{p}}.png"), "key", "1-2", ok_fail=True)
        png(exam, out / "assets" / (f"{eid}-key-{{p}}.png"), "key", "1", ok_fail=False)
        (out / "exam" / f"{eid}.html").write_text(exam_page_html(meta, blurb, n_questions))
        print(f"✓ {eid}: {len(sets)} sets, page exam/{eid}.html")

    shutil.copy(ROOT / "build" / "es335-quiz-1" / "answer_key.csv", out / "pdf" / "answer_key.csv")
    print(f"site assembled at {out}")


if __name__ == "__main__":
    main()
