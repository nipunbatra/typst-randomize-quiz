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
    ("exams/demo-features.typ", "Every quizforge capability, one question each — see the feature tour for the code."),
]

# The feature catalog shown on features.html: (anchor, title, description, code).
FEATURES = [
    ("mcq", "Multiple choice",
     "A ✓ (or ✔ / #yes) marks the correct option; option order shuffles per set. #explain shows only in the key.",
     "+ #m(2) Which option is correct?\n  - ✓ This one\n  - Not this one\n  #explain[Key-only explanation.]"),
    ("multi", "Auto multi-select",
     "Two or more ✓ options make a multi-select — “(Select all that apply.)” is added and the key reports all letters (e.g. AB).",
     "+ #m(2) Which reduce overfitting?\n  - ✓ Dropout\n  - ✓ Weight decay\n  - More parameters"),
    ("blank", "Fill in the blank",
     "The answer lives inside the blank: hidden on the paper, printed in the key, exported to the grading CSV. Math answers work.",
     "+ #m(1) Water is H#sub[2]#blank[O], and\n  $e^(i pi) = #blank(width: 1.5cm)[$-1$]$."),
    ("answer", "Subjective + rubric",
     "answer(space) prints writing space on the paper; the model answer and rubric appear only in the key.",
     "+ #m(3) Derive the normal equation.\n  #answer(4cm, rubric: [+2 gradient; +1 solve.])[\n    $hat(theta) = (X^T X)^(-1) X^T y$]"),
    ("answer-none", "Booklet mode",
     "answer(none) prints no space — for exams answered in a separate booklet. Quiz-wide default: quiz.with(answer-space: none).",
     "+ #m(2) Answer in your booklet.\n  #answer(none)[Model answer, key only.]"),
    ("pin", "Pinned options",
     "“None/All/Both of the above” pins itself last automatically; #pin / #pin-first pin anything else under shuffling.",
     "+ #m(1) What is the output size?\n  - $30 times 30$\n  - $32 times 32$\n  - ✓ None of the above  // auto-pinned last"),
    ("columns", "Two-column options",
     "Short options in two columns to save vertical space.",
     "+ #m(1) #opts(columns: 2) Which direction?\n  - ✓ North\n  - South\n  - East\n  - West"),
    ("compact", "Compact options",
     "Options flow inline in one wrapping row — the densest layout.",
     "+ #m(1) #opts(compact: true) $2 + 2 = $?\n  - $3$\n  - ✓ $4$\n  - $5$"),
    ("freeze-options", "Frozen option order",
     "I/II/III progressions must not shuffle.",
     "+ #m(1) #opts(shuffle: false) Which are true?\n  - I only\n  - ✓ I and II\n  - II and III"),
    ("qid", "Frozen identity",
     "Question identity defaults to a hash of its own text; #qid freezes it so wording edits never reshuffle its options.",
     "+ #m(1) #qid(\"conv-output\") Editable wording,\n  stable shuffle.\n  - ✓ Stable\n  - Equally stable"),
    ("freeze-questions", "Frozen question order",
     "A part whose questions stay in authored order in every set.",
     "= Long Answers #section(shuffle: false)\n\n+ First, always first.\n  #answer(3cm)[...]"),
    ("furniture", "Custom page furniture",
     "header:/footer: accept auto (generated), none, fixed content, or a function of (exam, set, mode, total). Totals and part subtotals are always computed.",
     "#show: quiz.with(\n  id: \"quiz-1\", sets: (\"A\", \"B\"),\n  header: none,\n  footer: info => align(center,\n    text(9pt)[Set #info.at(\"set\") · #info.total marks]),\n)"),
    ("banks", "Question banks + sampling",
     "The constructor front-end: build banks with mcq()/fib()/subj(), filter by type/topic/difficulty, and pick N — the same N in every set.",
     "#make-exam(\n  exam: (id: \"midsem\", sets: (\"A\", \"B\")),\n  questions: bank,\n  sections: ((title: \"MCQ\",\n    use: (\"must-appear\",),   // guaranteed\n    filter: (type: \"mcq\"),\n    pick: 10),),             // same 10 in every set\n)"),
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


def features_page_html(shots_exam, shots_key):
    entries = []
    for anchor, title, desc, code in FEATURES:
        entries.append(
            f'<section id="{anchor}">\n  <h2>{html.escape(title)}</h2>\n'
            f'  <p>{html.escape(desc)}</p>\n'
            f'  <pre class="block">{html.escape(code)}</pre>\n</section>'
        )
    pairs = []
    for i, (e, k) in enumerate(zip(shots_exam, shots_key), start=1):
        pairs.append(
            f'    <figure><img src="assets/{e}" alt="Feature tour paper, page {i}" loading="lazy">\n'
            f'      <figcaption>Student paper — page {i}</figcaption></figure>\n'
            f'    <figure><img src="assets/{k}" alt="Feature tour key, page {i}" loading="lazy">\n'
            f'      <figcaption><b>Answer key</b> — page {i}</figcaption></figure>'
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Feature tour — quizforge</title>
{FONTS}
<style>{PAGE_CSS}
  pre.block {{ background: rgba(127,127,127,.08); border-left: 3px solid var(--accent);
              padding: 12px 14px; overflow-x: auto; font: 0.8rem/1.5 "Source Code Pro", monospace; margin: 10px 0 4px; white-space: pre; }}
  .duo {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin: 14px 0; }}
  @media (max-width:700px) {{ .duo {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body><div class="page">
<header>
  <div class="crumb"><a href="index.html">quizforge</a> / feature tour</div>
  <h1>Every capability, with the code that produces it</h1>
  <div class="facts"><span>Each snippet is a complete question — drop it into any quiz.</span>
    <span><a href="exam/qf-feature-tour.html">rendered versions ↗</a> ·
    <a href="https://github.com/nipunbatra/quizforge/blob/main/exams/demo-features.typ">full source ↗</a></span></div>
</header>
{chr(10).join(entries)}
<h2 id="rendered">The tour, rendered</h2>
<p>All of the snippets above live in one real randomized exam
(<a href="https://github.com/nipunbatra/quizforge/blob/main/exams/demo-features.typ">exams/demo-features.typ</a>).
Left: the student paper. Right: the same pages of its answer key.</p>
<div class="duo">
{chr(10).join(pairs)}
</div>
<footer>MIT licensed · <a href="index.html">back to overview</a></footer>
</div></body></html>
"""


def exam_page_html(meta, blurb, n_questions, source):
    eid = meta["exam_id"]
    sets = meta["sets"]
    title = html.escape(meta["title"])
    course = html.escape(meta["course"])
    src_name = html.escape(meta["src"])
    src_lines = source.count("\n") + 1
    source_esc = html.escape(source)
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
<h2>The source that generated all of this</h2>
<p>One file produces every version above, its keys, and the grading CSV. The
<a href="../features.html">feature tour</a> explains each marker with minimal code.</p>
<details><summary style="cursor:pointer; font-family:'Source Sans 3',sans-serif;">View {src_name} ({src_lines} lines)</summary>
<pre style="background:rgba(127,127,127,.08); padding:14px; overflow-x:auto; font:0.78rem/1.5 'Source Code Pro',monospace; margin-top:8px; white-space:pre;">{source_esc}</pre>
</details>
<footer>MIT licensed · <a href="../index.html">back to overview</a> ·
  <a href="https://github.com/nipunbatra/quizforge">github.com/nipunbatra/quizforge</a></footer>
</div></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="_site")
    ap.add_argument("--quick", action="store_true", help="build only the feature tour (for tests)")
    args = ap.parse_args()
    gallery = [g for g in GALLERY if not args.quick or "demo-features" in g[0]]
    out = Path(args.out).resolve()
    (out / "assets").mkdir(parents=True, exist_ok=True)
    (out / "pdf").mkdir(exist_ok=True)
    (out / "exam").mkdir(exist_ok=True)
    shutil.copy(ROOT / "site" / "index.html", out / "index.html")

    for exam, blurb in gallery:
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
        # index/features assets: set-A pages, tolerating short documents
        for pages in ("1-3", "1-2", "1"):
            if png(exam, out / "assets" / (f"{eid}-exam-{{p}}.png"), "exam", pages, ok_fail=pages != "1"):
                break
        for pages in ("1-3", "1-2", "1"):
            if png(exam, out / "assets" / (f"{eid}-key-{{p}}.png"), "key", pages, ok_fail=pages != "1"):
                break
        source = (ROOT / exam).read_text()
        (out / "exam" / f"{eid}.html").write_text(exam_page_html(meta, blurb, n_questions, source))
        print(f"✓ {eid}: {len(sets)} sets, page exam/{eid}.html")

    if not args.quick:
        shutil.copy(ROOT / "build" / "es335-quiz-1" / "answer_key.csv", out / "pdf" / "answer_key.csv")
    tour_exam = sorted(x.name for x in (out / "assets").glob("qf-feature-tour-exam-*.png"))
    tour_key = sorted(x.name for x in (out / "assets").glob("qf-feature-tour-key-*.png"))
    (out / "features.html").write_text(features_page_html(tour_exam, tour_key))
    print(f"site assembled at {out}")


if __name__ == "__main__":
    main()
