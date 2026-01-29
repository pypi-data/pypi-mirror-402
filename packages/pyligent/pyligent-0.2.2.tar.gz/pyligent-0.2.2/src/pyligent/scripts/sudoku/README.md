# Sudoku Scripts overview

All the commands below should be executed from **project root**.

By default, configurations are in `configs/` folder.

## Training

By default, configurations are in `configs/train/sudoku` folder.

```bash
# Use default configs only
uv run src/scripts/sudoku/train.py

# Use default + user overrides
uv run src/scripts/sudoku/train.py --config configs/train/sudoku/user_config.yaml

# Add CLI overrides on top
uv run src/scripts/sudoku/train.py --config configs/train/sudoku/user_config.yaml -v --output_dir ./custom_out
```

<!-- ## Evaluation

By default, configurations are in `configs/eval` folder.

```bash
uv run src/scripts/eval_with_config.py --config configs/eval/gsm8k_eval.yaml
uv run src/scripts/eval_with_config.py --config configs/eval/gsm8k_eval.yaml --checkpoint output/my_model

``` -->
