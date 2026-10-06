"""Run every experiment, then draw the figures.

    python -m quantumtf_demo.run_all                 # full preset (used for the paper)
    python -m quantumtf_demo.run_all --preset quick  # ~minutes, smoke test
    python -m quantumtf_demo.run_all --only barren_plateaus noise
"""

import argparse
import time

PRESETS = {
    "quick": {
        "data_stats": dict(sizes=[3, 4]),
        "mnist_qnn": dict(n_train=200, n_test=100, epochs=1, batch_size=32, lr=0.01, seeds=[0]),
        "barren_plateaus": dict(qubits=[2, 4, 6], depths=[1, 5, 10], fixed_qubits=4,
                                fixed_depth=10, n_circuits=20, seeds=[0]),
        "noise": dict(eval_n_test=32, size=3, n_train=64, n_test=32, epochs=1, batch_size=16,
                      lr=0.02, seeds=[0], noise_levels=[0.0, 0.01], repetitions=20),
    },
    "full": {
        "data_stats": dict(sizes=[3, 4]),
        "mnist_qnn": dict(n_train=3000, n_test=500, epochs=4, batch_size=32, lr=0.01,
                          seeds=[0, 1, 2]),
        "barren_plateaus": dict(qubits=[2, 4, 6, 8, 10, 12], depths=[1, 2, 5, 10, 20, 50],
                                fixed_qubits=8, fixed_depth=50, n_circuits=200, seeds=[0]),
        "noise": dict(eval_n_test=500, size=3, n_train=200, n_test=200, epochs=3, batch_size=16,
                      lr=0.02, seeds=[0, 1, 2], noise_levels=[0.0, 0.001, 0.003, 0.01, 0.03],
                      repetitions=50),
    },
}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--preset", choices=PRESETS, default="full")
    p.add_argument("--only", nargs="+", choices=list(PRESETS["full"]))
    p.add_argument("--no-figures", action="store_true")
    args = p.parse_args(argv)

    from .experiments import barren_plateaus, data_stats, mnist_qnn, noise

    modules = {"data_stats": data_stats, "mnist_qnn": mnist_qnn,
               "barren_plateaus": barren_plateaus, "noise": noise}
    for name in args.only or modules:
        cfg = dict(PRESETS[args.preset][name], preset=args.preset)
        print(f"[{name}] preset={args.preset}", flush=True)
        t = time.time()
        path = modules[name].run(cfg)
        print(f"[{name}] done in {time.time() - t:.0f}s -> {path}", flush=True)

    if not args.no_figures:
        from . import figures
        figures.main()


if __name__ == "__main__":
    main()
