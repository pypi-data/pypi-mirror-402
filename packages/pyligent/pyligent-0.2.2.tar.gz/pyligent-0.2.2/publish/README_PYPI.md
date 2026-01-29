# Pyligent

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
[![PyPI version](https://badge.fury.io/py/pyligent.svg)](https://badge.fury.io/py/pyligent)

**Pyligent** is a framework for reinforcement learning through search-based reasoning, implementing concepts from [From Reasoning to Super-Intelligence: A Search-Theoretic Perspective](https://arxiv.org/abs/2507.15865).

## Installation

**Note:** Pyligent requires [PyTorch](https://pytorch.org/). Please install the version appropriate for your hardware before installing Pyligent.

### 1. Install PyTorch

**Using `uv`:**

Check the [official guide](https://docs.astral.sh/uv/guides/integration/pytorch/#using-a-pytorch-index)


**For CPU-only environments:**

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**For CUDA 12.8 environments:**

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu128
```

*(For other CUDA versions, please refer to the [PyTorch Get Started](https://pytorch.org/get-started/locally/) guide.)*

### 2. Install Pyligent

Once PyTorch is installed:

```bash
pip install pyligent
```

or

```bash
uv add pyligent
```

## Quick Start

```python
import pyligent

# Your quick start example here
```

## Key Features

- Search-based reasoning for transformer models
- PyTorch-based implementation with PEFT support
- GPU acceleration support (via CUDA-enabled PyTorch)
- Fine-tuning and evaluation pipelines

## Requirements

- Python ≥ 3.13
- PyTorch ≥ 2.8.0 (must be installed manually, see Installation above)

<!-- ## Documentation

For complete documentation, examples, and usage guides, visit our [GitHub repository](https://github.com/crogs-foundation/diligent-learner).

## Citation

If you use Pyligent in your research, please cite:

```bibtex
@article{yourpaper2026,
  title={Your Paper Title},
  author={Your Name},
  journal={arXiv preprint},
  year={2026}
}
```

## Support

- 📝 [Documentation](https://github.com/crogs-foundation/diligent-learner)
- 🐛 [Issue Tracker](https://github.com/crogs-foundation/diligent-learner/issues)
- 💬 [Discussions](https://github.com/crogs-foundation/diligent-learner/discussions) -->
