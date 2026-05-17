"""Smoke test for PDF generation."""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_generates_pdf_for_game_1(tmp_path, monkeypatch):
    """Running the script with Game 1's date should produce a non-empty PDF."""
    output = REPO_ROOT / "lineups" / "2026-05-14-lineup.pdf"
    if output.exists():
        output.unlink()
    result = subprocess.run(
        ["python", "scripts/make_lineup_pdf.py", "2026-05-14"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert output.exists(), "PDF not created"
    assert output.stat().st_size > 1000, "PDF suspiciously small"
    # PDF file magic number
    assert output.read_bytes()[:4] == b"%PDF"
