# Outline: arXiv preprint (article class, 10 pt, 1-inch margins, one column)

Target length: 5 pages of main text plus references. arXiv sets no page limit; 5 pages is the
length agreed in the setup questions (4–6).

## Page budget

| Section | Pages | Carries |
|---|---|---|
| Abstract + 1 Introduction | 0.8 | C1–C5 preview, contributions |
| 2 Background (QNNs, TFQ, barren plateaus, noise) | 0.6 | citations only |
| 3 Setup (data, models, training, simulation, compute) | 1.0 | Fig. 1 schematic, settings |
| 4 Results (4.1 QNN vs classical, 4.2 hybrid, 4.3 barren plateaus, 4.4 noise) | 2.0 | Tab. 1, Fig. 2–4, Tab. 2 |
| 5 Limitations | 0.3 | scale, simulation-only, 3×3 noise |
| 6 Conclusion + reproducibility | 0.3 | how to rerun |

## Figures and tables

| ID | Takeaway (caption's first sentence) | Data | Script | Width |
|---|---|---|---|---|
| Fig. 1 | QNN circuit: each data qubit couples to a readout qubit through XX and ZZ gates | n/a (TikZ) | figures/qnn_circuit.tex | text |
| Tab. 1 | Accuracy and size of the three models | results/mnist_qnn.json | make_values.py → tables/mnist.tex | text |
| Fig. 2 | Test loss/accuracy per epoch, QNN vs classical | results/mnist_qnn.json | mnist_qnn.py | text |
| Fig. 3 | Quantum readout vs hybrid head | results/mnist_qnn.json | hybrid.py | text |
| Fig. 4 | Gradient variance vs qubits and depth | results/barren_plateaus.json | barren_plateaus.py | text |
| Fig. 5 + Tab. 2 | Accuracy vs depolarizing probability | results/noise.json | noise.py, make_values.py → tables/noise.tex | 0.6 text |

## Required statements

arXiv requires none. Included anyway: a short AI-use note (honest description of the drafting and
code generation) and a reproducibility paragraph.

## Changelog

- 2026-10-06: first outline.
