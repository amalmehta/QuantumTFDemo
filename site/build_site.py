"""Build site/index.html from site/template.html and results/*.json.

    python3 site/build_site.py                      # site/index.html (full document)
    python3 site/build_site.py --fragment OUT.html  # also a body-only copy for hosts that add <head>

Standard library only. Copies the paper PDF next to the page when it exists.
"""
import argparse
import datetime
import json
import shutil
from pathlib import Path

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent
PAPER_PDF = ROOT / "paper" / "arxiv" / "main.pdf"


HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragment", type=Path, help="also write the page without <html>/<head> here")
    args = ap.parse_args()
    data = {}
    for name in ("data_stats", "mnist_qnn", "barren_plateaus", "noise"):
        path = ROOT / "results" / f"{name}.json"
        data[name] = json.loads(path.read_text()) if path.exists() else None
    data["has_paper"] = PAPER_PDF.exists()
    if data["has_paper"]:
        shutil.copyfile(PAPER_PDF, SITE / "paper.pdf")
    data["generated"] = datetime.date.today().isoformat()
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    body = (SITE / "template.html").read_text().replace("__DATA__", payload)
    title, rest = body.split("\n", 1)  # first line is the <title>
    html = HEAD + title + "\n" + rest.replace("<div class=\"wrap\">", "</head>\n<body>\n<div class=\"wrap\">", 1) + "</body>\n</html>\n"
    (SITE / "index.html").write_text(html)
    if args.fragment:
        args.fragment.write_text(body)
    print(f"wrote {SITE / 'index.html'} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
