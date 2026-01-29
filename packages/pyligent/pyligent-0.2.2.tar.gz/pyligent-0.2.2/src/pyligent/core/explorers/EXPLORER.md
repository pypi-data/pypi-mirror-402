# Tree Search Explorers

This document describes the exploration strategies implemented in `src/architecture/explorer_implementations/` and how they choose which nodes ('frontiers') to expand next.

All explorers implement the same `Explorer` interface and differ only in how `_sample_frontiers(state: PrefixState) -> list[Frontier]` selects/updates `Frontier.requested_children` and removes selected frontiers from `state.stack`.

Key concepts:

- **Frontier**: an expandable node in the prefix-local exploration tree (`Frontier.context`, `Frontier.depth`, `Frontier.children`, `Frontier.requested_children`).
- **Per-prefix stack**: `PrefixState.stack` stores candidate frontiers to expand (ordering matters for deterministic explorers).
- **Capacity**: each frontier has a maximum children limit `c_max(i)` determined by `_max_children_for_frontier(frontier)`.
- **Budget**: explorers typically enforce a per-iteration 'children budget' `U` that is distributed across selected frontiers by setting `requestedrequested_children`.

---

## Linear Explorer

### Overview

The Linear Explorer implements a **pure linear exploration** strategy optimized for parallel branch development:

- At the prefix-root (depth 0) it expands up to the full branching factor.
- For deeper nodes it expands as a linear chain (at most 1 child per node).

This yields 'B parallel chains' instead of a dense tree.

### Behavior summary

- **Capacity policy**:
  - Root: up to `branching_factor` children.
  - Non-root: up to `1` child.
- **Selection policy**:
  - Deterministic, stack-driven (LIFO-like), to advance multiple chains in parallel.

### When to use

- Prefer this explorer for production runs where predictable cost and stable behavior matter.
- Works well when exploration depth is more valuable than branching within a single trajectory.

---

## Dendritic Explorer

Implemented in `dendritic_explorer.py`.

### Overview

`DendriticExplorer` is an adaptive BFS→DFS explorer that **scores** frontiers using a smooth transition function and then allocates the per-iteration children budget `U` deterministically (no sampling).

Important: in the current implementation, `DendriticExplorer` works directly with *log-scores* and does not convert them into probabilities.

### Transition: BFS → DFS

The depth bias coefficient interpolates from BFS-like to DFS-like as the prefix-tree grows.

Definitions:

- `N`: number of discovered nodes in the current prefix-tree (`PrefixState.discovered_nodes + 1`).
- `B`: branching factor (`config.branching_factor`).
- `s`: `sampling_transition_point` (switch around `N ≈ B^s`).
- `h`: sigmoid sharpness.

Formulas:

```text
σ(N) = 1 / (1 + exp(-h · (log_B(N) - s)))
α(N) = α_bfs + (α_dfs - α_bfs) · σ(N)
```

Intuition:

- Early: `α(N)` ≈ `α_bfs` (often negative) ⇒ favors shallower nodes.
- Later: `α(N)` ≈ `α_dfs` (often positive) ⇒ favors deeper nodes.

### Normalized frontier scoring

Each expandable frontier `i` receives a log-score:

- `d`: relative depth from prefix-root (`Frontier.depth`).
- `L`: prefix length reconstructed as `L = len(context) - d`.
- `max_depth_abs`: absolute max depth for this prefix (`PrefixState.max_depth_abs`).
- `max_extra_depth = max(1, max_depth_abs - L)`.
- `max_children = c_max(i)` from capacity mode.
- `gap = max(0, max_children - children)`.

Scaled terms:

```text
depth_scaled = 1 + d / max_extra_depth
gap_scaled   = 1 + gap / max(1, max_children) + ε
```

Log-score:

```text
log(score_i) = α(N) · log(depth_scaled) + β · log(gap_scaled)
```

### Capacity modes (`capacity_mode`)

Controls `c_max(i)`:

- `exponential`:
  - All nodes can have up to `branching_factor` children.
- `linear`:
  - Root can have up to `branching_factor` children, non-root nodes up to `1`.

### Allocation strategies (`sampling_strategy`)

After computing log-scores, Dendritic allocates a total per-iteration children budget `U = sampling_nodes`:

- `prefer_nodes`:
  - Round-robin allocation across high-scoring nodes to improve coverage.
- `prefer_children`:
  - Greedy fill: allocate as much as possible to top-scoring nodes first.

Because allocation is deterministic, setting `seed` does not affect Dendritic selection.

### When to use

- When the goal is adaptive BFS→DFS behavior without adding stochasticity.
- When reproducibility is required but more adaptivity than Linear is desired.

---

## Sampling Explorer

Implemented in `sampling_explorer.py` and built on top of `DendriticExplorer`.

### Overview

`SamplingExplorer` reuses Dendritic's scoring (`_compute_scores`) and expandability rules, but replaces deterministic allocation with **stochastic sampling**:

1. Compute log-scores for expandable frontiers (same as Dendritic).
2. Convert them into probabilities using temperature softmax.
3. Sample which frontiers receive children using a NumPy RNG, while respecting per-node remaining capacity.

### Temperature-softmax

Given log-scores `log(score_i)`, probabilities are computed as:

```text
p_i ∝ exp(log(score_i) / temperature)
```

- High `temperature` ⇒ more uniform sampling.
- Low `temperature` ⇒ more 'argmax-like' sampling.

### Sampling with capacity constraints

Sampling is performed in batches (using `np.random.Generator.choice`) and then capped by each node's remaining capacity:

```text
remaining_capacity(i) = max(0, c_max(i) - children(i))
```

When a node hits capacity, its probability is masked out and sampling continues with renormalization until the total budget `U` is used (or all capacity is exhausted).

### RNG / reproducibility

- `SamplingExplorerConfig.seed` seeds the internal NumPy RNG used for sampling.
- For reproducible runs, set `seed` explicitly.

### When to use

- When stochastic exploration is desired to increase diversity and reduce deterministic bias.
- When tuning exploration behavior via `temperature` is useful (e.g., exploration vs exploitation trade-off).

---

## Practical comparison

| Aspect | Linear Explorer | Dendritic Explorer | Sampling Explorer |
|---|---|---|---|
| Core idea | Parallel linear chains | Deterministic adaptive BFS→DFS | Stochastic adaptive BFS→DFS |
| Scoring | None | Log-score (depth+gap) | Same as Dendritic |
| Uses softmax | No | No | Yes (temperature) |
| Selection/allocation | Deterministic | Deterministic | Random sampling (seeded) |
| Capacity modes | Linear-like | `linear` / `exponential` | `linear` / `exponential` |
| Main tuning knobs | `branching_factor`, `max_depth` | + (`sampling_transition_point`, `h`, `alpha_*`, `beta`, `sampling_nodes`, `sampling_strategy`) | + (`temperature`, `seed`) |
| Best for | Predictable cost | Adaptive but reproducible | Diversity + exploration |

---

## Configuration examples

### DendriticExplorer

```yaml
explorer_type: dendritic

# Base ExplorerConfig
branching_factor: 3
max_depth: 5
leaf_budget_multiplier: 3.0
max_leaf_capability: null
explore_batch_size: 128
seed: 123

# BaseDendriticExplorerConfig
sampling_nodes: 3
capacity_mode: exponential
sampling_transition_point: 2.0
h: 2.0
alpha_bfs: -1.0
alpha_dfs: 1.0
beta: 1.0
epsilon: 1e-6

# DendriticExplorerConfig
sampling_strategy: prefer_nodes
```

### SamplingExplorer

```yaml
explorer_type: sampling

# Base ExplorerConfig
branching_factor: 3
max_depth: 5
leaf_budget_multiplier: 3.0
max_leaf_capability: null
explore_batch_size: 128

# BaseDendriticExplorerConfig
sampling_nodes: 3
capacity_mode: exponential
sampling_transition_point: 2.0
h: 2.0
alpha_bfs: -1.0
alpha_dfs: 1.0
beta: 1.0
epsilon: 1e-6

# SamplingExplorerConfig additions
temperature: 1.0
seed: 42069
```
