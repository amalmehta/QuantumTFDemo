"""Fast checks of the data pipeline, models and experiment helpers (no MNIST download)."""

import numpy as np
import pytest

from quantumtf_demo import data, models
from quantumtf_demo.compat import cirq, tfq
from quantumtf_demo.experiments import barren_plateaus


def test_encode_image_puts_x_on_set_pixels():
    img = np.zeros((4, 4)); img[0, 1] = img[3, 3] = 1
    c = data.encode_image(img)
    assert len(list(c.all_operations())) == 2
    assert all(isinstance(op.gate, type(cirq.X)) for op in c.all_operations())


def test_remove_contradicting_drops_ambiguous_images():
    xs = np.array([[[1.0]], [[1.0]], [[0.0]]])
    ys = np.array([True, False, True])
    x, y = data.remove_contradicting(xs, ys)
    assert len(x) == 1 and y[0]


def test_hinge_labels():
    assert list(data.hinge_labels([True, False])) == [1.0, -1.0]


def test_qnn_circuit_has_two_params_per_pixel():
    circuit, readout, symbols = models.qnn_circuit()
    assert len(symbols) == 32
    assert readout in circuit.all_qubits()


@pytest.mark.parametrize("builder,expected", [
    (models.build_qnn, 32), (models.build_classical, 37), (models.build_hybrid, 32 + 17 * 8 + 8 + 9)])
def test_param_counts(builder, expected):
    assert models.count_params(builder()) == expected


def test_qnn_trains_on_a_toy_batch():
    rng = np.random.default_rng(0)
    x = (rng.random((16, 4, 4)) > 0.5).astype("float32")
    y = data.hinge_labels(x[:, 0, 0] > 0)  # learnable: label = top-left pixel
    t = data.to_tensor(x)
    m = models.build_qnn(lr=0.05)
    before = m.evaluate(t, y, verbose=0)[0]
    m.fit(t, y, epochs=5, batch_size=16, verbose=0)
    assert m.evaluate(t, y, verbose=0)[0] < before


def test_noisy_qnn_runs():
    x = np.zeros((2, 4, 4), dtype="float32")
    m = models.build_qnn(noise=0.01, repetitions=5)
    out = m(data.to_tensor(x)).numpy()
    assert out.shape == (2, 1) and np.all(np.abs(out) <= 1)


def test_gradient_variance_shrinks_with_qubits():
    small = barren_plateaus.grad_variance(2, 10, 30, seed=1)
    large = barren_plateaus.grad_variance(8, 10, 30, seed=1)
    assert np.isfinite(small) and large < small
