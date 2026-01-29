from pathlib import Path

import torch
from torch.utils.tensorboard import SummaryWriter
from transformers import TrainerCallback


class TensorBoardLogger:
    def __init__(self, log_dir: Path, time_stamp: str) -> None:
        self.writer = SummaryWriter(
            log_dir=str(log_dir / "tensorboard_logs" / time_stamp / "eval_logs")
        )

    def log_phase_data_single(
        self,
        phase: int,
        example_num: int,
        context: str,
        expected: str,
        predicted: str,
        is_valid: bool,
    ) -> None:
        tag = f"phase_{phase}_example_{example_num}"
        text = f"""
        Context: \n {context}
        Expected: \n {expected}
        Predicted: \n {predicted}
        Valid: \n {is_valid}
        """
        self.writer.add_text(tag, text, phase)


class TensorBoardPhaseLogger(TrainerCallback):
    def __init__(self, log_dir: Path, time_stamp: str, initial_phase: str = "A"):
        self.writer = SummaryWriter(
            log_dir=str(log_dir / "tensorboard_logs" / time_stamp / "phases")
        )
        self.phase = initial_phase
        self.phase_num = 0
        self._init_phase_steps()

    def _init_phase_steps(self):
        self.phase_steps = {"SFT-A": 0, "SFT-B": 0, "Final": 0}

    def set_phase(self, phase: str, phase_num: int):
        self.phase_num = phase_num
        self.phase = phase

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return
        logs_updated = False
        for key, value in logs.items():
            if isinstance(value, (int, float)):
                logs_updated = True
                tag = f"{self.phase}_t={self.phase_num}/{key}"
                self.writer.add_scalar(tag, value, self.phase_steps[self.phase])
        if logs_updated:
            self.phase_steps[self.phase] += 1
            self.writer.flush()


class TensorBoardPerformanceLogger(TrainerCallback):
    def __init__(self, log_dir: Path, time_stamp: str):
        self.writer = SummaryWriter(
            log_dir=str(log_dir / "tensorboard_logs" / time_stamp / "performance")
        )
        self.step = 0

    def on_step_end(self, args, state, control, **kwargs):
        if torch.cuda.is_available():
            allocated_memory = torch.cuda.memory_allocated() / 1024**2
            reserved_memory = torch.cuda.memory_reserved() / 1024**2
            utilization = torch.cuda.utilization()
        else:
            allocated_memory = 0
            reserved_memory = 0
            utilization = 0
        data = {"mem_allocated": allocated_memory, "reserved_memory": reserved_memory}
        self.writer.add_scalars("memory", data, self.step)
        self.writer.add_scalar("utilization", utilization, self.step)
        self.writer.flush()
        self.step += 1
