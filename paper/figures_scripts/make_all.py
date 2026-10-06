"""Regenerate every figure, table and value for one venue folder.

    python paper/figures_scripts/make_all.py paper/arxiv
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = ["make_values.py", "mnist_qnn.py", "hybrid.py", "barren_plateaus.py", "noise.py"]


def main():
    venue_dir = Path(sys.argv[1] if len(sys.argv) > 1 else HERE.parent / "arxiv").resolve()
    env = dict(os.environ, VENUE_DIR=str(venue_dir), VENUE=os.environ.get("VENUE", "arxiv"),
               SOURCE_DATE_EPOCH="0", MPLBACKEND="Agg")
    for script in SCRIPTS:
        subprocess.run([sys.executable, str(HERE / script)], cwd=HERE, env=env, check=True)


if __name__ == "__main__":
    main()
