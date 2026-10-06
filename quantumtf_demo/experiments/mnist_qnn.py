"""Experiments 1 and 4: the Farhi-Neven QNN vs a parameter-matched classical network,
and vs the same circuit with a classical dense head (hybrid). All three models see the
same data split for each seed.
"""

import numpy as np

from .. import data, models
from .common import RESULTS, save, set_seed, summarise, train_eval

WEIGHTS = RESULTS / "weights"  # trained QNN angles, reused by the noise experiment

MODELS = {"qnn": models.build_qnn, "hybrid": models.build_hybrid,
          "classical": models.build_classical}


def run(cfg):
    runs = {k: [] for k in MODELS}
    for seed in cfg["seeds"]:
        x_tr, y_tr, x_te, y_te = data.load_binary_mnist(cfg["n_train"], cfg["n_test"], seed)
        yh_tr, yh_te = data.hinge_labels(y_tr), data.hinge_labels(y_te)
        circuits = (data.to_tensor(x_tr), data.to_tensor(x_te))
        for name, build in MODELS.items():
            xtr, xte = (x_tr, x_te) if name == "classical" else circuits
            set_seed(seed)
            m = build(lr=cfg["lr"])
            r = train_eval(m, xtr, yh_tr, xte, yh_te, cfg["epochs"], cfg["batch_size"])
            runs[name].append({"seed": seed, "params": models.count_params(m), **r})
            if name == "qnn":
                WEIGHTS.mkdir(parents=True, exist_ok=True)
                np.save(WEIGHTS / f"qnn_seed{seed}.npy", m.get_weights()[0])
            print(f"  seed {seed} {name:9s} acc {r['test_acc']:.3f}  ({r['train_seconds']:.0f}s)",
                  flush=True)

    summary = {k: summarise(v) for k, v in runs.items()}
    return save("mnist_qnn", {"config": cfg, "n_train_after_filtering": int(len(x_tr)),
                              "summary": summary, "runs": runs})
