"""Dataset statistics, including the best accuracy any model can reach on binarised k x k input.

The ceiling is a lookup table: each binarised training pattern predicts its majority label
(unseen patterns predict the majority class), scored on the full 3-vs-6 test set.
"""

import collections

import numpy as np

from .. import data
from .common import save


def stats(size):
    x, y, xt, yt = data.load_binary_mnist(None, None, 0, size=size)
    votes = collections.defaultdict(list)
    for a, b in zip(x, y):
        votes[a.tobytes()].append(b)
    majority = {k: np.mean(v) > 0.5 for k, v in votes.items()}
    prior = y.mean() > 0.5
    pred = np.array([majority.get(a.tobytes(), prior) for a in xt])
    return {"size": size, "n_train": int(len(x)), "n_test": int(len(xt)),
            "unique_train_patterns": len(majority),
            "test_patterns_seen": float(np.mean([a.tobytes() in majority for a in xt])),
            "lookup_ceiling": float(np.mean(pred == yt)),
            "majority_class": float(max(yt.mean(), 1 - yt.mean()))}


def run(cfg):
    by_size = [stats(s) for s in cfg["sizes"]]
    for r in by_size:
        print(f"  {r['size']}x{r['size']}: {r['n_train']} train, ceiling {r['lookup_ceiling']:.3f}", flush=True)
    return save("data_stats", {"config": cfg, "by_size": by_size})
