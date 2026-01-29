"""
Configuration and enums for the runner package.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any


class ExecutionMode(Enum):
  """Execution mode for the solver"""
  REMOTE = "remote"
  NATIVE = "native"


class Stage(Enum):
  """Available execution stages"""
  START = "start"
  INPUT = "input" 
  DOWNLOAD = "download"
  UPLOAD = "upload"
  POSTPROCESS = "postprocess"


@dataclass
class Configuration:
  """Configuration container for the wrapper"""
  config_path: str
  work_dir: str
  inputs_path: str
  outputs_path: str
  downloads_path: str
  raw_path: Optional[str] = None
  debug_path: Optional[str] = None
  scripts_path: Optional[str] = None
  starting_stage: Stage = Stage.START
  skip_stages: List[Stage] = None
  debug_mode: bool = False
  execution_mode: ExecutionMode = ExecutionMode.NATIVE
  config: Dict[str, Any] = None

  def __post_init__(self):
    if self.skip_stages is None:
      self.skip_stages = []


class RuntimeAttributes:
  """Runtime state tracking"""
  def __init__(self):
    self.status = ""
    self.progress = 0
    self.status_label = ""
    self.log_paths = []
    self.logs_status = {}
    self.logs = {}
    self.plots_paths = []
    self.plots = {}
    self.media_paths = []
    self.media = {}
    self.fields = {}
    self.point_clouds = {}
    self.output_files = []
    self.filenames = {}
    self.run_id = ""
    self.compression = {"withCompression": False}
    self.current_uploads = []
    self.run_succeeded = False
    self.aborted = False  # Flag to indicate abort was requested