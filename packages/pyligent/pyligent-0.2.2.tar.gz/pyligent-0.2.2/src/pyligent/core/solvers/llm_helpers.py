from pathlib import Path
from typing import Any, Optional

import pyarrow as pa
import pyarrow.parquet as pq
from datasets import Dataset


class SolverParquetWriter:
    """
    Centralized Parquet writer for solver artifacts.
    """

    def __init__(self, out_dir: Path, *, dataset_dirname: str = "dataset") -> None:
        self._root_dir = Path(out_dir)
        self._dataset_dir = self._root_dir / dataset_dirname

        self.finetunning_snap_dir = self._dataset_dir / "finetunning_snapshots"
        self.inference_snap_dir = self._dataset_dir / "inference_snapshots"
        self.finetunning_snap_dir.mkdir(parents=True, exist_ok=True)
        self.inference_snap_dir.mkdir(parents=True, exist_ok=True)

    def write_finetunning_snapshot(self, ds: Dataset, *, stage: str, t: int) -> Path:
        """
        Persist a HuggingFace Dataset snapshot as parquet.
        """

        path = self.finetunning_snap_dir / f"{stage}_t={int(t):03d}.parquet"

        # Prefer the underlying Arrow table when available (fast + exact).
        table = getattr(getattr(ds, "data", None), "table", None)
        if table is None:
            # Fallback: materialize rows (slower).
            table = pa.Table.from_pylist(ds.to_list())

        return self._write_table(table, path)

    def write_inference_snapshot(
        self,
        rows: list[dict[str, Any]],
        *,
        t: int,
        call_id: int,
        filename_prefix: str = "proposed_actions",
    ) -> Path:
        """
        Persist raw LLM prompts/completions emitted by propose_actions.

        One row is expected per (context_idx, sample_idx).
        """

        path = (
            self.inference_snap_dir
            / f"{filename_prefix}_t={int(t):03d}_call={int(call_id):04d}.parquet"
        )
        table = pa.Table.from_pylist(rows)
        return self._write_table(table, path)

    def _write_table(
        self,
        table: pa.Table,
        path: Path,
        *,
        compression: Optional[str] = "snappy",
    ) -> Path:
        """
        Atomic-ish write: write to a temp file then replace target.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = path.with_suffix(path.suffix + ".tmp")
        if tmp_path.exists():
            tmp_path.unlink()

        pq.write_table(table, tmp_path, compression=compression)
        tmp_path.replace(path)
        return path
