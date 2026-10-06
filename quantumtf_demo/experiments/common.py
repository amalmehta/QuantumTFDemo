"""Shared helpers: seeding, a train/evaluate loop and result files."""

import json
import pathlib
import random
import time

import numpy as np

from ..compat import tf, versions

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)


def train_eval(model, x_train, y_train, x_test, y_test, epochs, batch_size=32):
    """Fit, then evaluate on the test set. Returns a JSON-friendly dict."""
    start = time.time()
    hist = model.fit(
        x_train,
        y_train,
        batch_size=batch_size,
        epochs=epochs,
        validation_data=(x_test, y_test),
        verbose=0,
    )
    train_s = time.time() - start
    loss, acc = model.evaluate(x_test, y_test, verbose=0)
    return {
        "test_loss": float(loss),
        "test_acc": float(acc),
        "train_seconds": round(train_s, 2),
        "history": {k: [float(v) for v in vs] for k, vs in hist.history.items()},
    }


def summarise(runs, key="test_acc"):
    vals = np.array([r[key] for r in runs], dtype=float)
    return {"mean": float(vals.mean()), "std": float(vals.std()), "n": int(len(vals))}


def save(name, payload):
    RESULTS.mkdir(exist_ok=True)
    payload = {"experiment": name, "versions": versions(), **payload}
    path = RESULTS / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2))
    return path


def load(name):
    return json.loads((RESULTS / f"{name}.json").read_text())
