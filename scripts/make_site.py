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
  :root { --bg:#fbfbf9; --surface:#fff; --ink:#17232b; --muted:#5c6a72; --faint:#8a969c;
          --accent:#0a6b34; --accent2:#8f1d1d; --border:#eae7df; --code:#f5f4ef;
          --shadow:0 1px 2px rgba(20,32,28,.05),0 6px 22px rgba(20,32,28,.05); }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#0e1311; --surface:#151c19; --ink:#e7ede9; --muted:#94a49b; --faint:#6b7f76;
            --accent:#5cc084; --accent2:#e28f8f; --border:#233029; --code:#111815;
            --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 26px rgba(0,0,0,.30); } }
  :root[data-theme="light"] { --bg:#fbfbf9; --surface:#fff; --ink:#17232b; --muted:#5c6a72; --faint:#8a969c; --accent:#0a6b34; --accent2:#8f1d1d; --border:#eae7df; --code:#f5f4ef; --shadow:0 1px 2px rgba(20,32,28,.05),0 6px 22px rgba(20,32,28,.05); }
  :root[data-theme="dark"] { --bg:#0e1311; --surface:#151c19; --ink:#e7ede9; --muted:#94a49b; --faint:#6b7f76; --accent:#5cc084; --accent2:#e28f8f; --border:#233029; --code:#111815; --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 26px rgba(0,0,0,.30); }
  * { box-sizing:border-box; margin:0; } html { scroll-behavior:smooth; }
  body { background:var(--bg); color:var(--ink); -webkit-font-smoothing:antialiased;
         font:16px/1.62 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif; }
  code,pre { font-family:ui-monospace,"SF Mono","JetBrains Mono",Menlo,Consolas,monospace; }
  a { color:var(--accent); text-decoration:none; } a:hover { color:var(--accent2); }
  .page { max-width:960px; margin:0 auto; padding:0 24px 10px; }
  nav { position:sticky; top:0; z-index:20; background:color-mix(in srgb,var(--bg) 82%,transparent);
        backdrop-filter:saturate(160%) blur(10px); border-bottom:1px solid var(--border); }
  nav .row { max-width:960px; margin:0 auto; padding:11px 24px; display:flex; align-items:center; gap:14px; flex-wrap:wrap; }
  .brand { font-weight:800; font-size:1.1rem; letter-spacing:-.02em; color:var(--ink); }
  .brand .dot { color:var(--accent2); }
  .navpk { display:flex; gap:4px; flex-wrap:wrap; flex:1; }
  .navpk a { font-size:.8rem; color:var(--muted); padding:3px 8px; border-radius:6px; }
  .navpk a:hover { background:var(--code); color:var(--ink); }
  .ghlink { font-size:.85rem; color:var(--muted); font-weight:600; white-space:nowrap; }
  .themetoggle { cursor:pointer; background:none; border:1px solid var(--border); color:var(--muted);
    border-radius:7px; width:30px; height:30px; font-size:.9rem; display:grid; place-items:center; }
  .themetoggle:hover { color:var(--ink); border-color:var(--accent); }
  header.page-head { padding:44px 0 22px; margin-bottom:6px; border-bottom:1px solid var(--border); }
  header .crumb { font-size:.82rem; color:var(--muted); }
  h1 { font-size:2.2rem; letter-spacing:-.02em; margin-top:10px; font-weight:800; }
  .facts { font-size:.86rem; color:var(--muted); margin-top:12px; display:flex; gap:16px; flex-wrap:wrap; }
  p.blurb { margin:22px 0 6px; max-width:74ch; }
  h2 { font-size:1.3rem; font-weight:800; letter-spacing:-.01em; margin:34px 0 14px; }
  .sets { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; }
  @media (max-width:820px){ .sets { grid-template-columns:repeat(2,1fr);} }
  figure { border:1px solid var(--border); background:var(--surface); padding:8px; margin:0;
           border-radius:12px; box-shadow:var(--shadow); transition:transform .14s,border-color .14s; }
  figure:hover { transform:translateY(-3px); border-color:var(--accent); }
  figure img { width:100%; display:block; border:1px solid var(--border); border-radius:7px; }
  figcaption { font-size:.82rem; color:var(--muted); padding:9px 4px 3px; }
  figcaption b { font-size:.92rem; color:var(--ink); }
  .keyrow { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
  @media (max-width:700px){ .keyrow { grid-template-columns:1fr; } }
  footer { margin:56px 0 40px; padding-top:14px; border-top:1px solid var(--border);
           font-size:.84rem; color:var(--muted); }
"""

THEME_INIT = '<script>(function(){var t=localStorage.getItem("qf-theme");if(t)document.documentElement.setAttribute("data-theme",t);})();</script>'


def nav_html(base=""):
    """Sticky nav shared by every sub-page. `base` is the path prefix to the site root."""
    return (
        '<nav><div class="row">'
        f'<a href="{base}index.html" class="brand">quizforge<span class="dot">.</span></a>'
        '<div class="navpk">'
        f'<a href="{base}index.html#overview">overview</a>'
        f'<a href="{base}index.html#design">design</a>'
        f'<a href="{base}index.html#gallery">gallery</a>'
        f'<a href="{base}features.html">features&nbsp;↗</a>'
        f'<a href="{base}index.html#reference">reference</a>'
        '</div>'
        '<a class="ghlink" href="https://github.com/nipunbatra/quizforge">GitHub&nbsp;↗</a>'
        '<button class="themetoggle" onclick="var d=document.documentElement,'
        "n=(d.getAttribute('data-theme')==='dark')?'light':'dark';"
        "d.setAttribute('data-theme',n);localStorage.setItem('qf-theme',n);"
        '" aria-label="Toggle theme">◑</button>'
        '</div></nav>'
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
{THEME_INIT}
<style>{PAGE_CSS}
  pre.block {{ background:var(--code); border:1px solid var(--border); border-left:3px solid var(--accent);
              border-radius:11px; padding:13px 15px; overflow-x:auto; font:0.8rem/1.55 ui-monospace,monospace;
              margin:10px 0 4px; white-space:pre; }}
  section#tour-body > section {{ padding-top:8px; }}
  section#tour-body > section h2 {{ font-size:1.08rem; margin:28px 0 6px; }}
  section#tour-body > section p {{ color:var(--muted); max-width:74ch; margin:6px 0; }}
  .duo {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; margin: 14px 0; }}
  @media (max-width:700px) {{ .duo {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
{nav_html("")}
<div class="page">
<header class="page-head">
  <div class="crumb"><a href="index.html">quizforge</a> / feature tour</div>
  <h1>Every capability, with the code that produces it</h1>
  <div class="facts"><span>Each snippet is a complete question — drop it into any quiz.</span>
    <span><a href="exam/qf-feature-tour.html">rendered versions ↗</a> ·
    <a href="https://github.com/nipunbatra/quizforge/blob/main/exams/demo-features.typ">full source ↗</a></span></div>
</header>
<section id="tour-body">
{chr(10).join(entries)}
</section>
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
{THEME_INIT}
<style>{PAGE_CSS}</style>
</head>
<body>
{nav_html("../")}
<div class="page">
<header class="page-head">
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
