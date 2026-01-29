from dataclasses import dataclass
from typing import Optional

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
from datasets import Dataset as HFDataset
from datasets import IterableDataset as HFIterableDataset

GeneralHFDataset = HFDataset | HFIterableDataset


@dataclass(frozen=True)
class DefaultSamplingStrategy:
    """Default pipeline semantics.

    - only_gold=True:  t == t AND gold == True
    - only_gold=False: t == t (gold + explored)
    """

    max_samples: Optional[int] = None
    shuffle: bool = True

    def build_filter(self, *, t: int, only_gold: bool) -> pc.Expression:
        expr = ds.field("t") == pa.scalar(int(t), pa.int32())
        if only_gold:
            expr = expr & (ds.field("gold") == pa.scalar(True))
        return expr

    def postprocess(
        self,
        *,
        ds: HFDataset,
        seed: int,
    ) -> GeneralHFDataset:
        if len(ds) == 0:
            return ds

        # If no max_samples, keep prior semantics.
        if self.max_samples is None:
            if self.shuffle:
                ds = ds.shuffle(seed=seed)
            return ds

        max_samples = int(self.max_samples)
        if max_samples <= 0:
            # Empty iterable dataset is awkward; return empty map-style dataset.
            return ds.select([])

        # If max_samples covers full dataset, keep map-style dataset (Trainer shuffling can handle it).
        if max_samples >= len(ds):
            if self.shuffle:
                ds = ds.shuffle(seed=seed)
            return ds

        # Convert to IterableDataset + shuffle + take(max_samples).
        it = ds.to_iterable_dataset()

        if self.shuffle:
            # Buffer size trade-off: bigger => closer to true uniform shuffle, but more memory.
            # Keep it bounded to avoid huge memory on massive datasets.
            buffer_size = min(len(ds), max(max_samples * 4, max_samples))
            it = it.shuffle(seed=seed, buffer_size=buffer_size)

        it = it.take(max_samples)

        # IMPORTANT!!!!
        try:
            it._pyligent_snapshot_n = max_samples  # ty:ignore[unresolved-attribute]
        except Exception:
            pass

        return it


@dataclass(frozen=True)
class CumulativeUpToTStrategy(DefaultSamplingStrategy):
    """Include all rows with t <= current t (useful for replay strategies)."""

    def build_filter(self, *, t: int, only_gold: bool) -> pc.Expression:
        expr = ds.field("t") <= pa.scalar(int(t), pa.int32())
        if only_gold:
            expr = expr & (ds.field("gold") == pa.scalar(True))
        return expr


@dataclass(frozen=True)
class AllDataStrategy(DefaultSamplingStrategy):
    """Scan all data regardless of t."""

    def build_filter(self, *, t: int, only_gold: bool) -> pc.Expression:
        expr = ds.field("row_id") >= pa.scalar(0, pa.int64())
        if only_gold:
            expr = expr & (ds.field("gold") == pa.scalar(True))
        return expr
