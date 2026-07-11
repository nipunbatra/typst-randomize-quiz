"""The site generator is part of the shipped tooling — test it like one."""

import subprocess
import sys

from conftest import ROOT


def test_make_site_quick(tmp_path):
    out = tmp_path / "_site"
    proc = subprocess.run(
        [sys.executable, "scripts/make_site.py", "--out", str(out), "--quick"],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert (out / "index.html").exists()
    assert (out / "features.html").exists()
    page = (out / "exam" / "qf-feature-tour.html").read_text()
    assert "View exams/demo-features.typ" in page          # embedded source
    assert "qf-feature-tour-set-B-1.png" in page           # per-set preview
    for a in ("qf-feature-tour-set-A-1.png", "qf-feature-tour-set-B-1.png",
              "qf-feature-tour-exam-1.png", "qf-feature-tour-key-1.png"):
        assert (out / "assets" / a).exists(), a
    features = (out / "features.html").read_text()
    for anchor in ("compact", "answer-none", "qid", "banks"):
        assert f'id="{anchor}"' in features
    assert "#opts(compact: true)" in features              # snippet made it through escaping


def test_features_page_covers_documented_markers():
    """Every marker exported by the package must appear somewhere in the
    feature-tour source, so the gallery can never silently lag the API."""
    src = (ROOT / "exams" / "demo-features.typ").read_text()
    for marker in ("#m(", "#blank", "#answer", "#explain", "#opts", "#qid",
                   "#section(shuffle: false)", "✓", "None of the above",
                   "answer(none)", "compact: true", "columns: 2", "footer:"):
        assert marker in src, f"feature tour is missing {marker}"
