"""Experiment 2: barren plateaus (McClean et al., 2018).

For random hardware-efficient circuits, measure Var[d<Z0 Z1>/d theta_0] over
random circuits and parameters, as the number of qubits and the depth grow.
"""

import numpy as np

from ..compat import cirq, sympy, tf, tfq
from .common import save, set_seed


def random_circuit(qubits, depth, rng):
    """Initial Ry(pi/4) layer, then `depth` layers of random Pauli rotations + CZ ladder."""
    symbols = []
    circuit = cirq.Circuit(cirq.ry(np.pi / 4)(q) for q in qubits)
    for d in range(depth):
        for i, q in enumerate(qubits):
            s = sympy.Symbol(f"t_{d}_{i}")
            symbols.append(s)
            gate = rng.choice([cirq.rx, cirq.ry, cirq.rz])
            circuit.append(gate(s)(q))
        for a, b in zip(qubits, qubits[1:]):
            circuit.append(cirq.CZ(a, b))
    return circuit, symbols


def grad_variance(n_qubits, depth, n_circuits, seed):
    rng = np.random.default_rng(seed)
    qubits = cirq.GridQubit.rect(1, n_qubits)
    op = cirq.Z(qubits[0]) * cirq.Z(qubits[1])
    expectation = tfq.layers.Expectation(differentiator=tfq.differentiators.Adjoint())
    grads = []
    for _ in range(n_circuits):
        circuit, symbols = random_circuit(qubits, depth, rng)
        values = tf.Variable(rng.uniform(0, 2 * np.pi, (1, len(symbols))).astype("float32"))
        with tf.GradientTape() as tape:
            out = expectation(circuit, symbol_names=symbols, symbol_values=values, operators=op)
        grads.append(float(tape.gradient(out, values)[0, 0]))
    return float(np.var(grads))


def run(cfg):
    set_seed(cfg["seeds"][0])
    by_qubits = []
    for n in cfg["qubits"]:
        v = grad_variance(n, cfg["fixed_depth"], cfg["n_circuits"], seed=n)
        by_qubits.append({"n_qubits": n, "depth": cfg["fixed_depth"], "variance": v})
        print(f"  qubits={n:2d} depth={cfg['fixed_depth']}: var={v:.2e}", flush=True)
    by_depth = []
    for d in cfg["depths"]:
        v = grad_variance(cfg["fixed_qubits"], d, cfg["n_circuits"], seed=100 + d)
        by_depth.append({"n_qubits": cfg["fixed_qubits"], "depth": d, "variance": v})
        print(f"  qubits={cfg['fixed_qubits']} depth={d:3d}: var={v:.2e}", flush=True)

    ns = np.array([r["n_qubits"] for r in by_qubits])
    vs = np.array([r["variance"] for r in by_qubits])
    slope, intercept = np.polyfit(ns, np.log(vs), 1)  # Var ~ exp(slope * n)
    fit = {"log_slope": float(slope), "log_intercept": float(intercept),
           "decay_base": float(np.exp(slope))}
    return save("barren_plateaus", {"config": cfg, "by_qubits": by_qubits,
                                    "by_depth": by_depth, "fit": fit})
