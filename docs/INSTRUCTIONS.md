# Instructions

How to set up Quantum TF Demo, run the experiments, and rebuild the paper and the site.

## 1. Set up

Two routes. Docker is recommended: it uses the latest TensorFlow Quantum and runs about 4× faster
than the native macOS route on the test machine.

### Docker (recommended): TFQ 0.7.6, TensorFlow 2.18

```bash
docker build -t quantumtfdemo .
```

The image is about 3 GB. `TF_USE_LEGACY_KERAS=1` is set inside it, because TFQ needs Keras 2
(`tf-keras`), not the Keras 3 that ships with TensorFlow 2.16+.

### Native macOS (Intel only): TFQ 0.7.2, TensorFlow 2.7

TFQ 0.7.2 is the last release with macOS wheels, and they are x86_64 only. Apple Silicon has to
use Docker.

```bash
conda create -y -p ./.venv python=3.9 pip
.venv/bin/python -m pip install --only-binary=:all: -r requirements.txt
```

The wheel is tagged `macosx_12_1`, but on macOS 11+ pip only accepts `macosx_XX_0` tags. Download
it and install it under a `12_0` name (the file contents are unchanged):

```bash
curl -L -o tensorflow_quantum-0.7.2-cp39-cp39-macosx_12_0_x86_64.whl https://files.pythonhosted.org/packages/83/ab/256e5c340e5fe044129de1592d93ea8fd8940535755d139b0523a2ce9fc1/tensorflow_quantum-0.7.2-cp39-cp39-macosx_12_1_x86_64.whl
```

```bash
.venv/bin/python -m pip install --no-deps tensorflow_quantum-0.7.2-cp39-cp39-macosx_12_0_x86_64.whl
```

Known native issues:

- **Imports hang at 0% CPU.** The multi-threaded BLAS in old numpy deadlocks on recent macOS.
  `quantumtf_demo` sets `OPENBLAS_NUM_THREADS=1` before importing numpy. Set it yourself when you
  import TensorFlow outside the package.
- **The first import is slow** (about 100 s on a busy machine) while macOS loads the large TFQ libraries.
- The python.org Python 3.9.1 build hangs in compiled extensions on macOS 26. Use conda's Python 3.9.

## 2. Run the experiments

Docker commands below mount the repo at `/work`, so results land in your checkout. Add
`-v "$PWD/.cache/keras":/root/.keras` to cache the MNIST download between runs.

| What | Command | Time (8-core laptop) |
|---|---|---|
| Tests | `docker run --rm -v "$PWD":/work quantumtfdemo python -m pytest -q tests` | ~1 min |
| Smoke test, all experiments | `docker run --rm -v "$PWD":/work quantumtfdemo python -m quantumtf_demo.run_all --preset quick` | ~10 min |
| Full runs (paper) | `docker run --rm -v "$PWD":/work quantumtfdemo python -m quantumtf_demo.run_all --preset full` | ~2–3 h |
| One experiment | add `--only barren_plateaus` (or `mnist_qnn`, `noise`) | |

Natively, replace `docker run … quantumtfdemo python` with `.venv/bin/python`.

`noise` reuses the QNN weights that `mnist_qnn` saves in `results/weights/`, so run `mnist_qnn` first
(`run_all` does this in order).

Outputs:

- `results/<experiment>.json`: the configuration, library versions, every seed, every epoch
- `results/weights/qnn_seed<N>.npy`: the trained QNN angles
- `figures/*.png`: quick plots (`python -m quantumtf_demo.figures` redraws them)

Presets live in `quantumtf_demo/run_all.py` (`PRESETS`). Edit them there.

## 3. Use the notebook

```bash
.venv/bin/python -m jupyter lab "notebooks/Quantum TF Demo.ipynb"
```

or in Docker:

```bash
docker run --rm -p 8888:8888 -v "$PWD":/work quantumtfdemo jupyter lab --ip 0.0.0.0 --allow-root --no-browser
```

The notebook runs every experiment at small sizes in a few minutes, then shows the full-run
figures if `figures/` has them.

## 4. Rebuild the paper

```bash
.venv/bin/python paper/figures_scripts/make_all.py paper/arxiv
```

```bash
cd paper/arxiv && tectonic main.tex --keep-logs --keep-intermediates
```

`make_all.py` writes every number (`generated/values.tex`), table (`generated/tables/`) and figure
(`figures/*.pdf`) from `results/*.json`, plus `sources.md`, which records where each number comes from.

## 5. Rebuild the site

```bash
python3 site/build_site.py
```

This writes `site/index.html` with the results embedded, and copies the paper PDF next to it if it
has been compiled. Open the file in a browser, or serve `site/` with any static host (GitHub Pages
works as is).
