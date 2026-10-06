"""MNIST 3-vs-6 data, downsampled to 4x4 and encoded as basis-state circuits.

Follows Farhi & Neven (2018) and the TensorFlow Quantum MNIST tutorial:
filter two digits, downsample, drop training images whose downsampled form
appears with both labels ("contradictory"), binarise, then encode each pixel
as an X gate. Contradictions are removed before binarising, as in the
tutorial; removing them after binarising discards about 70% of the data.
"""

import collections

import numpy as np

from .compat import cirq, keras, tf, tfq

SIZE = 4  # images become SIZE x SIZE -> SIZE**2 data qubits
THRESHOLD = 0.5


def _filter_36(x, y):
    keep = (y == 3) | (y == 6)
    return x[keep], (y[keep] == 3)  # True for "3"


def remove_contradicting(xs, ys):
    """Drop images that appear with both labels."""
    mapping = collections.defaultdict(set)
    keys = [tuple(x.flatten()) for x in xs]
    for k, y in zip(keys, ys):
        mapping[k].add(bool(y))
    keep = [len(mapping[k]) == 1 for k in keys]
    return xs[keep], ys[keep]


def load_binary_mnist(n_train=None, n_test=None, seed=0, size=SIZE):
    """Return (x_train, y_train, x_test, y_test) as binarised size x size arrays.

    Labels are booleans (True = digit 3). Subsets are drawn with `seed`.
    """
    (x_tr, y_tr), (x_te, y_te) = keras.datasets.mnist.load_data()
    out = []
    for x, y in ((x_tr, y_tr), (x_te, y_te)):
        x, y = _filter_36(x, y)
        x = x[..., np.newaxis].astype("float32") / 255.0
        x = tf.image.resize(x, (size, size)).numpy()[..., 0]
        out.append((x, y))
    (x_tr, y_tr), (x_te, y_te) = out
    x_tr, y_tr = remove_contradicting(x_tr, y_tr)
    x_tr = (x_tr > THRESHOLD).astype("float32")
    x_te = (x_te > THRESHOLD).astype("float32")

    rng = np.random.default_rng(seed)
    if n_train is not None and n_train < len(x_tr):
        idx = rng.choice(len(x_tr), n_train, replace=False)
        x_tr, y_tr = x_tr[idx], y_tr[idx]
    if n_test is not None and n_test < len(x_te):
        idx = rng.choice(len(x_te), n_test, replace=False)
        x_te, y_te = x_te[idx], y_te[idx]
    return x_tr, y_tr, x_te, y_te


def data_qubits(size=SIZE):
    return cirq.GridQubit.rect(size, size)


def encode_image(image, size=SIZE):
    """Basis encoding: an X gate on each qubit whose pixel is 1."""
    qubits = data_qubits(size)
    circuit = cirq.Circuit()
    for q, v in zip(qubits, np.ravel(image)):
        if v:
            circuit.append(cirq.X(q))
    return circuit


def to_tensor(images, size=SIZE):
    return tfq.convert_to_tensor([encode_image(x, size) for x in images])


def hinge_labels(y):
    """Map boolean labels to +/-1 for the hinge loss."""
    return 2.0 * np.asarray(y, dtype="float32") - 1.0
