"""Canonical filesystem paths for the RastroSeguro data layer.

Single source of truth for where the pipeline reads and writes data. Domain
modules must not hardcode these locations; they import from here (directly or
via the back-compat aliases re-exported by ``src.scoring.final_score``).
"""

from __future__ import annotations

from pathlib import Path

DATA_DIR = Path("data")
SYNTHETIC_DIR = DATA_DIR / "synthetic"
PROCESSED_DIR = DATA_DIR / "processed"

# Raw synthetic portfolio fed into the scoring pipeline.
RAW_CLAIMS_PATH = SYNTHETIC_DIR / "siniestros.csv"

# Scored portfolio: the de-facto datastore the API reads from and writes to.
SCORED_CLAIMS_PATH = PROCESSED_DIR / "siniestros_scored.csv"
