"""Experiment 3: the QNN under depolarizing noise.

A depolarizing channel follows every moment of the model circuit, simulated with quantum
trajectories (NoisyPQC). Two measurements:

  * eval_only (4x4, 17 qubits): the QNNs trained noiselessly in Experiment 1, tested
    under each noise level. Inference only, so it runs at the full model size.
  * trained_noisy (cfg["size"], default 3x3 = 10 qubits): train from scratch with the noise
    present. Parameter-shift gradients through noisy trajectories cost ~65x an inference,
    which was too slow at 17 qubits, so this part uses smaller images. Its p=0 entry is
    the matching noise-free baseline.
"""

import numpy as np

from .. import data, models
from .common import save, set_seed, summarise, train_eval
from .mnist_qnn import WEIGHTS


def run(cfg):
    levels = cfg["noise_levels"]
    runs = {"eval_only": {str(p): [] for p in levels},
            "trained_noisy": {str(p): [] for p in levels}}
    for seed in cfg["seeds"]:
        # Part A: Experiment 1's trained 4x4 QNN, tested under noise.
        wfile = WEIGHTS / f"qnn_seed{seed}.npy"
        if not wfile.exists():
            raise FileNotFoundError(f"{wfile} missing: run the mnist_qnn experiment first")
        _, _, x_te, y_te = data.load_binary_mnist(None, cfg["eval_n_test"], seed)
        t_te, yh_te = data.to_tensor(x_te), data.hinge_labels(y_te)
        weights = [np.load(wfile)]
        for p in levels:
            m = models.build_qnn(noise=p, repetitions=cfg["repetitions"])
            m.set_weights(weights)
            loss, acc = m.evaluate(t_te, yh_te, verbose=0)
            runs["eval_only"][str(p)].append({"seed": seed, "test_loss": float(loss),
                                              "test_acc": float(acc)})
            print(f"  seed {seed} p={p}: eval-only (4x4) {acc:.3f}", flush=True)

        # Part B: train from scratch with the noise present, on smaller images.
        size = cfg["size"]
        x_tr, y_tr, x_te, y_te = data.load_binary_mnist(cfg["n_train"], cfg["n_test"], seed, size=size)
        t_tr, t_te = data.to_tensor(x_tr, size), data.to_tensor(x_te, size)
        yh_tr, yh_te = data.hinge_labels(y_tr), data.hinge_labels(y_te)
        for p in levels:
            set_seed(seed)
            m = models.build_qnn(size, lr=cfg["lr"], noise=p, repetitions=cfg["repetitions"])
            r = train_eval(m, t_tr, yh_tr, t_te, yh_te, cfg["epochs"], cfg["batch_size"])
            runs["trained_noisy"][str(p)].append({"seed": seed, **r})
            print(f"  seed {seed} p={p}: trained-noisy ({size}x{size}) {r['test_acc']:.3f}  "
                  f"({r['train_seconds']:.0f}s)", flush=True)

    summary = {mode: {p: summarise(v) for p, v in by_p.items()} for mode, by_p in runs.items()}
    return save("noise", {"config": cfg, "summary": summary, "runs": runs})
