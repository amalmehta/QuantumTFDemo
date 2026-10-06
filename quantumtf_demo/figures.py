"""Plotting functions for results/*.json.

    python -m quantumtf_demo.figures      # quick PNGs in figures/ (README, notebook)

The paper's figure scripts (paper/figures_scripts/) call the same plot_* functions at
the paper's exact widths, so the README and the paper never show different plots.
"""

import json
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS, FIGURES = ROOT / "results", ROOT / "figures"

# Okabe-Ito (colorblind-safe), plus a neutral for fits.
BLUE, ORANGE, GREY = "#0072B2", "#D55E00", "#7a7f88"


def load(name):
    path = RESULTS / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def _curves(ax, runs, key, color, label, marker):
    arr = np.array([r["history"][key] for r in runs])
    x = np.arange(1, arr.shape[1] + 1)
    ax.plot(x, arr.mean(0), color=color, label=label, marker=marker)
    if len(arr) > 1:
        ax.fill_between(x, arr.mean(0) - arr.std(0), arr.mean(0) + arr.std(0),
                        color=color, alpha=0.2, lw=0)
    ax.set_xticks(x)


def plot_pair(res, keys, labels, figsize):
    """Test loss and accuracy per epoch for two models (mean +/- std over seeds)."""
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    for k, lab, c, mk in zip(keys, labels, (BLUE, ORANGE), ("o", "s")):
        runs = res["runs"][k]
        _curves(axes[0], runs, "val_loss", c, lab, mk)
        _curves(axes[1], runs, "val_hinge_accuracy", c, lab, mk)
    axes[0].set(xlabel="epoch", ylabel="test hinge loss")
    axes[1].set(xlabel="epoch", ylabel="test accuracy")
    axes[1].legend()
    return fig


def plot_mnist(res, figsize):
    p = res["runs"]["classical"][0]["params"]
    return plot_pair(res, ("qnn", "classical"), ("QNN", f"classical ({p} params)"), figsize)


def plot_hybrid(res, figsize):
    return plot_pair(res, ("qnn", "hybrid"), ("quantum readout", "hybrid head"), figsize)


def plot_barren(res, figsize):
    fig, axes = plt.subplots(1, 2, figsize=figsize)
    q = res["by_qubits"]
    ns, vs = [r["n_qubits"] for r in q], [r["variance"] for r in q]
    axes[0].semilogy(ns, vs, "o-", color=BLUE, label="measured")
    f = res["fit"]
    xs = np.linspace(min(ns), max(ns), 50)
    axes[0].semilogy(xs, np.exp(f["log_intercept"] + f["log_slope"] * xs), "--", color=GREY,
                     label=f"fit $\\propto {f['decay_base']:.2f}^n$")
    axes[0].set(xlabel=f"qubits (depth {q[0]['depth']})",
                ylabel=r"Var$[\partial_{\theta_0}\langle Z_0Z_1\rangle]$")
    axes[0].legend()
    d = res["by_depth"]
    axes[1].loglog([r["depth"] for r in d], [r["variance"] for r in d], "s-", color=ORANGE)
    axes[1].set(xlabel=f"layers ({d[0]['n_qubits']} qubits)")
    return fig


def plot_noise(res, figsize):
    fig, ax = plt.subplots(figsize=figsize)
    k = res["config"]["size"]
    for mode, c, mk, lab in (("eval_only", BLUE, "o", "4x4 (17 qubits): trained clean, tested noisy"),
                             ("trained_noisy", ORANGE, "s",
                              f"{k}x{k} ({k * k + 1} qubits): trained and tested noisy")):
        s = res["summary"][mode]
        ps = sorted(s, key=float)
        ax.errorbar([float(p) for p in ps], [s[p]["mean"] for p in ps],
                    yerr=[s[p]["std"] for p in ps], marker=mk, capsize=2, color=c, label=lab)
    ax.set(xlabel="depolarizing probability $p$ per moment", ylabel="test accuracy")
    ax.legend()
    return fig


PLOTS = {"mnist_qnn": plot_mnist, "hybrid": plot_hybrid,
         "barren_plateaus": plot_barren, "noise": plot_noise}
QUICK_SIZE = {"mnist_qnn": (6.4, 2.4), "hybrid": (6.4, 2.4),
              "barren_plateaus": (6.4, 2.4), "noise": (4.2, 2.6)}


def main():
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "legend.frameon": False, "figure.constrained_layout.use": True})
    FIGURES.mkdir(exist_ok=True)
    for name, plot in PLOTS.items():
        res = load("mnist_qnn" if name == "hybrid" else name)
        if res:
            fig = plot(res, QUICK_SIZE[name])
            fig.savefig(FIGURES / f"{name}.png", dpi=160)
            plt.close(fig)
    print(f"figures -> {FIGURES}")


if __name__ == "__main__":
    main()
