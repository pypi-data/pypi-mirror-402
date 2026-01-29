import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Optional, Protocol

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from datasets import Dataset as HFDataset
from datasets import IterableDataset as HFIterableDataset

from pyligent.core.action import Action, BacktrackAction, DoneAction
from pyligent.core.datasets.sampling_strategies import AllDataStrategy
from pyligent.core.path import PathContext

DiligentDatasetItem = tuple[PathContext, Action]
GeneralHFDataset = HFDataset | HFIterableDataset


class SamplingStrategy(Protocol):
    """Sampling strategy = Parquet predicate + optional HF postprocessing."""

    @property
    def max_samples(self) -> int: ...

    @property
    def shuffle(self) -> bool: ...

    def build_filter(self, *, t: int, only_gold: bool) -> pc.Expression: ...
    def postprocess(self, *, ds: HFDataset, seed: int) -> GeneralHFDataset: ...


@dataclass(frozen=True)
class ParquetDatasetConfig:
    seed: Optional[int] = None
    check_uniqueness: bool = True
    writer_flush_rows: int = 512


_PARQUET_SCHEMA = pa.schema(
    [
        ("row_id", pa.int64()),
        ("t", pa.int32()),
        ("gold", pa.bool_()),
        ("successful", pa.bool_()),
        ("input", pa.large_string()),
        ("prefix", pa.list_(pa.large_string())),
        ("generated", pa.list_(pa.large_string())),
        ("final", pa.large_string()),
        ("bt_reason", pa.large_string()),
    ]
)

_PARTITION_SCHEMA = pa.schema([("t", pa.int32()), ("gold", pa.bool_())])
_PARTITIONING = ds.partitioning(_PARTITION_SCHEMA, flavor="hive")


def _empty_table(columns: Optional[list[str]] = None) -> pa.Table:
    """Return a 0-row Arrow table with the expected schema."""
    if columns is None:
        fields = list(_PARQUET_SCHEMA)
        schema = _PARQUET_SCHEMA
    else:
        name_to_field = {f.name: f for f in _PARQUET_SCHEMA}
        fields = [name_to_field[c] for c in columns if c in name_to_field]
        schema = pa.schema(fields)

    arrays = [pa.array([], type=f.type) for f in fields]
    return pa.Table.from_arrays(arrays, names=[f.name for f in fields], schema=schema)


@dataclass(slots=True)
class _WriterConfig:
    flush_rows: int = 512
    queue_max: int = 50_000


class _AsyncParquetWriter:
    _CMD_KEY = "__cmd__"
    _CMD_FLUSH = "flush"

    def __init__(self, *, root_samples_dir: Path, cfg: _WriterConfig):
        self._root = root_samples_dir
        self._cfg = cfg
        self._q: queue.Queue[dict] = queue.Queue(maxsize=cfg.queue_max)
        self._thread = threading.Thread(
            target=self._run, name="parquet-writer", daemon=True
        )
        self._thread.start()

    def put(self, row: dict) -> None:
        self._q.put(row)

    def put_many(self, rows: Iterable[dict]) -> None:
        # Keeps writer single-threaded but reduces call-site overhead.
        for row in rows:
            self._q.put(row)

    def flush(self) -> None:
        self._q.put({self._CMD_KEY: self._CMD_FLUSH})
        self._q.join()

    def close(self) -> None:
        self.flush()
        self._q.put({})  # sentinel
        self._thread.join(timeout=30)

    def _run(self) -> None:
        buffer: list[dict] = []
        while True:
            row = self._q.get()
            try:
                if not row:
                    if buffer:
                        self._flush(buffer)
                        buffer.clear()
                    return

                cmd = row.get(self._CMD_KEY)
                if cmd == self._CMD_FLUSH:
                    if buffer:
                        self._flush(buffer)
                        buffer.clear()
                    continue

                buffer.append(row)
                if len(buffer) >= self._cfg.flush_rows:
                    self._flush(buffer)
                    buffer.clear()
            finally:
                self._q.task_done()

    def _flush(self, rows: list[dict]) -> None:
        table = pa.Table.from_pylist(rows, schema=_PARQUET_SCHEMA)
        pq.write_to_dataset(
            table=table,
            root_path=str(self._root),
            partition_cols=["t", "gold"],
            existing_data_behavior="overwrite_or_ignore",
        )


@dataclass(frozen=True, slots=True)
class PersistedPair:
    """A persisted pair row (string-based), cheap to load from Parquet."""

    row_id: int
    t: int
    gold: bool
    successful: bool
    input: str
    prefix: list[str]
    generated: list[str]
    final: str
    bt_reason: str


class DiligentDataset:
    """Single dataset store across the whole run (Parquet on disk + async writer)."""

    def __init__(
        self,
        *,
        strategy: SamplingStrategy,
        root_dir: Path,
        config: ParquetDatasetConfig,
    ) -> None:
        self.strategy = strategy
        self.root_dir = Path(root_dir)
        self.config = config
        self.seed = int(config.seed or 0)

        self.dataset_dir = self.root_dir / "dataset" / "samples"
        self.dataset_dir.mkdir(parents=True, exist_ok=True)

        self._writer = _AsyncParquetWriter(
            root_samples_dir=self.dataset_dir,
            cfg=_WriterConfig(flush_rows=int(config.writer_flush_rows)),
        )

        # Global row_id across the whole run.
        self._row_id_lock = threading.Lock()
        self._next_row_id = 0

        # Pre-write dedup.
        self._dedup_lock = threading.Lock()
        self._seen_pair_keys: set[tuple[int, int]] = set()

    def at(self, t: int) -> "DiligentDatasetView":
        # No caching
        return DiligentDatasetView(store=self, t=int(t))

    def __enter__(self) -> "DiligentDataset":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self._writer.close()

    def flush(self) -> None:
        self._writer.flush()

    # ----------------
    # Predicates / dataset opening
    # ----------------

    def _has_parquet_fragments(self) -> bool:
        # Avoid ds.dataset() on empty dir: pyarrow.dataset may error / return no fragments.
        return any(self.dataset_dir.rglob("*.parquet"))

    def _open_dataset(self) -> Optional[ds.Dataset]:
        if not self._has_parquet_fragments():
            return None
        return ds.dataset(
            str(self.dataset_dir), format="parquet", partitioning=_PARTITIONING
        )

    def _predicate(self, *, t: Optional[int], gold: Optional[bool]) -> pc.Expression:
        pred = pc.scalar(True)
        if t is not None:
            pred = pred & (pc.field("t") == int(t))
        if gold is not None:
            pred = pred & (pc.field("gold") == bool(gold))
        return pred

    # ----------------
    # Counting
    # ----------------

    def __len__(self) -> int:
        return self.count_pairs(t=None, gold=None)

    def count_pairs(self, *, t: Optional[int], gold: Optional[bool]) -> int:
        """Count persisted pairs (flushes first to include latest writes)."""
        self.flush()
        dataset = self._open_dataset()
        if dataset is None:
            return 0
        return int(dataset.count_rows(filter=self._predicate(t=t, gold=gold)))

    # ----------------
    # Dedup gate
    # ----------------

    def _pair_key(self, *, ctx: PathContext, action: Action) -> tuple[int, int]:
        return (ctx.hash_value, action.hash_value)

    def _accept_pairs(
        self, pairs: Iterable[DiligentDatasetItem]
    ) -> list[DiligentDatasetItem]:
        """Batch dedup in one lock, preserving order."""
        pairs_list = list(pairs)
        if not self.config.check_uniqueness:
            return pairs_list

        accepted: list[DiligentDatasetItem] = []
        with self._dedup_lock:
            for ctx, action in pairs_list:
                key = self._pair_key(ctx=ctx, action=action)
                if key in self._seen_pair_keys:
                    continue
                self._seen_pair_keys.add(key)
                accepted.append((ctx, action))
        return accepted

    def _reserve_row_ids(self, n: int) -> int:
        """Reserve a contiguous [start, start+n) range, return start."""
        with self._row_id_lock:
            start = self._next_row_id
            self._next_row_id += n
            return start

    # ----------------
    # Writing (public)
    # ----------------

    def add_gold_pairs(
        self, *, t: int, pairs: Iterable[DiligentDatasetItem]
    ) -> list[DiligentDatasetItem]:
        return self._add_pairs(t=int(t), gold=True, pairs=pairs)

    def add_exploration_pairs(
        self, *, t: int, pairs: Iterable[DiligentDatasetItem]
    ) -> list[DiligentDatasetItem]:
        return self._add_pairs(t=int(t), gold=False, pairs=pairs)

    def add_gold_pair(self, *, t: int, pair: DiligentDatasetItem) -> bool:
        return self.add_gold_pairs(t=int(t), pairs=[pair]) == 1

    def add_exploration_pair(self, *, t: int, pair: DiligentDatasetItem) -> bool:
        return self.add_exploration_pairs(t=int(t), pairs=[pair]) == 1

    def _add_pairs(
        self, *, t: int, gold: bool, pairs: Iterable[DiligentDatasetItem]
    ) -> list[DiligentDatasetItem]:
        accepted = self._accept_pairs(pairs)
        if not accepted:
            return []

        start_row_id = self._reserve_row_ids(len(accepted))

        def build_rows() -> Iterator[dict]:
            for offset, (ctx, action) in enumerate(accepted):
                action: Action
                input_str = str(ctx.nodes[0].action) if ctx.nodes else ""

                prefix_nodes: list[str] = []
                generated_nodes: list[str] = []
                for node in ctx.nodes[1:]:
                    if node.appearance_order > 0:
                        generated_nodes.append(str(node.action))
                    else:
                        prefix_nodes.append(str(node.action))

                yield {
                    "row_id": start_row_id + offset,
                    "t": int(t),
                    "gold": bool(gold),
                    "successful": isinstance(action, DoneAction),
                    "input": input_str,
                    "prefix": prefix_nodes,
                    "generated": generated_nodes,
                    "final": str(action),
                    "bt_reason": str(action.reason)
                    if isinstance(action, BacktrackAction) and action.reason
                    else "",
                }

        self._writer.put_many(build_rows())
        return accepted

    # ----------------
    # Reading (persisted)
    # ----------------

    def read_pairs_table(
        self,
        *,
        t: Optional[int],
        gold: Optional[bool],
        columns: Optional[list[str]] = None,
    ) -> pa.Table:
        """Read persisted pairs as an Arrow table (flushes first)."""
        self.flush()
        dataset = self._open_dataset()
        if dataset is None:
            return _empty_table(columns)

        table = dataset.to_table(filter=self._predicate(t=t, gold=gold), columns=columns)
        if table.num_rows == 0:
            return table

        sort_idx = pc.sort_indices(table["row_id"])  # ty:ignore[unresolved-attribute]
        return table.take(sort_idx)

    # ----------------
    # Single-parquet export (no partitions)
    # ----------------

    def export_single_parquet(
        self,
        *,
        output_path: Optional[Path] = None,
        overwrite: bool = True,
        compression: Optional[str] = None,
    ) -> Path:
        """
        Export the entire persisted dataset into a single parquet file (no partitions).

        This is intended to be called once at the end of the pipeline.
        """
        self.flush()

        if output_path is None:
            output_path = self.root_dir / "dataset" / "full_samples.parquet"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.exists() and not overwrite:
            raise FileExistsError(f"File already exists: {output_path}")

        table = self.read_pairs_table(
            t=None,
            gold=None,
            columns=[
                "row_id",
                "t",
                "gold",
                "successful",
                "input",
                "prefix",
                "generated",
                "final",
                "bt_reason",
            ],
        )

        tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        if tmp_path.exists():
            tmp_path.unlink()

        if compression is None:
            pq.write_table(table, tmp_path)
        else:
            pq.write_table(table, tmp_path, compression=compression)

        tmp_path.replace(output_path)
        return output_path

    # ----------------
    # HF materialization
    # ----------------

    def materialize_hf(
        self,
        *,
        t: int,
        only_gold: bool,
        strategy: Optional[SamplingStrategy] = None,
        seed: Optional[int] = None,
    ) -> GeneralHFDataset:
        self.flush()
        strategy = strategy or self.strategy
        seed = self.seed if seed is None else int(seed)

        predicate = strategy.build_filter(t=int(t), only_gold=bool(only_gold))
        table = self.read_pairs_table(
            t=None,  # use strategy predicate instead of (t, gold) helper
            gold=None,
            columns=[
                "row_id",
                "t",
                "gold",
                "successful",
                "input",
                "prefix",
                "generated",
                "final",
                "bt_reason",
            ],
        )
        # Re-filter with strategy predicate on already-loaded table if needed:
        # For large datasets, prefer a dedicated scan that applies `predicate` at dataset level.
        hf = HFDataset(table.filter(predicate))
        return strategy.postprocess(ds=hf, seed=seed)

    def materialize_hf_all(self, *, seed: Optional[int] = None) -> GeneralHFDataset:
        return self.materialize_hf(
            t=0, only_gold=False, strategy=AllDataStrategy(), seed=seed
        )


class DiligentDatasetView:
    """Per-t view used by teacher-building and exploration (requires PathContext objects)."""

    __slots__ = ("store", "t", "_gold_pairs", "_exploration_pairs")

    def __init__(self, *, store: DiligentDataset, t: int) -> None:
        self.store = store
        self.t = int(t)
        self._gold_pairs: list[DiligentDatasetItem] = []
        self._exploration_pairs: list[DiligentDatasetItem] = []

    @property
    def gold_pairs(self) -> list[DiligentDatasetItem]:
        return self._gold_pairs

    @property
    def exploration_pairs(self) -> list[DiligentDatasetItem]:
        return self._exploration_pairs

    @property
    def pairs(self) -> list[DiligentDatasetItem]:
        return self._gold_pairs + self._exploration_pairs

    def __len__(self) -> int:
        return len(self._gold_pairs) + len(self._exploration_pairs)

    def __iter__(self) -> Iterator[DiligentDatasetItem]:
        return iter(self.pairs)

    def add_gold_pairs(self, pairs: Iterable[DiligentDatasetItem]):
        self._gold_pairs.extend(self.store.add_gold_pairs(t=self.t, pairs=pairs))

    def add_exploration_pairs(self, pairs: Iterable[DiligentDatasetItem]):
        self._exploration_pairs.extend(
            self.store.add_exploration_pairs(t=self.t, pairs=pairs)
        )
