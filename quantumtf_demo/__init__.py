"""Quantum TF Demo: training experiments with TensorFlow Quantum."""

import os

# Must be set before TensorFlow is imported: TFQ >= 0.7.4 is built on Keras 2
# (tf-keras), and on some macOS builds a multi-threaded BLAS deadlocks on import.
os.environ.setdefault("TF_USE_LEGACY_KERAS", "1")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

__version__ = "0.1.0"
