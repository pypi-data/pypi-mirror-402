# Sudoku Dataset Generator

Production-ready CLI tool for generating large-scale Sudoku puzzle datasets with solution chains.

## Quick Start

### 1. Create Configuration

Create a YAML configuration file (see `configs/generation/sudoku/default.yaml`):

```yaml
dataset_name: "my_sudoku_dataset"

num_examples:
  easy: 100
  medium: 100
  hard: 100
  expert: 50

min_clues:
  easy: 40
  medium: 32
  hard: 25
  expert: 22

random_seed: 42
require_unique: true
save_path: "./data./sudoku/datasets"
```

### 2. Generate Dataset

```bash
uv run src/scripts/sudoku/generation.py -c configs/generation/sudoku/default.yaml
```

### 3. Output Structure

```bash
datasets/
└── sudoku_benchmark_v1/
    ├── puzzles.bin      # Binary file with all puzzles
    ├── chains.bin       # Binary file with solution chains
    └── index.yaml       # Dataset metadata and statistics
```

## Configuration Reference

### Dataset Settings

| Parameter      | Type   | Description                         |
| -------------- | ------ | ----------------------------------- |
| `dataset_name` | string | Name of dataset (creates directory) |
| `save_path`    | string | Base directory for dataset          |

### Generation Settings

| Parameter        | Type     | Description                      |
| ---------------- | -------- | -------------------------------- |
| `num_examples`   | dict     | Number of puzzles per difficulty |
| `min_clues`      | dict     | Minimum clues per difficulty     |
| `random_seed`    | int/null | Seed for reproducibility         |
| `require_unique` | bool     | Enforce unique solutions         |

### Difficulty Levels

| Level    | Typical Clues | Description                          |
| -------- | ------------- | ------------------------------------ |
| `easy`   | 40-45         | Many clues, straightforward solving  |
| `medium` | 32-39         | Moderate challenge                   |
| `hard`   | 25-31         | Complex strategies required          |
| `expert` | 22-24         | Near-minimal clues, very challenging |

**Note:** 17 is the theoretical minimum for unique solutions in standard Sudoku.

### index.yaml

Metadata and statistics:

```yaml
name: sudoku_benchmark_v1
total_examples: 350
date_created: "2025-12-22T00:30:00"

config:
  dataset_name: sudoku_benchmark_v1
  num_examples:
    easy: 100
    medium: 100
    hard: 100
    expert: 50
  # ... full config

statistics:
  generated: 350
  rejected: 15
  by_difficulty:
    easy:
      generated: 100
      rejected: 2
    # ... per difficulty stats

files:
  puzzles: sudoku_benchmark_v1/puzzles.jsonl
  chains: sudoku_benchmark_v1/chains.jsonl
```
