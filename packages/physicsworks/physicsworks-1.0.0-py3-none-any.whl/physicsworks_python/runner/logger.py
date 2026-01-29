"""
Enhanced logging for debugging runner operations.
"""

from .config import Stage


class DebugLogger:
  """Enhanced logging for debugging"""
  
  def __init__(self, debug_mode: bool = False):
    self.debug_mode = debug_mode
  
  def info(self, message: str, stage: str = "MAIN"):
    print(f"[{stage}] {message}")
  
  def debug(self, message: str, stage: str = "DEBUG"):
    if self.debug_mode:
      print(f"[{stage}] {message}")
  
  def error(self, message: str, stage: str = "ERROR"):
    print(f"[{stage}] ERROR: {message}")
  
  def stage_start(self, stage: Stage):
    print(f"\n{'='*50}")
    print(f"STARTING STAGE: {stage.value.upper()}")
    print(f"{'='*50}")
  
  def stage_skip(self, stage: Stage):
    print(f"\n{'*'*50}")
    print(f"SKIPPING STAGE: {stage.value.upper()}")
    print(f"{'*'*50}")
  
  def stage_complete(self, stage: Stage):
    print(f"\n{'-'*50}")
    print(f"COMPLETED STAGE: {stage.value.upper()}")
    print(f"{'-'*50}")