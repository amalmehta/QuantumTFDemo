# File structure

```
demo_with_quantumtf/
├── README.md                     # what it is, visuals, links
├── demo_with_quantumtf.md        # the project brief, decisions, changelog
├── Dockerfile                    # TFQ 0.7.6 / TF 2.18 runtime (recommended)
├── requirements-docker.txt       # pins for the Docker image
├── requirements.txt              # pins for native macOS (TFQ 0.7.2 / TF 2.7, Python 3.9)
│
├── quantumtf_demo/               # the Python package
│   ├── __init__.py               # sets TF_USE_LEGACY_KERAS / BLAS threads before TF loads
│   ├── compat.py                 # one import point for tf, keras (tf-keras or tf.keras), cirq, tfq
│   ├── data.py                   # MNIST 3-vs-6 → 4×4 → binarised → X-gate circuits
│   ├── models.py                 # QNN circuit, QNN / hybrid / classical / noisy model builders
│   ├── figures.py                # plot_* functions, shared by README PNGs and the paper PDFs
│   ├── run_all.py                # CLI: presets (quick, full), runs experiments, draws figures
│   └── experiments/
│       ├── common.py             # seeding, train/evaluate loop, result files
│       ├── data_stats.py         # dataset sizes and the lookup-table accuracy ceiling
│       ├── mnist_qnn.py          # Experiments 1 + 2: QNN vs classical vs hybrid
│       ├── barren_plateaus.py    # Experiment 3: gradient variance vs qubits and depth
│       └── noise.py              # Experiment 4: depolarizing noise (4×4 eval, 3×3 training)
│
├── tests/test_demo.py            # encoding, parameter counts, a training step, noisy layer, gradients
├── notebooks/Quantum TF Demo.ipynb   # guided walkthrough at small sizes
│
├── results/                      # written by the experiments (committed so figures rebuild)
│   ├── data_stats.json, mnist_qnn.json, barren_plateaus.json, noise.json
│   ├── weights/qnn_seed*.npy     # trained QNN angles, reused by the noise experiment
│   └── logs/*.log                # stdout of the full runs
├── figures/*.png                 # quick plots for the README and notebook
│
├── paper/
│   ├── intake.md                 # claims ↔ evidence, open questions
│   ├── figures_scripts/          # one script per paper figure + make_values.py + make_all.py
│   └── arxiv/
│       ├── main.tex, sections/   # the paper
│       ├── generated/            # values.tex and tables/, written by make_values.py
│       ├── figures/*.pdf         # written by figures_scripts
│       ├── refs.bib, citations_verification.md
│       ├── sources.md            # where every number in the paper comes from
│       ├── outline.md, venue_report.md, checks.md
│       └── main.pdf              # compiled paper
│
├── site/                         # the website
│   ├── build_site.py             # results + paper sources + code → public/ (8 pages)
│   ├── src/style.css, src/site.js    # shared styles; charts, circuit, seed toggles, copy buttons
│   └── public/                   # built site: index, mnist, hybrid, barren, noise, paper, run,
│                                 #   about .html + assets/ (style, site.js, data.js) + paper.pdf
│
└── docs/
    ├── INSTRUCTIONS.md           # setup, run, use
    ├── SYSTEM-DESIGN.md          # architecture, flows, decisions, limits
    └── FILE-STRUCTURE.md         # this file
```

Not committed: `.venv/` (native environment), `.cache/` (MNIST download, scratch scripts),
`paper/arxiv/build/`.
