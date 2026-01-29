# How to run scripts

All the commands below should be executed from **project root**.

By default, configurations are in `configs/` folder.

## Training

By default, configurations are in `configs/train` folder.

```bash
# Use default configs only
uv run src/scripts/gsm8k/train.py

# Use default + user overrides
uv run src/scripts/gsm8k/train.py --config user_config.yaml

# Add CLI overrides on top
uv run src/scripts/gsm8k/train.py --config user_config.yaml -v --output_dir ./custom_out
```

## Evaluation

By default, configurations are in `configs/eval` folder.

```bash
uv run src/scripts/eval_with_config.py --config configs/eval/gsm8k_eval.yaml
uv run src/scripts/eval_with_config.py --config configs/eval/gsm8k_eval.yaml --checkpoint output/my_model

```

## Important Notes

### Dataset configs

The `dataset` field in `.yaml` config file should **explicitly** specify dataset type.

Dataset types can be found in `src/scripts/helpers/dataset_config.py`.

```yaml
# Example 1: Basic Dataset
dataset:
  dataset_type: "basic"

# Example 2: Replay Buffer Dataset
dataset:
  dataset_type: "replay_buffer"
  replay_ratio_gold: 2.0
  replay_ratio_exploration: 2.0

```

### Epoch configs

The `training` field in `.yaml` config file contains three types of epoch
configurations:

- `epochs_a`
- `epochs_b`
- `epochs_final`

Each of this filed can be either

1. **Integer**. In this case the provided number of epoch will be used
2. **String** of simple expression of `t` (algorithm step). In this case, the expression will be evaluated and the resulting number of epochs will be used

```yaml
# Example 1: Integer values
training:
  epochs_a: 1
  epochs_b: 2
  epochs_final: 3

# Example 2: String expression
training:
  epochs_a: "max(10-t, 5)"
  epochs_b: "10 if t<=3 else 5"
  epochs_final: "min(t, 10)"

```
