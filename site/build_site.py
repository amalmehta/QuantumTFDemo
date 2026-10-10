"""Build the Quantum TF Demo website into site/public/.

    python3 site/build_site.py                       # site/public/*.html + assets
    python3 site/build_site.py --fragment OUT.html   # also the home page without <html>/<head>,
                                                     # for hosts that add their own (claude.ai)

Inputs (nothing is typed in by hand):
  results/*.json                      experiment results -> charts, tables, numbers in the prose
  paper/arxiv/generated/values.tex    the paper's \\val macros -> same numbers the PDF uses
  paper/arxiv/sections/*.tex          the paper -> paper.html (LaTeX subset converted here)
  paper/arxiv/refs.bib                references
  quantumtf_demo/**/*.py              code excerpts, pulled by function name
Standard library only.
"""
import argparse
import ast
import datetime
import html
import io
import json
import keyword
import re
import shutil
import tokenize
from pathlib import Path

SITE = Path(__file__).resolve().parent
ROOT = SITE.parent
SRC, OUT = SITE / "src", SITE / "public"
PAPER = ROOT / "paper" / "arxiv"
MATHJAX = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg-full.min.js"
FONTS = ("https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,500;0,600;1,500"
         "&family=Public+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap")
AUTHOR = "Amal Mehta"

NAV = [("index", "Home"), ("mnist", "QNN vs classical"), ("hybrid", "Hybrid"),
       ("barren", "Barren plateaus"), ("noise", "Noise"), ("paper", "Paper"),
       ("run", "Run it"), ("about", "About")]
EXPERIMENTS = ["mnist", "hybrid", "barren", "noise"]


# ------------------------------------------------------------------ data
def load_results():
    data = {}
    for name in ("data_stats", "mnist_qnn", "barren_plateaus", "noise"):
        p = ROOT / "results" / f"{name}.json"
        data[name] = json.loads(p.read_text()) if p.exists() else None
    return data


def load_values():
    text = (PAPER / "generated" / "values.tex").read_text()
    return {m.group(1): m.group(2) for m in re.finditer(r"\\newcommand\{\\val(\w+)\}\{(.*)\}", text)}


def pct(x):
    return f"{100 * x:.1f}%"


def sci(x):
    m, e = f"{x:.1e}".split("e")
    return f"{m}×10<sup>{int(e)}</sup>"


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


# ------------------------------------------------------------------ code excerpts
def excerpt(rel, name):
    """Source of function `name` in `rel`, syntax-highlighted, with real line numbers."""
    path = ROOT / rel
    src = path.read_text()
    node = next(n for n in ast.walk(ast.parse(src))
                if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name)
    lines = src.splitlines()[node.lineno - 1: node.end_lineno]
    body = highlight("\n".join(lines) + "\n").rstrip("\n").split("\n")
    numbered = "\n".join(f'<span class="ln">{node.lineno + i}</span>{line}' for i, line in enumerate(body))
    return (f'<figure class="code"><figcaption>{rel} · {name}() · lines {node.lineno}–{node.end_lineno}</figcaption>'
            f"<pre><code>{numbered}</code></pre></figure>")


def highlight(src):
    out, pos = [], 0
    line_starts = [0]
    for line in src.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))
    off = lambda rc: line_starts[rc[0] - 1] + rc[1]  # noqa: E731
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.ENDMARKER:
            break
        a, b = off(tok.start), off(tok.end)
        out.append(html.escape(src[pos:a]))
        text = html.escape(src[a:b])
        if tok.type == tokenize.COMMENT:
            text = f'<span class="com">{text}</span>'
        elif tok.type == tokenize.STRING:
            text = f'<span class="str">{text}</span>'
        elif tok.type == tokenize.NAME and keyword.iskeyword(tok.string):
            text = f'<span class="kw">{text}</span>'
        out.append(text)
        pos = b
    out.append(html.escape(src[pos:]))
    return "".join(out)


# ------------------------------------------------------------------ bibliography
def parse_bib():
    text = (PAPER / "refs.bib").read_text()
    entries = {}
    for m in re.finditer(r"@\w+\{(\w+),(.*?)\n\}", text, re.S):
        fields = {k.lower(): v for k, v in re.findall(r"(\w+)\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}", m.group(2))}
        entries[m.group(1)] = fields
    return entries


def detex(s):
    for a, b in ((r"{\'\i}", "í"), (r"{\'e}", "é"), (r"\'\i", "í"), (r"\'e", "é")):
        s = s.replace(a, b)
    return re.sub(r"[{}]", "", s)


def authors(f):
    names = [detex(a).strip() for a in f["author"].split(" and ")]
    return [("et al." if n == "others" else n) for n in names]


def surname(name):
    return name.split(",")[0].strip() if "," in name else name.split()[-1]


def short_cite(f):
    a = authors(f)
    if len(a) == 2 and a[1] != "et al.":
        return f"{surname(a[0])} and {surname(a[1])}"
    return surname(a[0]) + (" et al." if len(a) > 1 else "")


def ref_order(bib):
    # plainnat: sorted by first author's surname, then year (matches the PDF's numbering)
    keys = sorted(bib, key=lambda k: (surname(authors(bib[k])[0]).lower(), bib[k].get("year", "")))
    return {k: i + 1 for i, k in enumerate(keys)}


def references_html(bib, order):
    items = []
    for k, n in sorted(order.items(), key=lambda kv: kv[1]):
        f = bib[k]
        a = authors(f)
        names = ", ".join(a[:-1]) + (" " if a[-1] == "et al." else ", and ") + a[-1] if len(a) > 1 else a[0]
        venue = detex(f.get("journal", ""))
        if f.get("volume"):
            venue += f" {f['volume']}"
        if f.get("pages"):
            venue += f", {f['pages'].replace('--', '–')}"
        link = (f'<a href="https://doi.org/{f["doi"]}">doi:{f["doi"]}</a>' if f.get("doi") else "")
        if f.get("eprint"):
            link += ("; " if link else "") + f'<a href="https://arxiv.org/abs/{f["eprint"]}">arXiv:{f["eprint"]}</a>'
        items.append(f'<li id="ref-{k}" value="{n}">{html.escape(names)} ({f.get("year", "")}). '
                     f'{html.escape(detex(f["title"]))}. <em>{html.escape(venue)}</em>. {link}</li>')
    return '<ol class="refs">' + "\n".join(items) + "</ol>"


# ------------------------------------------------------------------ LaTeX -> HTML (the subset the paper uses)
FIG_CHART = {"mnist_qnn": "mnist", "hybrid": "hybrid", "barren_plateaus": "barren", "noise": "noise"}


def strip_comments(tex):
    return re.sub(r"(?<!\\)%.*", "", tex)


def braced(s, i):
    """Return (content, end) for the {...} group starting at s[i] == '{'."""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
    raise ValueError("unbalanced braces")


def replace_cmd(s, cmd, fn):
    """Replace every \\cmd{arg} (balanced) with fn(arg)."""
    out, i, pat = [], 0, "\\" + cmd + "{"
    while True:
        j = s.find(pat, i)
        if j < 0:
            return "".join(out) + s[i:]
        arg, end = braced(s, j + len(pat) - 1)
        out.append(s[i:j]); out.append(fn(arg)); i = end


def tabular_html(tex):
    body = re.search(r"\\begin\{tabular\}\{[^}]*\}(.*)\\end\{tabular\}", tex, re.S).group(1)
    rows = [r.strip() for r in body.split("\\\\")]
    head, rows_out, seen_mid = None, [], False
    for r in rows:
        r = r.replace("\\toprule", "").replace("\\bottomrule", "").strip()
        if "\\midrule" in r:
            seen_mid = True
            r = r.replace("\\midrule", "").strip()
        if not r:
            continue
        cells = [inline(c.strip()) for c in r.split("&")]
        if head is None and not seen_mid:
            head = cells
        else:
            rows_out.append(cells)
    th = "".join(f"<th>{c}</th>" for c in head)
    tb = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows_out)
    return f'<div class="table-wrap"><table class="data"><thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table></div>'


CTX = {}  # labels, citation order, bib: filled by paper_html()


def inline(s):
    """Inline LaTeX -> HTML. Math ($...$) is set aside, then restored for MathJax."""
    maths = []

    def stash(m):
        maths.append(html.escape(m.group(0), quote=False))
        return f"\x00{len(maths) - 1}\x00"
    t = re.sub(r"\$[^$]*\$", stash, s)
    t = html.escape(t, quote=False)
    t = t.replace("-{}-", "&#45;&#45;").replace("---", "—").replace("--", "–")
    t = t.replace("``", "“").replace("''", "”").replace("~", "&nbsp;").replace("\\S", "§")
    t = t.replace("\\_", "_").replace("\\,", "&thinsp;").replace("\\%", "%").replace("\\&", "&amp;")
    t = replace_cmd(t, "emph", lambda a: f"<em>{a}</em>")
    t = replace_cmd(t, "textbf", lambda a: f"<strong>{a}</strong>")
    t = replace_cmd(t, "texttt", lambda a: f"<code>{a}</code>")
    t = replace_cmd(t, "TODO", lambda a: f'<span class="todo">[To do: {a}]</span>')
    t = replace_cmd(t, "label", lambda a: "")
    t = replace_cmd(t, "ref", lambda a: ref_link(a))
    t = replace_cmd(t, "citep", lambda a: cite(a, paren=True))
    t = replace_cmd(t, "citet", lambda a: cite(a, paren=False))
    t = replace_cmd(t, "cite", lambda a: cite(a, paren=True))
    t = t.replace("{,}", ",").replace("{}", "")
    return re.sub(r"\x00(\d+)\x00", lambda m: maths[int(m.group(1))], t)


def ref_link(label):
    num = CTX["labels"].get(label, "?")
    return f'<a href="#{anchor(label)}">{num}</a>'


def anchor(label):
    return label.replace(":", "-")


def cite(keys, paren):
    links = []
    for k in [k.strip() for k in keys.split(",")]:
        n = CTX["order"][k]
        a = f'<a href="#ref-{k}">{n}</a>'
        links.append(a if paren else f"{html.escape(short_cite(CTX['bib'][k]))} [{a}]")
    return f"[{', '.join(links)}]" if paren else ", ".join(links)


def collect_labels(texts):
    """Number sections, subsections, figures and tables in reading order, as LaTeX does."""
    labels, sec, sub, fig, tab = {}, 0, 0, 0, 0
    for tex in texts:
        for m in re.finditer(r"\\(section|subsection)\{.*?\}\s*\\label\{([^}]+)\}|\\begin\{(figure|table)\}(.*?)\\end\{\3\}", tex, re.S):
            if m.group(1) == "section":
                sec += 1; sub = 0; labels[m.group(2)] = str(sec)
            elif m.group(1) == "subsection":
                sub += 1; labels[m.group(2)] = f"{sec}.{sub}"
            else:
                lab = re.search(r"\\label\{([^}]+)\}", m.group(4))
                if m.group(3) == "figure":
                    fig += 1; n = fig
                else:
                    tab += 1; n = tab
                if lab:
                    labels[lab.group(1)] = str(n)
    return labels


def float_html(kind, body):
    lab = re.search(r"\\label\{([^}]+)\}", body)
    label = lab.group(1) if lab else ""
    num = CTX["labels"].get(label, "")
    cap_start = body.find("\\caption{")
    caption, _ = braced(body, cap_start + len("\\caption"))
    name = "Figure" if kind == "figure" else "Table"
    cap = f"<figcaption><b>{name} {num}.</b> {inline(caption)}</figcaption>"
    inner = ""
    g = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{figures/([\w]+)\.pdf\}", body)
    if g:
        inner = f'<div class="chart" data-chart="{FIG_CHART[g.group(1)]}"></div>'
    elif "figures/qnn_circuit" in body:
        inner = '<div class="circuit"><svg data-circuit role="img" aria-label="QNN circuit"></svg></div>'
    t = re.search(r"\\input\{generated/tables/(\w+)\.tex\}", body)
    if t:
        inner = tabular_html((PAPER / "generated" / "tables" / f"{t.group(1)}.tex").read_text())
    parts = [cap, inner] if kind == "table" else [inner, cap]
    return f'<figure id="{anchor(label)}" class="wide">{"".join(parts)}</figure>'


def block_html(tex):
    """One section file -> HTML blocks."""
    out = []
    # floats first, replaced by placeholders so paragraph splitting leaves them intact
    floats = []

    def keep(m):
        floats.append(float_html(m.group(1), m.group(2)))
        return f"\n\n@@FLOAT{len(floats) - 1}@@\n\n"
    tex = re.sub(r"\\begin\{(figure|table)\}(?:\[[^\]]*\])?(.*?)\\end\{\1\}", keep, tex, flags=re.S)

    def itemize(m):
        items = [i.strip() for i in m.group(1).split("\\item") if i.strip()]
        return "\n\n@@HTML" + "<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>@@\n\n"
    tex = re.sub(r"\\begin\{itemize\}(.*?)\\end\{itemize\}", itemize, tex, flags=re.S)

    abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", tex, re.S)
    if abstract:
        return f'<div class="abstract"><div class="label">Abstract</div><p>{inline(" ".join(abstract.group(1).split()))}</p></div>'

    for para in re.split(r"\n\s*\n", tex):
        para = para.strip()
        if not para:
            continue
        f = re.fullmatch(r"@@FLOAT(\d+)@@", para)
        if f:
            out.append(floats[int(f.group(1))]); continue
        if para.startswith("@@HTML"):
            out.append(para[6:-2]); continue
        para = " ".join(para.split())
        m = re.match(r"\\(section\*?|subsection)\{(.*?)\}\s*(?:\\label\{([^}]+)\})?\s*(.*)", para)
        if m:
            star = m.group(1).endswith("*")
            tag = "h2" if m.group(1).startswith("section") else "h3"
            num = "" if star else CTX["labels"].get(m.group(3) or "", "")
            ident = f' id="{anchor(m.group(3))}"' if m.group(3) else ""
            out.append(f"<{tag}{ident}>{num + '&ensp;' if num else ''}{inline(m.group(2))}</{tag}>")
            para = m.group(4)
            if not para:
                continue
        p = re.match(r"\\paragraph\{(.*?)\}\s*(.*)", para)
        if p:
            out.append(f"<p><strong>{inline(p.group(1))}</strong> {inline(p.group(2))}</p>")
        else:
            out.append(f"<p>{inline(para)}</p>")
    return "\n".join(out)


def paper_html(values):
    main = (PAPER / "main.tex").read_text()
    order = re.findall(r"\\input\{sections/(\w+)\}", main)
    texts = []
    for name in order:
        t = strip_comments((PAPER / "sections" / f"{name}.tex").read_text())
        t = re.sub(r"\\val(\w+)(\{\})?", lambda m: values[m.group(1)], t)
        texts.append((name, t))
    bib = parse_bib()
    CTX.update(labels=collect_labels([t for _, t in texts]), bib=bib, order=ref_order(bib))
    title = re.search(r"\\title\{(.*?)\}\n", main, re.S).group(1).replace("\\\\", " ")
    blocks = [block_html(t) for _, t in texts]
    return title, "\n".join(blocks), references_html(bib, CTX["order"])


# ------------------------------------------------------------------ layout
def head(title, description, extra=""):
    return f"""<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="assets/style.css">
{extra}"""


def topbar(slug):
    cur = ' aria-current="page"'
    links = "".join('<a href="{}.html"{}>{}</a>'.format(s, cur if s == slug else "", label)
                    for s, label in NAV[1:])
    return f"""<header class="top"><div class="bar">
  <a class="name" href="./">Quantum TF Demo</a>
  <nav aria-label="Site">{links}</nav>
</div></header>"""


def footer(data):
    v = next((r["versions"] for r in (data["mnist_qnn"], data["noise"], data["barren_plateaus"]) if r), None)
    built = datetime.date.today().isoformat()
    ver = f"TensorFlow {v['tensorflow']} · TensorFlow Quantum {v['tensorflow_quantum']} · Cirq {v['cirq']}" if v else ""
    return f"""<footer class="site"><span>{AUTHOR}, independent researcher</span><span>{ver}</span>
<span>Built {built} from results/*.json</span></footer>"""


def pager(slug):
    i = EXPERIMENTS.index(slug)
    labels = dict(NAV)
    prev = (f'<a href="{EXPERIMENTS[i - 1]}.html"><span>Previous</span>{labels[EXPERIMENTS[i - 1]]}</a>' if i > 0
            else '<a href="./"><span>Back to</span>Home</a>')
    nxt = (f'<a class="next" href="{EXPERIMENTS[i + 1]}.html"><span>Next</span>{labels[EXPERIMENTS[i + 1]]}</a>'
           if i < len(EXPERIMENTS) - 1 else '<a class="next" href="paper.html"><span>Next</span>The paper</a>')
    return f'<nav class="pager" aria-label="Experiments">{prev}{nxt}</nav>'


def page(slug, title, description, body, data, extra_head="", extra_scripts=""):
    """Returns (full_document, fragment). The fragment omits <html>/<head>/<body>."""
    h = head(title, description, extra_head)
    content = f"""{topbar(slug)}
<main class="frame">
{body}
{footer(data)}
</main>
<script src="assets/data.js"></script>
<script src="assets/site.js"></script>
{extra_scripts}"""
    full = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{h}
</head>
<body>
{content}
</body>
</html>
"""
    return full, h + "\n" + content


# ------------------------------------------------------------------ pages
def page_index(data, V, abstract_html):
    m, b, z = data["mnist_qnn"], data["barren_plateaus"], data["noise"]
    q8 = next(r for r in b["by_qubits"] if r["n_qubits"] == 8)
    zp = sorted(z["summary"]["eval_only"], key=float)
    cards = [
        ("mnist", "Experiment 1", "QNN vs classical", f"{pct(m['summary']['qnn']['mean'])} <small>vs {pct(m['summary']['classical']['mean'])}</small>",
         f"A 32-angle quantum circuit against a {m['runs']['classical'][0]['params']}-weight classical network on the same pixels. The classical one wins."),
        ("hybrid", "Experiment 2", "Hybrid head", f"+{V['HybridGain']} <small>points</small>",
         "Reading out every qubit into a small dense layer lifts the QNN to the classical score."),
        ("barren", "Experiment 3", "Barren plateaus", f"÷{V['BpRatioEight']} <small>from 2 to 8 qubits</small>",
         f"Gradients in random circuits shrink as circuits widen, then flatten in this sweep at {b['by_qubits'][0]['depth']} layers."),
        ("noise", "Experiment 4", "Depolarizing noise", f"{pct(z['summary']['eval_only'][zp[0]]['mean'])} → {pct(z['summary']['eval_only'][zp[-1]]['mean'])}",
         f"A trained 17-qubit model falls to chance at p = {zp[-1]} noise per moment."),
    ]
    card_html = "".join(f"""<a class="card" href="{s}.html"><div class="label">{lab}</div><h3>{t}</h3>
<div class="num">{num}</div><p>{txt}</p><span class="go">See the experiment →</span></a>""" for s, lab, t, num, txt in cards)
    ceil = data["data_stats"]["by_size"][1]["lookup_ceiling"]
    return f"""
<header class="page-head">
  <div class="label">TensorFlow Quantum · training experiments</div>
  <h1>Training a quantum neural network on handwritten digits, and where it struggles</h1>
  <p class="lede">A small, reproducible study by {AUTHOR}. A 17-qubit circuit learns to tell a 3 from a 6. We compare it with a classical network of the same size, add a classical head, measure how gradients vanish as circuits grow, and test it under simulated hardware noise.</p>
</header>
<figure class="circuit">
  <svg data-circuit role="img" aria-label="QNN circuit: data qubits each couple to a readout qubit through XX and ZZ gates, then the readout is measured in Z"></svg>
  <figcaption>The model (Farhi &amp; Neven, 2018). Each white pixel flips its data qubit to <span class="ket">|1⟩</span>. Every data qubit then couples to the readout qubit through one trainable <span class="ket">XX<sup>θ</sup></span> gate and one <span class="ket">ZZ<sup>φ</sup></span> gate. The prediction is <span class="ket">⟨Z⟩</span> on the readout. Four of the 16 data wires are drawn.</figcaption>
</figure>
<div class="facts" style="padding-block:1.5rem 0">
  <div><b>17</b><span>qubits in the main model</span></div>
  <div><b>32</b><span>trainable angles</span></div>
  <div><b>4×4</b><span>pixels per digit</span></div>
  <div><b>{len(m['config']['seeds'])}</b><span>seeds per experiment</span></div>
  <div><b>{pct(ceil)}</b><span>best possible on this input</span></div>
</div>
<section class="block">
  <div class="label">Four experiments</div>
  <div class="cards">{card_html}</div>
</section>
<section class="block">
  <div class="prose">
    <div class="label">The paper</div>
    <h2>{html.escape(V.get('_title', 'Training Quantum Neural Networks with TensorFlow Quantum'))}</h2>
    {abstract_html}
    <p><a href="paper.html">Read the paper on the web</a> · <a href="paper.pdf">PDF</a> · <a href="run.html">Reproduce every number</a></p>
  </div>
</section>"""


def seed_table_mnist(m):
    rows = ""
    for i, seed in enumerate(m["config"]["seeds"]):
        r = {k: m["runs"][k][i] for k in ("qnn", "hybrid", "classical")}
        rows += (f"<tr><td>{seed}</td><td>{r['qnn']['test_acc']:.3f}</td><td>{r['hybrid']['test_acc']:.3f}</td>"
                 f"<td>{r['classical']['test_acc']:.3f}</td><td>{r['qnn']['train_seconds']:.0f}</td>"
                 f"<td>{r['hybrid']['train_seconds']:.0f}</td><td>{r['classical']['train_seconds']:.0f}</td></tr>")
    s = m["summary"]
    rows += (f"<tr><td><strong>mean ± std</strong></td>" + "".join(
        f"<td><strong>{s[k]['mean']:.3f} ± {s[k]['std']:.3f}</strong></td>" for k in ("qnn", "hybrid", "classical"))
        + "<td></td><td></td><td></td></tr>")
    return f"""<div class="table-wrap"><table class="data"><thead><tr><th>Seed</th><th>QNN</th><th>Hybrid</th><th>Classical</th>
<th>QNN (s)</th><th>Hybrid (s)</th><th>Classical (s)</th></tr></thead><tbody>{rows}</tbody></table></div>
<p class="muted" style="font-size:var(--step--1)">Test accuracy per seed, and wall-clock training seconds. Times varied with machine load.</p>"""


def method_mnist(m, ds):
    d4 = next(r for r in ds["by_size"] if r["size"] == 4)
    return f"""<ol class="steps">
<li><div><strong>Keep two digits.</strong> MNIST 3s and 6s only ({d4['n_test']:,} test images).</div></li>
<li><div><strong>Shrink to 4×4.</strong> Bilinear resize, then drop training images whose small version appears with both labels, leaving {d4['n_train']:,}. This happens before binarising, as in the TFQ tutorial.</div></li>
<li><div><strong>Binarise.</strong> Pixels above 0.5 become 1. Only {d4['unique_train_patterns']} distinct patterns remain, so a lookup table over them is the best any model can do: {pct(d4['lookup_ceiling'])} on the test set.</div></li>
<li><div><strong>Encode.</strong> Each lit pixel becomes an <code>X</code> gate on its qubit, giving a basis state of 16 qubits.</div></li>
<li><div><strong>Train.</strong> Each seed draws {m['config']['n_train']:,} training and {m['config']['n_test']} test images. Hinge loss on ±1 labels, Adam (learning rate {m['config']['lr']}, batch {m['config']['batch_size']}), {m['config']['epochs']} epochs, exact simulation with adjoint gradients.</div></li>
</ol>"""


def page_mnist(data, V):
    m, ds = data["mnist_qnn"], data["data_stats"]
    q, c = m["summary"]["qnn"], m["summary"]["classical"]
    return f"""
<header class="page-head">
  <div class="label">Experiment 1 of 4</div>
  <h1>QNN vs a classical network of the same size</h1>
  <p class="q">Can 32 trainable angles in a quantum circuit match {m['runs']['classical'][0]['params']} classical weights on the same pixels?</p>
  <p class="lede">Not quite. The QNN reaches {pct(q['mean'])} test accuracy and the classical network {pct(c['mean'])}, close to the {pct(V and float(V['CeilFour']))} ceiling that the 4×4 input allows.</p>
</header>
<section class="block">
  <div class="label">Results</div>
  <div class="result"><div class="chart" data-chart="mnist" data-seeds></div><div class="numbers" data-numbers="mnist"></div></div>
  <p class="prose">The classical network is behind after the first epoch, then pulls ahead and stays there with much less spread across seeds. The QNN's loss barely moves after epoch 2. Shaded bands show ±1 standard deviation over {q['n']} seeds; tick "Show each seed" to see the individual runs.</p>
  {seed_table_mnist(m)}
</section>
<section class="block"><div class="label">Method</div>{method_mnist(m, ds)}</section>
<section class="block">
  <div class="label">The code that ran it</div>
  {excerpt('quantumtf_demo/models.py', 'qnn_circuit')}
  <details class="code"><summary>Show the classical baseline and the data pipeline</summary><div class="stack">
  {excerpt('quantumtf_demo/models.py', 'build_classical')}
  {excerpt('quantumtf_demo/data.py', 'load_binary_mnist')}
  {excerpt('quantumtf_demo/data.py', 'encode_image')}
  </div></details>
</section>
<section class="block">
  <div class="label">Caveats</div>
  <ul class="caveats">
    <li>Exact simulation on a CPU: the QNN's training time says nothing about quantum hardware.</li>
    <li>{q['n']} seeds and two hyperparameter settings tried on seed 0. Treat differences of a point or two with care.</li>
    <li>The input is so coarse that every model is capped near {pct(float(V['CeilFour']))}. This task can't show a quantum advantage.</li>
  </ul>
  <p><a href="paper.html#sec-res-mnist">Read §{V['_labels']['sec:res-mnist']} in the paper</a></p>
</section>
{pager('mnist')}"""


def page_hybrid(data, V):
    m = data["mnist_qnn"]
    q, h = m["summary"]["qnn"], m["summary"]["hybrid"]
    return f"""
<header class="page-head">
  <div class="label">Experiment 2 of 4</div>
  <h1>Quantum readout vs a classical head</h1>
  <p class="q">Does reading out every qubit and adding a small dense layer help the same circuit?</p>
  <p class="lede">Yes. The same circuit with an 8-unit dense head reaches {pct(h['mean'])}, up {V['HybridGain']} points from the single-readout QNN's {pct(q['mean'])}, and matches the classical network.</p>
</header>
<section class="block">
  <div class="label">Results</div>
  <div class="result"><div class="chart" data-chart="hybrid" data-seeds></div><div class="numbers" data-numbers="hybrid"></div></div>
  <p class="prose">The hybrid model is ahead from the first epoch, and its spread across seeds is about a quarter of the QNN's (±{100 * h['std']:.1f} vs ±{100 * q['std']:.1f} points). Same data splits, seeds and circuit as Experiment 1.</p>
</section>
<section class="block"><div class="label">Method</div>
<ol class="steps">
<li><div><strong>Same circuit.</strong> The 17-qubit Farhi–Neven circuit with its 32 trainable angles.</div></li>
<li><div><strong>Read out every qubit.</strong> ⟨Z⟩ on all 17 qubits instead of only the readout qubit.</div></li>
<li><div><strong>Classical head.</strong> Those 17 values feed Dense(8, ReLU) → Dense(1, tanh): {m['runs']['hybrid'][0]['params'] - 32} classical parameters on top of the 32 quantum ones.</div></li>
<li><div><strong>Train jointly.</strong> Same loss, optimizer, data and seeds as Experiment 1. Gradients flow through the head into the circuit.</div></li>
</ol></section>
<section class="block">
  <div class="label">The code that ran it</div>
  {excerpt('quantumtf_demo/models.py', 'build_hybrid')}
  <details class="code"><summary>Show the experiment loop shared with Experiment 1</summary>
  {excerpt('quantumtf_demo/experiments/mnist_qnn.py', 'run')}</details>
</section>
<section class="block">
  <div class="label">Caveats</div>
  <ul class="caveats">
    <li>The gain can't be credited to the circuit alone: the hybrid has {m['runs']['hybrid'][0]['params']} parameters, most of them classical.</li>
    <li>16 of the 17 readouts are on data qubits, which start in the input's basis state, so the head sees something close to the pixels.</li>
  </ul>
  <p><a href="paper.html#sec-res-hybrid">Read §{V['_labels']['sec:res-hybrid']} in the paper</a></p>
</section>
{pager('hybrid')}"""


def page_barren(data, V):
    b = data["barren_plateaus"]
    q, d = b["by_qubits"], b["by_depth"]
    rows_q = "".join(f"<tr><td>{r['n_qubits']}</td><td>{sci(r['variance'])}</td></tr>" for r in q)
    rows_d = "".join(f"<tr><td>{r['depth']}</td><td>{sci(r['variance'])}</td></tr>" for r in d)
    return f"""
<header class="page-head">
  <div class="label">Experiment 3 of 4</div>
  <h1>Barren plateaus</h1>
  <p class="q">How fast do gradients vanish as random circuits get wider and deeper?</p>
  <p class="lede">The gradient variance drops {V['BpRatioEight']}-fold from 2 to 8 qubits, then stops falling in this sweep. At 8 qubits it is still dropping at {d[-1]['depth']} layers, which suggests the wider circuits weren't deep enough to behave fully randomly.</p>
</header>
<section class="block">
  <div class="label">Results</div>
  <div class="result"><div class="chart" data-chart="barren"></div><div class="numbers" data-numbers="barren"></div></div>
  <p class="prose">Each point is the variance of ∂⟨Z₀Z₁⟩/∂θ₀ over {b['config']['n_circuits']} random circuits with random angles. The dashed line is a log-linear fit over all six widths (decay factor {V['BpDecay']} per qubit). It describes the trend only loosely, because the points flatten after 8 qubits.</p>
  <div class="cards" style="grid-template-columns:repeat(auto-fit,minmax(14rem,1fr))">
    <div class="table-wrap"><table class="data"><thead><tr><th>Qubits ({q[0]['depth']} layers)</th><th>Variance</th></tr></thead><tbody>{rows_q}</tbody></table></div>
    <div class="table-wrap"><table class="data"><thead><tr><th>Layers ({d[0]['n_qubits']} qubits)</th><th>Variance</th></tr></thead><tbody>{rows_d}</tbody></table></div>
  </div>
</section>
<section class="block"><div class="label">Method</div>
<ol class="steps">
<li><div><strong>Random circuit.</strong> R<sub>y</sub>(π/4) on every qubit, then each layer applies a randomly chosen R<sub>x</sub>, R<sub>y</sub> or R<sub>z</sub> to every qubit, followed by a ladder of CZ gates (McClean et al., 2018).</div></li>
<li><div><strong>Random angles.</strong> Every angle uniform in [0, 2π).</div></li>
<li><div><strong>Gradient.</strong> d⟨Z₀Z₁⟩/dθ₀ for the first angle, by the adjoint method (exact).</div></li>
<li><div><strong>Variance.</strong> Over {b['config']['n_circuits']} circuits, at {q[0]['n_qubits']}–{q[-1]['n_qubits']} qubits (at {q[0]['depth']} layers) and {d[0]['depth']}–{d[-1]['depth']} layers (at {d[0]['n_qubits']} qubits).</div></li>
</ol></section>
<section class="block">
  <div class="label">The code that ran it</div>
  {excerpt('quantumtf_demo/experiments/barren_plateaus.py', 'random_circuit')}
  {excerpt('quantumtf_demo/experiments/barren_plateaus.py', 'grad_variance')}
</section>
<section class="block">
  <div class="label">Caveats</div>
  <ul class="caveats">
    <li>The "too shallow" explanation for the flattening is an interpretation. A deeper sweep at 10–12 qubits would test it; we didn't run one.</li>
    <li>{b['config']['n_circuits']} circuits per point. Variance estimates from heavy-tailed gradients are themselves noisy.</li>
  </ul>
  <p><a href="paper.html#sec-res-barren">Read §{V['_labels']['sec:res-barren']} in the paper</a></p>
</section>
{pager('barren')}"""


def page_noise(data, V):
    z = data["noise"]
    ps = sorted(z["summary"]["eval_only"], key=float)
    rows = "".join(
        f"<tr><td>{p}</td><td>{z['summary']['eval_only'][p]['mean']:.3f} ± {z['summary']['eval_only'][p]['std']:.3f}</td>"
        f"<td>{z['summary']['trained_noisy'][p]['mean']:.3f} ± {z['summary']['trained_noisy'][p]['std']:.3f}</td></tr>" for p in ps)
    k = z["config"]["size"]
    return f"""
<header class="page-head">
  <div class="label">Experiment 4 of 4</div>
  <h1>Training under depolarizing noise</h1>
  <p class="q">How much accuracy does hardware-like noise cost a trained model, and can a model still learn with the noise present?</p>
  <p class="lede">A trained 17-qubit QNN goes from {pct(z['summary']['eval_only'][ps[0]]['mean'])} to {pct(float(V['NoiseEvMid']))} at p = 0.01, and to chance ({pct(z['summary']['eval_only'][ps[-1]]['mean'])}) at p = {ps[-1]}. Smaller {k}×{k} models trained with the noise present still learn, but that comparison is confounded.</p>
</header>
<section class="block">
  <div class="label">Results</div>
  <div class="result"><div class="chart" data-chart="noise" data-seeds></div><div class="numbers" data-numbers="noise"></div></div>
  <p class="prose">Blue: the {len(z['config']['seeds'])} trained models from Experiment 1, tested under noise. Orange: {k}×{k} models ({k * k + 1} qubits) trained and tested with the noise present. The orange curve is flatter, but its circuit has {2 * k * k} noisy couplings instead of 32, so it collects less noise whether or not it's trained with it. Error bars are ±1 standard deviation over seeds.</p>
  <div class="table-wrap"><table class="data"><thead><tr><th>p</th><th>4×4, trained clean, tested noisy</th><th>{k}×{k}, trained and tested noisy</th></tr></thead><tbody>{rows}</tbody></table></div>
</section>
<section class="block"><div class="label">Method</div>
<ol class="steps">
<li><div><strong>Noise channel.</strong> A single-qubit depolarizing channel with probability p after every moment of the model circuit (<code>circuit.with_noise</code>).</div></li>
<li><div><strong>Trajectories.</strong> Each expectation averages {z['config']['repetitions']} quantum trajectories (<code>tfq.layers.NoisyPQC</code>).</div></li>
<li><div><strong>Noisy evaluation, 4×4.</strong> The angles saved by Experiment 1, loaded into a noisy model, tested on {z['config']['eval_n_test']} images per seed.</div></li>
<li><div><strong>Noisy training, {k}×{k}.</strong> Parameter-shift gradients through noisy trajectories cost about 65 noisy circuits per image, which was too slow at 17 qubits (about 400 s per 64 images per epoch in a test run). So these models use {k}×{k} images: {z['config']['n_train']} training and {z['config']['n_test']} test images, {z['config']['epochs']} epochs, batch {z['config']['batch_size']}, learning rate {z['config']['lr']}.</div></li>
</ol></section>
<section class="block">
  <div class="label">The code that ran it</div>
  {excerpt('quantumtf_demo/models.py', 'build_qnn')}
  <details class="code"><summary>Show the experiment loop</summary>
  {excerpt('quantumtf_demo/experiments/noise.py', 'run')}</details>
</section>
<section class="block">
  <div class="label">Caveats</div>
  <ul class="caveats">
    <li>The two curves are different models. Don't read the gap between them as a benefit of noise-aware training.</li>
    <li>Every noisy estimate carries trajectory-sampling error on top of the channel itself ({z['config']['repetitions']} trajectories).</li>
    <li>The {k}×{k} input caps any model at {pct(next(r for r in data['data_stats']['by_size'] if r['size'] == k)['lookup_ceiling'])}.</li>
  </ul>
  <p><a href="paper.html#sec-res-noise">Read §{V['_labels']['sec:res-noise']} in the paper</a></p>
</section>
{pager('noise')}"""


def page_paper(title, body, refs):
    bib = f"""@misc{{mehta2026quantumtf,
  title  = {{{title}}},
  author = {{{AUTHOR}}},
  year   = {{2026}},
  note   = {{Preprint}}
}}"""
    return f"""
<header class="page-head">
  <div class="label">Paper · preprint</div>
  <h1>{html.escape(title)}</h1>
  <div class="paper-meta"><span>{AUTHOR}, independent researcher</span><span>2026</span><a href="paper.pdf">PDF version</a></div>
</header>
<article class="paper">
{body}
<h2 id="references">References</h2>
{refs}
<h2 id="cite">Cite this</h2>
<div class="cmd"><code>{html.escape(bib)}</code><button type="button" data-copy>Copy</button></div>
</article>"""


def cmd(text):
    return f'<div class="cmd"><code>{html.escape(text)}</code><button type="button" data-copy>Copy</button></div>'


def page_run():
    return f"""
<header class="page-head">
  <div class="label">Run it yourself</div>
  <h1>Reproduce every number</h1>
  <p class="lede">Everything runs on a laptop CPU in Docker. One command reruns all four experiments; two more rebuild the paper and this site from the new results.</p>
</header>
<section class="block"><div class="prose">
  <h2>1. Build the environment</h2>
  <p>The image uses TensorFlow Quantum 0.7.6 with TensorFlow 2.18 on Linux and works on any Mac or PC with Docker. It's about 3 GB.</p>
  {cmd('docker build -t quantumtfdemo .')}
  <p class="muted">There is also a native route for Intel Macs (TFQ 0.7.2, the last macOS release). It needs a few workarounds, which are listed in <code>docs/INSTRUCTIONS.md</code>.</p>
</div></section>
<section class="block"><div class="prose">
  <h2>2. Check it works</h2>
  <p>Ten tests, about a minute:</p>
  {cmd('docker run --rm -v "$PWD":/work quantumtfdemo python -m pytest -q tests')}
  <p>Every experiment at tiny sizes, about ten minutes:</p>
  {cmd('docker run --rm -v "$PWD":/work quantumtfdemo python -m quantumtf_demo.run_all --preset quick')}
</div></section>
<section class="block"><div class="prose">
  <h2>3. Run the full experiments</h2>
  <p>A few hours on an 8-core laptop. Results land in <code>results/</code>: every seed, every epoch, the configuration and the library versions.</p>
  {cmd('docker run --rm -v "$PWD":/work quantumtfdemo python -m quantumtf_demo.run_all --preset full')}
  <p class="muted">Run a single experiment with <code>--only mnist_qnn</code>, <code>barren_plateaus</code> or <code>noise</code>. The noise experiment reuses the weights saved by <code>mnist_qnn</code>.</p>
</div></section>
<section class="block"><div class="prose">
  <h2>4. Rebuild the paper and this site</h2>
  {cmd('python paper/figures_scripts/make_all.py paper/arxiv')}
  {cmd('cd paper/arxiv && tectonic main.tex')}
  {cmd('python3 site/build_site.py')}
  <p class="muted">Every number in the paper is a generated macro, and <code>paper/arxiv/sources.md</code> records where each one comes from. This site reads the same results and the same macros.</p>
</div></section>
<section class="block">
  <div class="label">What's in the repo</div>
  <div class="filelist">
    <div><code>quantumtf_demo/</code><span>Data encoding, models and the four experiments.</span></div>
    <div><code>notebooks/Quantum TF Demo.ipynb</code><span>Guided walkthrough at small sizes, a few minutes end to end.</span></div>
    <div><code>results/*.json</code><span>Raw results from the full runs.</span></div>
    <div><code>paper/arxiv/</code><span>The paper's LaTeX, generated values, figures and checks.</span></div>
    <div><code>site/</code><span>This website: sources in <code>src/</code>, output in <code>public/</code>.</span></div>
    <div><code>docs/</code><span>Instructions, system design and file structure.</span></div>
  </div>
</section>"""


def page_about(data):
    v = data["mnist_qnn"]["versions"]
    return f"""
<header class="page-head">
  <div class="label">About</div>
  <h1>About this project</h1>
</header>
<section class="block"><div class="prose">
  <h2>Author</h2>
  <p>{AUTHOR}, independent researcher.</p>
</div></section>
<section class="block"><div class="prose">
  <h2>What this is</h2>
  <p>A small, reproducible study of training quantum neural networks with TensorFlow Quantum. It reproduces known behaviour (a strong classical baseline, the effect of a classical head, barren plateaus and noise) with current open-source tools, error bars over seeds, and code that regenerates every number. None of the findings are new; the aim is to make them easy to see, rerun and extend.</p>
</div></section>
<section class="block"><div class="prose">
  <h2>How it was made</h2>
  <p>An AI assistant (Claude) wrote the experiment code, ran the experiments, generated the figure and table scripts, drafted the paper and this site, and checked the references against arXiv and Crossref. The author chose the scope and the experiments.</p>
</div></section>
<section class="block"><div class="prose">
  <h2>Built with</h2>
  <p>TensorFlow Quantum {v['tensorflow_quantum']}, TensorFlow {v['tensorflow']} and Cirq {v['cirq']}, simulated on CPU in Docker. Data: MNIST (LeCun et al., 1998). The model follows Farhi &amp; Neven (2018); the barren-plateau setup follows McClean et al. (2018). <a href="paper.html#references">Full references</a>.</p>
</div></section>"""


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragment", type=Path, help="also write the home page without <html>/<head> here")
    args = ap.parse_args()

    data = load_results()
    V = load_values()
    title, paper_body, refs = paper_html(V)
    V["_title"] = title
    V["_labels"] = CTX["labels"]
    abstract = re.search(r'<div class="abstract">.*?<p>(.*?)</p></div>', paper_body, re.S).group(1)

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    shutil.copyfile(SRC / "style.css", OUT / "assets" / "style.css")
    shutil.copyfile(SRC / "site.js", OUT / "assets" / "site.js")
    payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    (OUT / "assets" / "data.js").write_text(f"window.QTF_DATA={payload};\n")
    pdf = PAPER / "main.pdf"
    if pdf.exists():
        shutil.copyfile(pdf, OUT / "paper.pdf")

    mathjax = (f"""<script>window.MathJax = {{ tex: {{ inlineMath: [["$", "$"]], macros: {{ ket: ["\\\\lvert #1\\\\rangle", 1] }} }},
  svg: {{ fontCache: "global" }} }};</script>
<script src="{MATHJAX}" defer></script>""")
    desc = "A reproducible TensorFlow Quantum study: a 17-qubit QNN on MNIST digits, a classical baseline, a hybrid head, barren plateaus and noise."
    pages = {
        "index": ("Quantum TF Demo", desc, page_index(data, V, f"<p>{abstract}</p>"), ""),
        "mnist": ("QNN vs Classical · Quantum TF Demo", "Experiment 1: the Farhi–Neven QNN against a classical network of the same size.", page_mnist(data, V), ""),
        "hybrid": ("Hybrid Head · Quantum TF Demo", "Experiment 2: the same circuit with a classical dense head.", page_hybrid(data, V), ""),
        "barren": ("Barren Plateaus · Quantum TF Demo", "Experiment 3: gradient variance in random circuits as width and depth grow.", page_barren(data, V), ""),
        "noise": ("Depolarizing Noise · Quantum TF Demo", "Experiment 4: QNN accuracy under depolarizing noise.", page_noise(data, V), ""),
        "paper": ("The Paper · Quantum TF Demo", title, page_paper(title, paper_body, refs), mathjax),
        "run": ("Run It · Quantum TF Demo", "How to reproduce every number in this study.", page_run(), ""),
        "about": ("About · Quantum TF Demo", "About the author and how this project was made.", page_about(data), ""),
    }
    for slug, (t, d, body, extra) in pages.items():
        full, frag = page(slug, t, d, body, data, extra_head=extra)
        (OUT / f"{slug}.html").write_text(full)
        if slug == "index" and args.fragment:
            args.fragment.write_text(frag)
    print(f"wrote {len(pages)} pages to {OUT}")


if __name__ == "__main__":
    main()
