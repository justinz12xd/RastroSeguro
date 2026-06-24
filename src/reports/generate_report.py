"""Public report generation entrypoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.reports.executive_summary import build_executive_report
from src.reports.io import load_scored_claims
from src.reports.markdown_report import render_markdown_report
from src.scoring.final_score import OUTPUT_PATH


def generate_report_dict(data_path: Path = OUTPUT_PATH, top_limit: int = 10) -> dict[str, Any]:
    return build_executive_report(load_scored_claims(data_path), top_limit=top_limit)


def generate_report_markdown(data_path: Path = OUTPUT_PATH, top_limit: int = 10) -> str:
    return render_markdown_report(generate_report_dict(data_path, top_limit=top_limit))
