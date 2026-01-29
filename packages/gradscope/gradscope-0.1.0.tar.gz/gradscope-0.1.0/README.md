# GradScope

GradScope is a small, focused library that watches your training loops and tells you when gradients, metrics, or weight updates go bad.

- 2-line attach for PyTorch and TensorFlow
- Automatic collection of gradients, updates, drift, and metrics
- Rich alerting, summaries, diffing, export, CLI, and web API
- Lightweight FastAPI dashboard for quick inspection of runs
- Git-aware run metadata (commit, branch, dirty state) for reproducibility

For full documentation and examples, see [docs/README.md](docs/README.md).
