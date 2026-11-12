"""Reference slicer files (Bambu Studio 02.08.02.61, A1 mini) — SAD §10 QG-1.

Copied verbatim from docs/features/print-file-import/example-import/; generated bad files live
only in memory (`bad_files.py`).
"""

from pathlib import Path

SLICER_DIR = Path(__file__).parent

# Project saved without slicing results (AC-12).
VTULKA_PROJECT = SLICER_DIR / "vtulka_A.3mf"
# Sliced plate export: 1 plate, PLA white 11.54 g, prediction 5 828 s (AC-01).
VTULKA_SLICED = SLICER_DIR / "vtulka_A.gcode.3mf"
# 10 plates, only plate 1 «mini christmas tree» sliced; 3 of 4 filaments used (AC-02).
LITTLE_TREES = SLICER_DIR / "LITTLE_TREES_-_multicolor.gcode.3mf"

REFERENCE_FILES = (VTULKA_PROJECT, VTULKA_SLICED, LITTLE_TREES)
