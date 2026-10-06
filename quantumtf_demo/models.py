"""Model builders: the Farhi-Neven QNN, a hybrid variant and a classical baseline."""

from .compat import cirq, keras, sympy, tf, tfq
from .data import SIZE, data_qubits

READOUT = cirq.GridQubit(-1, -1)


def qnn_circuit(size=SIZE, gates=("XX", "ZZ")):
    """Parameterised circuit: each data qubit couples to a readout qubit.

    Returns (circuit, readout_qubit, symbols). One layer per gate type, one
    parameter per (layer, data qubit), so 2 * size**2 parameters by default.
    """
    qubits = data_qubits(size)
    circuit = cirq.Circuit([cirq.X(READOUT), cirq.H(READOUT)])
    symbols = []
    for name in gates:
        gate = getattr(cirq, name)
        for i, q in enumerate(qubits):
            s = sympy.Symbol(f"{name.lower()}{i}")
            symbols.append(s)
            circuit.append(gate(q, READOUT) ** s)
    circuit.append(cirq.H(READOUT))
    return circuit, READOUT, symbols


def hinge_accuracy(y_true, y_pred):
    y_true = tf.squeeze(y_true) > 0.0
    y_pred = tf.squeeze(y_pred) > 0.0
    return tf.reduce_mean(tf.cast(y_true == y_pred, tf.float32))


def _compile(model, lr, loss=None, metrics=None):
    model.compile(
        loss=loss or keras.losses.Hinge(),
        optimizer=keras.optimizers.Adam(learning_rate=lr),
        metrics=metrics or [hinge_accuracy],
    )
    return model


def build_qnn(size=SIZE, lr=0.01, noise=0.0, repetitions=200):
    """Pure-quantum classifier: a single <Z> on the readout qubit is the output.

    With noise > 0 the model circuit gets a depolarizing channel after every
    moment and is simulated with trajectories (NoisyPQC + parameter shift).
    """
    circuit, readout, _ = qnn_circuit(size)
    inputs = keras.Input(shape=(), dtype=tf.string)
    if noise > 0:
        noisy = circuit.with_noise(cirq.depolarize(noise))
        layer = tfq.layers.NoisyPQC(
            noisy,
            cirq.Z(readout),
            repetitions=repetitions,
            sample_based=False,
            differentiator=tfq.differentiators.ParameterShift(),
        )
    else:
        layer = tfq.layers.PQC(circuit, cirq.Z(readout))
    model = keras.Model(inputs, layer(inputs))
    return _compile(model, lr)


def build_hybrid(size=SIZE, lr=0.01, hidden=8):
    """Same circuit body, but <Z> on every qubit feeds a small dense head."""
    circuit, readout, _ = qnn_circuit(size)
    ops = [cirq.Z(q) for q in data_qubits(size)] + [cirq.Z(readout)]
    inputs = keras.Input(shape=(), dtype=tf.string)
    x = tfq.layers.PQC(circuit, ops)(inputs)
    x = keras.layers.Dense(hidden, activation="relu")(x)
    out = keras.layers.Dense(1, activation="tanh")(x)
    return _compile(keras.Model(inputs, out), lr)


def build_classical(size=SIZE, lr=0.01, hidden=2):
    """'Fair' classical baseline on the same binarised pixels (37 parameters at 4x4)."""
    model = keras.Sequential(
        [
            keras.Input(shape=(size, size)),
            keras.layers.Flatten(),
            keras.layers.Dense(hidden, activation="relu"),
            keras.layers.Dense(1, activation="tanh"),
        ]
    )
    return _compile(model, lr)


def count_params(model):
    return int(sum(int(tf.size(w)) for w in model.trainable_weights))
