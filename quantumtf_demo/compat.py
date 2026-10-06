"""Version shims so the same code runs on TFQ 0.7.2 (TF 2.7) and TFQ 0.7.6 (TF 2.18)."""

import quantumtf_demo  # noqa: F401  (sets env vars before TF loads)
import tensorflow as tf

try:  # TF >= 2.16 ships Keras 3 as tf.keras; TFQ needs Keras 2.
    import tf_keras as keras
except ImportError:  # TF 2.7
    keras = tf.keras

import cirq
import sympy
import tensorflow_quantum as tfq

__all__ = ["tf", "keras", "cirq", "sympy", "tfq", "versions"]


def versions():
    return {
        "tensorflow": tf.__version__,
        "tensorflow_quantum": tfq.__version__,
        "cirq": cirq.__version__,
        "keras": keras.__version__ if hasattr(keras, "__version__") else "builtin",
    }
