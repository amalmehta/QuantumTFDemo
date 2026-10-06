"""Write generated/values.tex, generated/tables/*.tex and sources.md from results/*.json.

Every number in the paper's prose is a \\val... macro defined here, and every macro and
hand-typed setting gets a row in sources.md saying where it came from.
"""
import json

import numpy as np

from _common import ROOT, VENUE_DIR

RES = ROOT / "results"
GEN = VENUE_DIR / "generated"

values, rows = [], []


def val(name, value, meaning, source):
    values.append(f"\\newcommand{{\\val{name}}}{{{value}}}")
    rows.append(f"| `\\val{name}` | {value} | {meaning} | {source} |")


def f3(x):
    return f"{x:.3f}"


def sci(x):
    m, e = f"{x:.1e}".split("e")
    return f"{m}\\times10^{{{int(e)}}}"


def load(name):
    p = RES / f"{name}.json"
    return json.loads(p.read_text()) if p.exists() else None


def bold_best(cells, scores):
    best = max(scores)
    return [f"\\textbf{{{c}}}" if s == best else c for c, s in zip(cells, scores)]


def mnist(r):
    src = "results/mnist_qnn.json"
    c = r["config"]
    names = {"qnn": ("Qnn", "QNN (quantum readout)"), "hybrid": ("Hybrid", "QNN + dense head (hybrid)"),
             "classical": ("Classical", "classical MLP")}
    for k, (tag, label) in names.items():
        s, runs = r["summary"][k], r["runs"][k]
        val(f"{tag}Acc", f3(s["mean"]), f"{label}: mean test accuracy", f"{src} → summary.{k}.mean")
        val(f"{tag}Std", f3(s["std"]), f"{label}: std of test accuracy over seeds", f"{src} → summary.{k}.std")
        val(f"{tag}Params", runs[0]["params"], f"{label}: trainable parameters", f"{src} → runs.{k}[0].params")
        val(f"{tag}Secs", f"{np.mean([x['train_seconds'] for x in runs]):.0f}",
            f"{label}: mean wall-clock training seconds", f"{src} → mean(runs.{k}[*].train_seconds)")
    val("MnistNTrain", c["n_train"], "training images per seed (subsample)", f"{src} → config.n_train")
    val("MnistNTest", c["n_test"], "test images per seed (subsample)", f"{src} → config.n_test")
    val("MnistEpochs", c["epochs"], "training epochs", f"{src} → config.epochs")
    val("MnistSeeds", len(c["seeds"]), "number of seeds", f"{src} → len(config.seeds)")
    val("MnistBatch", c["batch_size"], "batch size", f"{src} → config.batch_size")
    val("MnistLr", c["lr"], "Adam learning rate", f"{src} → config.lr")
    gap = r["summary"]["hybrid"]["mean"] - r["summary"]["qnn"]["mean"]
    val("HybridGain", f"{100 * gap:.1f}", "hybrid minus QNN mean accuracy, percentage points",
        f"{src} → 100*(summary.hybrid.mean - summary.qnn.mean)")

    keys = list(names)
    accs = [r["summary"][k]["mean"] for k in keys]
    cells = bold_best([f"{f3(r['summary'][k]['mean'])} $\\pm$ {f3(r['summary'][k]['std'])}" for k in keys], accs)
    lines = [r"\begin{tabular}{lrrr}", r"\toprule",
             r"Model & Parameters & Test accuracy & Train time (s) \\", r"\midrule"]
    for k, cell in zip(keys, cells):
        runs = r["runs"][k]
        lines.append(f"{names[k][1]} & {runs[0]['params']} & {cell} & "
                     f"{np.mean([x['train_seconds'] for x in runs]):.0f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (GEN / "tables" / "mnist.tex").write_text("\n".join(lines) + "\n")


def barren(r):
    src = "results/barren_plateaus.json"
    c, q, d, f = r["config"], r["by_qubits"], r["by_depth"], r["fit"]
    val("BpDecay", f"{f['decay_base']:.2f}", "fitted per-qubit variance decay factor exp(slope)", f"{src} → fit.decay_base")
    val("BpCircuits", c["n_circuits"], "random circuits per point", f"{src} → config.n_circuits")
    val("BpFixedDepth", c["fixed_depth"], "layers in the qubit sweep", f"{src} → config.fixed_depth")
    val("BpFixedQubits", c["fixed_qubits"], "qubits in the depth sweep", f"{src} → config.fixed_qubits")
    val("BpMinQ", q[0]["n_qubits"], "smallest qubit count", f"{src} → by_qubits[0].n_qubits")
    val("BpMaxQ", q[-1]["n_qubits"], "largest qubit count", f"{src} → by_qubits[-1].n_qubits")
    val("BpVarMinQ", f"${sci(q[0]['variance'])}$", "gradient variance at smallest qubit count", f"{src} → by_qubits[0].variance")
    val("BpVarMaxQ", f"${sci(q[-1]['variance'])}$", "gradient variance at largest qubit count", f"{src} → by_qubits[-1].variance")
    val("BpRatio", f"{q[0]['variance'] / q[-1]['variance']:.0f}", "variance ratio smallest/largest qubit count",
        f"{src} → by_qubits[0].variance / by_qubits[-1].variance")
    q8 = next(x for x in q if x["n_qubits"] == 8)
    val("BpRatioEight", f"{q[0]['variance'] / q8['variance']:.0f}", "variance ratio 2 qubits / 8 qubits",
        f"{src} → by_qubits[n=2].variance / by_qubits[n=8].variance")
    val("BpVarEight", f"${sci(q8['variance'])}$", "gradient variance at 8 qubits", f"{src} → by_qubits[n=8].variance")
    val("BpDepthRatio", f"{d[0]['variance'] / d[-1]['variance']:.0f}", "variance ratio shallowest / deepest",
        f"{src} → by_depth[0].variance / by_depth[-1].variance")
    val("BpMinDepth", d[0]["depth"], "shallowest depth", f"{src} → by_depth[0].depth")
    val("BpMaxDepth", d[-1]["depth"], "deepest depth", f"{src} → by_depth[-1].depth")
    val("BpVarShallow", f"${sci(d[0]['variance'])}$", "variance at shallowest depth", f"{src} → by_depth[0].variance")
    val("BpVarDeep", f"${sci(d[-1]['variance'])}$", "variance at deepest depth", f"{src} → by_depth[-1].variance")


def noise(r):
    src = "results/noise.json"
    c, s = r["config"], r["summary"]
    levels = sorted(s["trained_noisy"], key=float)
    val("NoiseSize", c["size"], "image side length for the noise experiment", f"{src} → config.size")
    val("NoiseQubits", c["size"] ** 2 + 1, "qubits in the noise experiment (data + readout)", f"{src} → config.size**2 + 1")
    val("NoiseNTrain", c["n_train"], "training images per seed (noisy training)", f"{src} → config.n_train")
    val("NoiseNTest", c["n_test"], "test images per seed (noisy training)", f"{src} → config.n_test")
    val("NoiseEvalNTest", c["eval_n_test"], "test images per seed (noisy evaluation of 4x4 models)", f"{src} → config.eval_n_test")
    val("NoiseBatch", c["batch_size"], "batch size (noisy training)", f"{src} → config.batch_size")
    val("NoiseLr", c["lr"], "learning rate (noisy training)", f"{src} → config.lr")
    val("NoiseEpochs", c["epochs"], "training epochs", f"{src} → config.epochs")
    val("NoiseReps", c["repetitions"], "trajectories per expectation", f"{src} → config.repetitions")
    val("NoiseSeeds", len(c["seeds"]), "number of seeds", f"{src} → len(config.seeds)")
    val("NoiseMaxP", levels[-1], "largest depolarizing probability", f"{src} → max(config.noise_levels)")
    for mode, tag in (("trained_noisy", "Tr"), ("eval_only", "Ev")):
        val(f"Noise{tag}Clean", f3(s[mode][levels[0]]["mean"]), f"{mode}: mean accuracy at p=0", f"{src} → summary.{mode}['0.0'].mean")
        val(f"Noise{tag}Max", f3(s[mode][levels[-1]]["mean"]), f"{mode}: mean accuracy at largest p",
            f"{src} → summary.{mode}['{levels[-1]}'].mean")
    mid = "0.01"
    if mid in s["eval_only"]:
        val("NoiseEvMid", f3(s["eval_only"][mid]["mean"]), "eval_only: mean accuracy at p=0.01", f"{src} → summary.eval_only['0.01'].mean")
        val("NoiseTrMid", f3(s["trained_noisy"][mid]["mean"]), "trained_noisy: mean accuracy at p=0.01", f"{src} → summary.trained_noisy['0.01'].mean")
    lines = [r"\begin{tabular}{lcc}", r"\toprule",
             r"$p$ & 3$\times$3, trained with noise & 4$\times$4, trained clean, tested with noise \\", r"\midrule"]
    for p in levels:
        tr, ev = s["trained_noisy"][p], s["eval_only"][p]
        # No bolding: the two columns are different models (3x3 vs 4x4), not competitors.
        cells = [f"{f3(tr['mean'])} $\\pm$ {f3(tr['std'])}", f"{f3(ev['mean'])} $\\pm$ {f3(ev['std'])}"]
        lines.append(f"{p} & {cells[0]} & {cells[1]} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (GEN / "tables" / "noise.tex").write_text("\n".join(lines) + "\n")


def data_stats(r):
    src = "results/data_stats.json"
    for i, row in enumerate(r["by_size"]):
        tag = {3: "Three", 4: "Four"}[row["size"]]
        val(f"Ceil{tag}", f3(row["lookup_ceiling"]), f"lookup-table test accuracy ceiling, {row['size']}x{row['size']}",
            f"{src} → by_size[{i}].lookup_ceiling")
        val(f"NTrainFull{tag}", f"{row['n_train']:,}".replace(",", "{,}"), f"training images after filtering, {row['size']}x{row['size']}",
            f"{src} → by_size[{i}].n_train")
        val(f"Patterns{tag}", row["unique_train_patterns"], f"distinct binarised training patterns, {row['size']}x{row['size']}",
            f"{src} → by_size[{i}].unique_train_patterns")
    val("NTestFull", f"{r['by_size'][0]['n_test']:,}".replace(",", "{,}"), "3-vs-6 test images", f"{src} → by_size[0].n_test")


def provenance():
    r = next((x for x in (load("mnist_qnn"), load("noise"), load("barren_plateaus")) if x), None)
    if r:
        v = r["versions"]
        for k, tag in (("tensorflow", "TF"), ("tensorflow_quantum", "TFQ"), ("cirq", "Cirq")):
            val(f"Ver{tag}", v[k], f"{k} version used for the runs", f"results/*.json → versions.{k}")


SETTINGS = """
## Hand-typed settings (from the code)

| Setting in the text | Value | Source |
|---|---|---|
| image size for the main experiments | 4 (4x4 = 16 data qubits, 1 readout, 17 qubits) | quantumtf_demo/data.py → SIZE |
| binarisation threshold | 0.5 | quantumtf_demo/data.py → THRESHOLD |
| digits | 3 vs 6 | quantumtf_demo/data.py → _filter_36 |
| QNN layers | XX then ZZ, one angle per data qubit each (2 per pixel) | quantumtf_demo/models.py → qnn_circuit |
| hybrid head | Dense(8, relu) → Dense(1, tanh) on 17 ⟨Z⟩ values | quantumtf_demo/models.py → build_hybrid |
| classical baseline | Dense(2, relu) → Dense(1, tanh) on 16 pixels | quantumtf_demo/models.py → build_classical |
| barren-plateau observable | Z0 Z1 | quantumtf_demo/experiments/barren_plateaus.py → grad_variance |
| barren-plateau initial layer | Ry(π/4) on every qubit | barren_plateaus.py → random_circuit |
| gradient method (exact runs) | adjoint | barren_plateaus.py; PQC default |
| gradient method (noisy runs) | parameter shift | quantumtf_demo/models.py → build_qnn |
| optimizer, loss | Adam, hinge | quantumtf_demo/models.py → _compile |
| coupling gates in the QNN | 2 per data qubit: 32 at 4x4, 18 at 3x3 | quantumtf_demo/models.py → qnn_circuit |
| hybrid hidden units | 8 | quantumtf_demo/models.py → build_hybrid(hidden=8) |
| classical hidden units | 2 | quantumtf_demo/models.py → build_classical(hidden=2) |
| CPU cores | 8 (Docker) | `docker info` NCPU |
| hyperparameter candidates | 2 (batch 32 / lr 0.01 vs batch 16 / lr 0.02) | .cache/tune.py (not committed) |
| 1, 2, 3, 4 in "Experiment 1/2/3/4", section and figure numbering | labels, not results | — |
"""


def main():
    (GEN / "tables").mkdir(parents=True, exist_ok=True)
    for name, fn in (("data_stats", data_stats), ("mnist_qnn", mnist), ("barren_plateaus", barren), ("noise", noise)):
        r = load(name)
        if r:
            fn(r)
        else:
            print(f"skip values for {name}: results missing")
    provenance()
    (GEN / "values.tex").write_text("% Generated by figures_scripts/make_values.py; do not edit.\n"
                                    + "\n".join(values) + "\n")
    (VENUE_DIR / "sources.md").write_text(
        "# Sources\n\nGenerated by `paper/figures_scripts/make_values.py`. Every macro in the paper "
        "and where its value comes from.\n\n| Macro | Value | Meaning | Source |\n|---|---|---|---|\n"
        + "\n".join(rows) + "\n" + SETTINGS)
    print(f"wrote {len(values)} values")


if __name__ == "__main__":
    main()
