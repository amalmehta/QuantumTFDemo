"""Shared setup for the paper's figure scripts: paths and the venue figure style."""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                      # project root
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import figure_style as fs                   # noqa: E402
from quantumtf_demo import figures as qf    # noqa: E402  (the plot_* functions, shared with README)

VENUE = os.environ.get("VENUE", "arxiv")
VENUE_DIR = Path(os.environ.get("VENUE_DIR", HERE.parent / "arxiv"))


def make(name, result, width="text", aspect=0.32):
    """Draw qf.PLOTS[name] from results/<result>.json at the venue width; save figures/<name>.pdf."""
    res = qf.load(result)
    if res is None:
        print(f"skip {name}: results/{result}.json missing")
        return
    fs.setup(VENUE)
    fig = qf.PLOTS[name](res, fs.size(VENUE, width, aspect))
    out = VENUE_DIR / "figures" / f"{name}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    fs.save(fig, out)
    print("wrote", out.relative_to(VENUE_DIR))
