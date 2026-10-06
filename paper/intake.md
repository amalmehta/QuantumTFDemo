# Intake: Training Quantum Neural Networks with TensorFlow Quantum — a Reproducible Demo

Inputs: the project brief (`demo_with_quantumtf.md`: "create a demo with the quantum tensorflow
library, run some training experiments"; deliverables "demo & paper"), the answers to the setup
questions (four experiments, LaTeX preprint, local git only), the code in `quantumtf_demo/`, and
`results/*.json` (full preset).

The brief gives no scientific claims of its own, so the claims below are the questions the
experiments were designed to answer. Each one is worded to match what the data supports, and the
status column is filled in from the results.

## Claims

| # | Claim | Evidence | Status |
|---|---|---|---|
| C1 | TFQ makes a 17-qubit Farhi–Neven QNN trainable end to end inside Keras, on a laptop CPU | results/mnist_qnn.json → runs.qnn | **supported**: 0.868 ± 0.023, ~9 min per run |
| C2 | On 4×4 binarised MNIST 3-vs-6, a 37-parameter classical net matches or beats the 32-parameter QNN | results/mnist_qnn.json → summary | **supported**: 0.909 ± 0.006 vs 0.868 ± 0.023 |
| C3 | Adding a small classical head to the same circuit (hybrid) changes accuracy by `\valHybridGain` points | results/mnist_qnn.json → summary | **supported**: +3.8 points, matching the classical model; confounded by 153 extra classical parameters (stated) |
| C4 | Gradient variance of random circuits decays exponentially with qubit count (barren plateaus) and saturates with depth | results/barren_plateaus.json | **partial**, reworded: 27× drop from 2→8 qubits, flat 8→12. Depth does *not* saturate by 50 layers at 8 qubits |
| C5 | Depolarizing noise lowers QNN accuracy; training with the noise present recovers part of the loss compared with training clean | results/noise.json | **first half supported** (4×4: 0.859 → 0.770 → 0.501). **Second half not shown**: the 3×3 comparison is confounded by circuit size, and the paper says so |

## Facts I still need from you

- Author name(s) and affiliation for the title block (currently "\TODO{author}").
- Whether to keep the framing "reproducible demo / tutorial study" (recommended, since nothing here
  is novel) or position it differently.

## Disagreements between inputs

- The setup answer listed "hybrid quantum-classical" as a separate experiment. In the code it shares
  data and seeds with Experiment 1, so the QNN baseline is trained once (`experiments/mnist_qnn.py`).
- Noise: the 4×4 models are tested under noise (inference only); noisy *training* uses 3×3 images
  (10 qubits), because parameter shift through noisy trajectories was too slow at 17 qubits (~400 s per
  64 images per epoch in a test run).
- Data-pipeline bug found and fixed before the final runs: contradictions were first removed after
  binarising, which kept 30% of the data. They are now removed before binarising, as in the tutorial.
