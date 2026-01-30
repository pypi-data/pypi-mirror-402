# lrdbenchmark

Modern, reproducible benchmarking for long-range dependence (LRD) estimation across classical statistics, machine learning, and neural approaches.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10–3.12](https://img.shields.io/badge/python-3.10%E2%80%933.12-blue.svg)](https://www.python.org/downloads/)
[![Version 2.3.2](https://img.shields.io/badge/version-2.3.2-green.svg)](https://pypi.org/project/lrdbenchmark/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17535020.svg)](https://doi.org/10.5281/zenodo.17535020)

---

## Why lrdbenchmark?

- **One interface, twenty estimators** – 13 classical, 3 machine learning, and 4 neural estimators share a unified API with consistent metadata.
- **Deterministic by construction** – global RNG coordination, stratified summaries, significance testing, and provenance capture are built in.
- **Runtime profiles** – choose `quick` for smoke tests or CI, or `full` for exhaustive diagnostics, bootstraps, and robustness panels.
- **Production-aware workflows** – supports CPU-only deployments by default with optional JAX/Numba/Torch acceleration.
- **Documentation-first tutorials** – the tutorial series now ships directly in `docs/tutorials/`, mirrored by lightweight Markdown notebooks for interactive sessions.

---

## Getting Started

### Installation

```bash
pip install lrdbenchmark
```

Acceleration backends (JAX, Numba, PyTorch) are **optional** and auto-detected at runtime. The library falls back to NumPy when accelerators are unavailable. Install accelerators only if you need them:

```bash
pip install lrdbenchmark[accel-jax]      # JAX for GPU/TPU
pip install lrdbenchmark[accel-numba]    # Numba JIT compilation
pip install lrdbenchmark[accel-pytorch]  # PyTorch for neural estimators
pip install lrdbenchmark[accel-all]      # All accelerators
```

### Pretrained models

Large pretrained estimators (joblib/pth files) live in a separate download channel to keep the repository lightweight. Fetch them with checksum verification whenever you need deterministic ML/NN baselines:

```bash
python tools/fetch_pretrained_models.py          # download every published artifact
python tools/fetch_pretrained_models.py --list   # inspect available keys
python tools/fetch_pretrained_models.py --models random_forest_estimator svr_estimator
```

By default the artefacts are cached under `~/.cache/lrdbenchmark/models`. Override the location with `LRDBENCHMARK_MODELS_DIR=/path/to/artifacts` if you need a project-local cache (e.g., `artifacts/models/` inside the repo, which is Git-ignored).

### Supported environments

- Python 3.10–3.12 across Linux, macOS, and Windows (covered in CI).
- NumPy 2.x is the preferred runtime and receives full testing; NumPy 1.26.x remains available for legacy stacks but only receives best-effort support.
- GPU/acceleration extras require the latest compatible backends (JAX ≥ 0.4.28, PyTorch ≥ 2.2, Numba ≥ 0.60) to ensure Python 3.12 and NumPy 2 compatibility.

### Runtime configuration

- CPU guard: the package defaults to safe CPU-only settings to avoid noisy CUDA warnings. Override by setting `LRDBENCHMARK_AUTO_CPU=0` *before* importing to opt into your own CUDA configuration.
- Asset cache: set `LRDBENCHMARK_MODELS_DIR=/path/to/cache` if you want pretrained weights downloaded into a custom directory (default is `~/.cache/lrdbenchmark/models`).

---

## Command-Line Benchmarks

Run classical estimator failure analysis from the CLI:

```bash
# Quick screening (~5 min) - 3 H values, 2 lengths, 10 realizations
python scripts/benchmarks/run_classical_failure_benchmark.py --profile quick

# Standard analysis (~1 hour) - 7 H values, 3 lengths, 100 realizations
python scripts/benchmarks/run_classical_failure_benchmark.py --profile standard

# Full publication run (~8-10 hours) - 17 H values, 7 lengths, 500 realizations
python scripts/benchmarks/run_classical_failure_benchmark.py --profile full
```

### CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `--profile` | `standard` | `quick`, `standard`, or `full` |
| `--output` | auto | Custom output directory |
| `--seed` | 42 | Random seed for reproducibility |
| `--realizations` | per-profile | Override realization count |
| `--checkpoint-every` | 100 | Checkpoint frequency |
| `--no-resume` | false | Start fresh, ignore checkpoints |
| `--dry-run` | false | Show config without running |

### Example Workflows

```bash
# Dry-run to see configuration
python scripts/benchmarks/run_classical_failure_benchmark.py --dry-run --profile full

# Custom output and more realizations
python scripts/benchmarks/run_classical_failure_benchmark.py --profile standard \
    --output results/my_experiment --realizations 200

# Resume interrupted run (automatic)
python scripts/benchmarks/run_classical_failure_benchmark.py --profile full
```

Results are saved as `results.csv`, `summary.json`, and `config.json` in the output directory.

---

## First Benchmark (Python API)


```python
from lrdbenchmark import ComprehensiveBenchmark

# Quick profile skips heavy diagnostics – perfect for tests and CI
benchmark = ComprehensiveBenchmark(runtime_profile="quick")
summary = benchmark.run_comprehensive_benchmark(
    data_length=256,
    benchmark_type="classical",
    save_results=False,
)

print(summary["random_state"])
print(summary["stratified_metrics"]["hurst_bands"])
```

Want the full analysis (bootstrap confidence intervals, robustness panels, influence diagnostics)? Simply drop the profile override:

```python
benchmark = ComprehensiveBenchmark()   # runtime_profile defaults to "auto"/"full"
```

### Runtime Profiles at a Glance

| Profile | How to enable | Designed for | What is disabled |
|---------|---------------|--------------|------------------|
| `quick` | `ComprehensiveBenchmark(runtime_profile="quick")` or `export LRDBENCHMARK_RUNTIME_PROFILE=quick` | Unit tests, CI, exploratory work | Advanced metrics, bootstraps, robustness panels, heavy diagnostics |
| `full`  | Default when running outside pytest/quick mode | End-to-end studies, publications | Nothing – full diagnostics and provenance |

---

## Core Capabilities

- **Estimator families** – temporal (R/S, DFA, DMA, GHE, Higuchi), spectral (Periodogram, GPH, Whittle), wavelet (CWT, variance, log-variance, wavelet Whittle), multifractal (MFDFA, wavelet leaders), machine-learning (Random Forest, SVR, Gradient Boosting), and neural (CNN, LSTM, GRU, Transformer).
- **Robust benchmarking** – contamination models, adaptive preprocessing, stratified reporting, non-parametric significance tests, and provenance bundles per result.
- **Nonstationarity testing** – time-varying H generators (regime switching, continuous drift, structural breaks), critical regime models (OU, fractional Lévy, SOC), and structural break detection (CUSUM, Chow test, ICSS).
- **Surrogate data testing** – IAAFT, phase randomization, and AR surrogates for hypothesis testing of LRD and nonlinearity.
- **Analytics tooling** – convergence analysis, bias estimation, stress panels, uncertainty calibration (including studentized bootstrap with coverage analysis), scale influence diagnostics.
- **GPU-aware execution** – intelligent fallbacks (JAX ▶ Numba ▶ NumPy) with automatic CPU mode unless the user explicitly opts into GPU acceleration.
- **Containerized experiments** – Docker support for reproducible cloud/HPC benchmarking.

For the full catalogue see the [API reference](https://lrdbenchmark.readthedocs.io/en/latest/api/).

---


## Documentation & Learning Path

- **Full documentation**: <https://lrdbenchmark.readthedocs.io/>
- **Tutorial sequence**: `docs/tutorials/` (rendered on Read the Docs, aligned with the original notebook curriculum)
- **Interactive notebooks**: Markdown sources in `notebooks/markdown/`, easily opened via [Jupytext](https://jupytext.readthedocs.io/) or any Markdown-friendly notebook environment
- **Examples & scripts**: runnable patterns in `examples/` and `scripts/`

### Working with the Markdown notebooks

```bash
pip install jupytext
jupytext --to notebook notebooks/markdown/02_estimation_and_validation.md
jupyter notebook notebooks/markdown/
```

This keeps the repository light while preserving the original interactive walkthroughs.

---

## Project Layout

```
lrdbenchmark/
├── lrdbenchmark/            # Package modules
│   ├── analysis/            # Estimators, benchmarking, diagnostics
│   ├── analytics/           # Provenance, reporting, dashboards
│   ├── models/              # Data generators & contamination models
│   └── robustness/          # Adaptive preprocessing & stress tests
├── artifacts/               # (Ignored) downloaded pretrained weights
├── docs/                    # Sphinx documentation & tutorials
├── notebooks/               # Markdown notebooks + supporting artefacts
├── examples/                # Minimal usage examples
├── scripts/                 # Reproducible benchmarking pipelines
└── tests/                   # Pytest suite (quick profile by default)
```

---

## Testing

```bash
python -m pytest                       # quick profile exercises
python -m pytest --cov=lrdbenchmark    # add coverage
```

---

## Contributing

We welcome improvements to estimators, diagnostics, documentation, and tutorials.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/improvement`
3. Run the test suite (see above)
4. Submit a pull request describing the change and relevant use-cases

Please consult `CONTRIBUTING.md` for coding standards and review expectations.

---

## Citation

```bibtex
@software{chin2024lrdbenchmark,
  author  = {Chin, Davian R.},
  title   = {lrdbenchmark: A Comprehensive Framework for Long-Range Dependence Estimation},
  version = {2.3.2},
  year    = {2025},
  doi     = {10.5281/zenodo.17535020},
  url     = {https://github.com/dave2k77/lrdbenchmark}
}
```

---

## Licence & Support

- **Licence**: MIT (see [`LICENSE`](LICENSE))
- **Issues & feature requests**: <https://github.com/dave2k77/lrdbenchmark/issues>
- **Discussions**: <https://github.com/dave2k77/lrdbenchmark/discussions>
- **Documentation**: <https://lrdbenchmark.readthedocs.io/>

Made with care for the time-series community. If you publish results using lrdbenchmark, please share them – the benchmarking suite evolves with real-world feedback.









