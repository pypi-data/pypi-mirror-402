"""
Interface utilities for status tracking and progress reporting.
"""

import os
from datetime import datetime
from enum import Enum


class StepStatus(Enum):
  """Status values for execution steps"""
  PENDING = "pending"
  RUNNING = "running"
  FINISHED = "finished"
  FAILED = "failed"


def append_status(outputs_dir: str, progress: int, message: str, step: str = "", status: StepStatus = StepStatus.RUNNING):
  """
  Append status update to state.txt file.
  
  Writes a CSV-formatted line to state.txt with the format:
  timestamp,progress,message,step,status
  
  Args:
    outputs_dir: Path to outputs directory
    progress: Progress percentage (0-100)
    message: Status message
    step: Step name (optional)
    status: Step status enum value
  """
  state_file = os.path.join(outputs_dir, "state.txt")
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  
  # Convert enum to string value
  status_str = status.value if isinstance(status, StepStatus) else str(status)
  
  with open(state_file, "a", encoding="utf-8") as f:
    f.write(f"{timestamp},{progress},{message},{step},{status_str}\n")
