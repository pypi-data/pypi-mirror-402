"""
Core runner implementation for the SPRIME runner package.
"""

import argparse
import json
import os
import sys
import time
import traceback

from .config import Configuration, RuntimeAttributes, Stage
from .logger import DebugLogger
from .server import ServerCommunicator
from .watcher import FileSystemWatcher
from .executor import StageExecutor
from .interface import append_status, StepStatus


class UnifiedRunner:
  """Main runner class that orchestrates the execution"""
  
  def __init__(self, on_abort_callback=None):
    self.config = None
    self.runtime_attrs = RuntimeAttributes()
    self.logger = DebugLogger()
    self.server_comm = ServerCommunicator(self.runtime_attrs, self.logger)
    self.watcher = None  # Will be initialized after config is loaded
    self.executor = None
    self.on_abort_callback = on_abort_callback
    self.main_process = None  # Reference to running subprocess for abort handling
  
  def _parse_arguments(self, args=None) -> Configuration:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
      description="Unified PhysicsWorks Solver Template Runner",
      formatter_class=argparse.RawDescriptionHelpFormatter,
      epilog="""
Examples:
  # Normal execution
  python runner.py --configPath=config.json
  
  # Start from download stage
  python runner.py --configPath=config.json --startingStage=download
  
  # Skip stages for debugging
  python runner.py --configPath=config.json --skipStages=watch,upload
  
  # Debug mode with verbose logging
  python runner.py --configPath=config.json --debugMode
      """
    )
    
    parser.add_argument(
      "--configPath", 
      required=True,
      help="Path to the configuration JSON file"
    )
    
    parser.add_argument(
      "--startingStage", 
      choices=[stage.value for stage in Stage],
      default=Stage.START.value,
      help="Starting stage for execution (default: start)"
    )
    
    parser.add_argument(
      "--skipStages",
      help="Comma-separated list of stages to skip (e.g., watch,upload)"
    )
    
    parser.add_argument(
      "--debugMode",
      action='store_true',
      help="Enable debug mode with verbose logging"
    )
    
    parsed_args = parser.parse_args(args)
    
    # Parse configuration file
    try:
      with open(parsed_args.configPath) as config_file:
        config_dict = json.load(config_file)
    except Exception as e:
      print(f"Error loading configuration file: {e}")
      sys.exit(1)
    
    # Parse skip stages
    skip_stages = []
    if parsed_args.skipStages:
      skip_stage_names = [s.strip() for s in parsed_args.skipStages.split(',')]
      for stage_name in skip_stage_names:
        try:
          skip_stages.append(Stage(stage_name))
        except ValueError:
          print(f"Warning: Unknown stage '{stage_name}' in skipStages")
    
    # Create configuration
    work_dir = config_dict['workDir']
    
    config = Configuration(
      config_path=parsed_args.configPath,
      work_dir=work_dir,
      inputs_path=os.path.join(work_dir, "inputs"),
      outputs_path=os.path.join(work_dir, "outputs"),
      downloads_path=os.path.join(work_dir, "inputs"),
      raw_path=os.path.join(work_dir, "raw"),
      debug_path=os.path.join(work_dir, "debug"),
      scripts_path=os.path.join(work_dir, "scripts"),
      starting_stage=Stage(parsed_args.startingStage),
      skip_stages=skip_stages,
      debug_mode=parsed_args.debugMode,
      config=config_dict
    )
    
    return config
  
  def run(self, args=None):
    """Main execution method"""
    try:
      # 1. Initialize (parse arguments and create directories)
      self.config = self._parse_arguments(args)
      self._create_directories()
      
      self.logger = DebugLogger(self.config.debug_mode)
      self.server_comm = ServerCommunicator(self.runtime_attrs, self.logger)
      # Create watcher with reference to get main process for abort handling
      self.watcher = FileSystemWatcher(
        self.runtime_attrs, 
        self.server_comm, 
        self.logger, 
        on_abort_callback=self.on_abort_callback,
        main_process_ref=lambda: self.main_process
      )
      self.executor = StageExecutor(
        self.config, self.runtime_attrs, self.server_comm, self.watcher, self.logger
      )
      
      self.logger.info(f"Starting unified runner in {self.config.starting_stage.value} mode")
      self.logger.debug(f"Work directory: {self.config.work_dir}")
      
      if self.config.skip_stages:
        self.logger.info(f"Skipping stages: {[s.value for s in self.config.skip_stages]}")
      
      # Initialize status file
      append_status(self.config.outputs_path, 0, "Initializing simulation", "initialization", StepStatus.RUNNING)
      
      # 2. Download inputs from server (0-10%)
      append_status(self.config.outputs_path, 0, "Starting preprocessing", "preprocessing", StepStatus.RUNNING)
      
      if not self.executor.execute_stage(Stage.DOWNLOAD):
        self.logger.error("Download stage failed")
        self.server_comm.set_status("error", 0, "Failed at download")
        append_status(self.config.outputs_path, 0, "Error in preprocessing: Download stage failed", "preprocessing", StepStatus.FAILED)
        return False
      
      append_status(self.config.outputs_path, 10, "Preprocessing complete", "preprocessing", StepStatus.FINISHED)
      
      # 3. Start file watcher on a separate thread
      self._start_file_watcher()
      
      # 4. Run the main.py script under scripts (10-90%)
      append_status(self.config.outputs_path, 10, "Starting solver execution", "solver", StepStatus.RUNNING)
      
      if not self._run_main_script():
        self.logger.error("Main script execution failed")
        self.server_comm.set_status("error", 0, "Failed at script execution")
        append_status(self.config.outputs_path, 0, "Error in solver: Main script execution failed", "solver", StepStatus.FAILED)
        return False
      
      append_status(self.config.outputs_path, 90, "Solver execution complete", "solver", StepStatus.FINISHED)
      
      # Check if aborted before post-processing
      if self.runtime_attrs.aborted:
        self.logger.error("Execution aborted by user")
        return False
      
      # 5. Post processing (90-100%)
      append_status(self.config.outputs_path, 90, "Starting postprocessing", "postprocessing", StepStatus.RUNNING)
      
      if not self.executor.execute_stage(Stage.POSTPROCESS):
        self.logger.error("Post-processing stage failed")
        self.server_comm.set_status("error", 0, "Failed at post-processing")
        append_status(self.config.outputs_path, 0, "Error in postprocessing: Post-processing stage failed", "postprocessing", StepStatus.FAILED)
        return False
      
      append_status(self.config.outputs_path, 100, "Simulation completed successfully", "postprocessing", StepStatus.FINISHED)
      
      # Final status
      append_status(self.config.outputs_path, 100, "Simulation completed successfully")
      
      self.logger.info("Runner execution completed successfully")
      return True
      
    except KeyboardInterrupt:
      self.logger.info("Execution interrupted by user")
      self.server_comm.set_status("error", 0, "Interrupted by user")
      return False
    except Exception as e:
      self.logger.error(f"Runner execution failed: {e}")
      if self.config and self.config.debug_mode:
        traceback.print_exc()
      self.server_comm.set_status("error", 0, "error")
      return False
    finally:
      # Stop file watcher
      if hasattr(self, 'watcher'):
        self.watcher.stop_watching()
  
  def _create_directories(self):
    """Create required directories: debug, inputs, outputs, raw, scripts and outputs subdirectories"""
    directories = [
      self.config.debug_path,
      self.config.inputs_path,
      self.config.outputs_path,
      self.config.raw_path,
      self.config.scripts_path
    ]
    
    # Create output subdirectories
    output_subdirs = ["files", "graphics", "logs", "media", "plots"]
    for subdir in output_subdirs:
      directories.append(os.path.join(self.config.outputs_path, subdir))
    
    for directory in directories:
      try:
        os.makedirs(directory, exist_ok=True)
        self.logger.debug(f"Created directory: {directory}")
      except Exception as e:
        self.logger.error(f"Failed to create directory {directory}: {e}")
        raise
  
  def _start_file_watcher(self):
    """Start file watcher on a separate thread for outputs monitoring and config.json abort signals"""
    try:
      # Watch outputs directory for state.txt changes and file uploads
      watch_paths = [
        self.config.outputs_path,
        os.path.join(self.config.outputs_path, "logs"),
        os.path.join(self.config.outputs_path, "media"), 
        os.path.join(self.config.outputs_path, "plots")
      ]
      
      # Also watch config directory for config.json changes (abort signals)
      config_dir = os.path.dirname(self.config.config_path)
      if config_dir and os.path.isdir(config_dir):
        watch_paths.append(config_dir)
        self.logger.debug(f"Watching config directory for abort signals: {config_dir}")
      
      self.watcher.start_watching(watch_paths)
      self.logger.info("File watcher started on separate thread")
      
    except Exception as e:
      self.logger.error(f"Failed to start file watcher: {e}")
      raise
  
  def _run_main_script(self):
    """Run the main.py script under scripts directory"""
    try:
      main_script_path = os.path.join(self.config.scripts_path, "main.py")
      
      if not os.path.exists(main_script_path):
        self.logger.error(f"Main script not found at {main_script_path}")
        return False
      
      self.logger.info(f"Executing main script: {main_script_path}")
      
      # Set environment variables for the script
      # Convert all paths to use forward slashes for cross-platform compatibility
      script_env = os.environ.copy()
      script_env["PHYSICSWORKS_INPUTS_DIR"] = self.config.inputs_path.replace('\\', '/')
      script_env["PHYSICSWORKS_OUTPUTS_DIR"] = self.config.outputs_path.replace('\\', '/')
      script_env["PHYSICSWORKS_RAW_DIR"] = self.config.raw_path.replace('\\', '/')
      script_env["PHYSICSWORKS_WORK_DIR"] = self.config.work_dir.replace('\\', '/')
      script_env["PHYSICSWORKS_RUN_ID"] = self.runtime_attrs.run_id
      
      # Build command to run main.py with proper arguments
      command = [
        "python",
        main_script_path,
        f"--inputsPath={self.config.inputs_path}",
        f"--outputsPath={self.config.outputs_path}",
        f"--rawPath={self.config.raw_path}"
      ]
      
      # Execute the main script with environment variables
      import subprocess
      self.main_process = subprocess.Popen(
        command, 
        cwd=self.config.scripts_path, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True,
        env=script_env
      )
      
      # Poll the process instead of blocking, checking for abort
      while self.main_process.poll() is None:
        # Check if abort was requested
        if self.runtime_attrs.aborted:
          self.logger.error("Main script execution was aborted")
          self.main_process = None
          return False
        time.sleep(0.5)  # Check every 500ms
      
      # Process completed, get output
      stdout, stderr = self.main_process.communicate()
      result_code = self.main_process.returncode
      self.main_process = None
      
      # Check if aborted during execution (redundant but safe)
      if self.runtime_attrs.aborted:
        self.logger.error("Main script execution was aborted")
        return False
      
      # Create result object for compatibility
      class Result:
        def __init__(self, stdout, stderr, returncode):
          self.stdout = stdout
          self.stderr = stderr
          self.returncode = returncode
      
      result = Result(stdout, stderr, result_code)
      
      # Write logs to debug/main.txt
      log_file_path = os.path.join(self.config.debug_path, "main.txt")
      try:
        with open(log_file_path, 'w') as log_file:
          log_file.write("=== STDOUT ===\n")
          log_file.write(result.stdout)
          log_file.write("\n=== STDERR ===\n")
          log_file.write(result.stderr)
        self.logger.debug(f"Main script logs written to {log_file_path}")
      except Exception as log_error:
        self.logger.error(f"Failed to write main script logs: {log_error}")
      
      if result.returncode == 0:
        self.logger.info("Main script executed successfully")
        self.runtime_attrs.run_succeeded = True
        return True
      else:
        self.logger.error(f"Main script failed with exit code: {result.returncode}")
        self.runtime_attrs.run_succeeded = False
        return False
        
    except Exception as e:
      self.logger.error(f"Error executing main script: {e}")
      return False

def main():
  """Entry point for the runner"""
  runner = UnifiedRunner()
  success = runner.run()
  sys.exit(0 if success else 1)

if __name__ == "__main__":
  main()