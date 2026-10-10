# Quantum TF Demo

A reproducible TensorFlow Quantum demo: a 17-qubit quantum neural network learns to tell a 3 from a 6,
compared with a classical network of the same size and a hybrid head, plus barren plateaus and
training under depolarizing noise.

![The website's home page](docs/images/site.png)

| QNN vs classical | Quantum readout vs hybrid head |
|---|---|
| ![QNN vs classical test loss and accuracy per epoch](figures/mnist_qnn.png) | ![QNN vs hybrid test loss and accuracy per epoch](figures/hybrid.png) |
| **Barren plateaus** | **Depolarizing noise** |
| ![Gradient variance vs qubits and depth](figures/barren_plateaus.png) | ![Test accuracy vs depolarizing probability](figures/noise.png) |

## Links

- [Website](site/public/index.html): serve it with `python3 -m http.server --directory site/public`, or host `site/public/` anywhere
- [Paper (PDF)](paper/arxiv/main.pdf)
- [Notebook walkthrough](notebooks/Quantum%20TF%20Demo.ipynb)
- [Instructions: setup, run, use](docs/INSTRUCTIONS.md)
- [System design](docs/SYSTEM-DESIGN.md)
- [File structure](docs/FILE-STRUCTURE.md)
