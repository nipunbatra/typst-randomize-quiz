"""The VS Code kit ships with the repo — its snippets must stay compilable.
Every snippet body (with placeholder defaults substituted) is compiled: full-
document snippets alone, question snippets together under a quiz scaffold."""

import json
import re
import subprocess

from conftest import ROOT

SNIPPETS = json.loads((ROOT / ".vscode" / "quizforge.code-snippets").read_text())

PLACEHOLDER_CHOICE = re.compile(r"\$\{\d+\|([^|,}]+)[^}]*\}")
PLACEHOLDER_DEFAULT = re.compile(r"\$\{\d+:([^}]*)\}")
PLACEHOLDER_BARE = re.compile(r"\$\d+")


def realize_snippet(body_lines):
    text = "\n".join(body_lines)
    text = PLACEHOLDER_CHOICE.sub(r"\1", text)
    text = PLACEHOLDER_DEFAULT.sub(r"\1", text)
    text = PLACEHOLDER_BARE.sub("", text)
    # snippets import via @local; tests compile against the repo source
    return text.replace('@local/quizforge:0.1.0', '/quizforge/lib.typ')


SCRATCH = ROOT / "build" / "snippets"  # must live under the typst --root


def compile_ok(src, tmp_path, name):
    SCRATCH.mkdir(parents=True, exist_ok=True)
    f = SCRATCH / f"{name}.typ"
    f.write_text(src)
    proc = subprocess.run(
        ["typst", "compile", str(f), str(tmp_path / f"{name}.pdf"), "--root", str(ROOT)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"{name}:\n{proc.stderr}\n--- source ---\n{src}"


def test_snippets_are_valid_json_and_typst_scoped():
    assert len(SNIPPETS) >= 10
    for name, snip in SNIPPETS.items():
        assert snip["scope"] == "typst", name
        assert snip["prefix"].startswith("qf-"), name
        assert snip["body"], name


def test_full_document_snippets_compile(tmp_path):
    for name, snip in SNIPPETS.items():
        src = realize_snippet(snip["body"])
        if src.lstrip().startswith("#import"):
            compile_ok(src, tmp_path, snip["prefix"])


def test_question_snippets_compile_under_scaffold(tmp_path):
    parts = [
        '#import "/quizforge/lib.typ": *',
        '#show: quiz.with(id: "snippet-test", sets: ("A",))',
        "= Part A",
        "",
    ]
    n = 0
    questions, headings = [], []
    for name, snip in SNIPPETS.items():
        src = realize_snippet(snip["body"])
        if src.lstrip().startswith("#import"):
            continue  # full documents, tested above
        (headings if src.lstrip().startswith("=") else questions).append(src)
        n += 1
    assert n >= 7
    parts += questions
    for hi, h in enumerate(headings):  # a part snippet needs >= 1 question under it
        parts += [h, f"+ Filler question number {hi} for the part above?", "  - ✓ yes", "  - no", ""]
    compile_ok("\n".join(parts), tmp_path, "all-question-snippets")


def test_tasks_and_extensions_parse():
    tasks = json.loads((ROOT / ".vscode" / "tasks.json").read_text())
    assert any("build current exam" in t["label"] for t in tasks["tasks"])
    ext = json.loads((ROOT / ".vscode" / "extensions.json").read_text())
    assert "myriad-dreamin.tinymist" in ext["recommendations"]
