"""
File watching utilities for monitoring solver execution.
"""

import os
import json
import sys
import threading
import time
import stat
import base64
from typing import List, Optional
import uuid

from .server import ServerCommunicator
from .config import RuntimeAttributes
from .logger import DebugLogger


class FileWatcher:
  """Monitors files and directories for changes during solver execution"""
  
  def __init__(self, runtime_attrs: RuntimeAttributes, server_communicator: ServerCommunicator, 
               logger: DebugLogger, poll_interval: float = 1.0, on_abort_callback=None, main_process_ref=None):
    self.runtime_attrs = runtime_attrs
    self.server_communicator = server_communicator
    self.logger = logger
    self.watching = False
    self.watch_thread = None
    self.file_states = {}  # Track file modification times
    self.watch_directories = []
    self.poll_interval = poll_interval  # Configurable polling interval
    self.upload_threads = set()  # Track active upload threads
    self.upload_lock = threading.Lock()  # Protect upload_threads set
    self.on_abort_callback = on_abort_callback  # Optional callback for custom abort handling
    self.main_process_ref = main_process_ref  # Callable to get reference to main process
  
  def add_watch_directory(self, directory: str):
    """Add a directory to watch"""
    if os.path.isdir(directory):
      self.watch_directories.append(directory)
      
  def start_watching(self):
    """Start the file watching thread"""
    self.watching = True
    self.watch_thread = threading.Thread(target=self._watch_loop, daemon=False)
    self.watch_thread.start()
  
  def stop_watching(self):
    """Stop the file watching thread and wait for pending operations"""
    self.watching = False
    if self.watch_thread:
      self.logger.debug("Waiting for file watcher to complete pending operations...")
      self.watch_thread.join(timeout=None)  # Wait indefinitely for completion
      
      # Wait for all upload threads to complete
      with self.upload_lock:
        pending_uploads = list(self.upload_threads)
      
      if pending_uploads:
        self.logger.debug(f"Waiting for {len(pending_uploads)} upload thread(s) to complete...")
        for thread in pending_uploads:
          thread.join(timeout=30)  # 30 second timeout per upload
          if thread.is_alive():
            self.logger.warning(f"Upload thread {thread.name} did not complete in time")
      
      self.logger.debug("File watcher stopped successfully")
      
  def _watch_loop(self):
    """Main watching loop using polling"""
    while self.watching:
      try:
        self._check_files()
        time.sleep(self.poll_interval)  # Configurable poll interval
      except Exception as e:
        self.logger.error(f"Error in file watcher: {e}")
    
  def _check_files(self):
    """Check for file changes in watched directories"""
    for directory in self.watch_directories:
      if not os.path.isdir(directory):
        continue
      
      # Check all files recursively
      for root, dirs, files in os.walk(directory):
        for file in files:
          filepath = os.path.join(root, file)
          try:
            stat_info = os.stat(filepath)
            current_mtime = stat_info.st_mtime
            
            # Check if file is new or modified
            if filepath not in self.file_states:
              self.file_states[filepath] = current_mtime
              self._handle_file_event(filepath, 'created')
            elif self.file_states[filepath] != current_mtime:
              self.file_states[filepath] = current_mtime
              self._handle_file_event(filepath, 'modified')
          except (OSError, IOError):
            # File might have been deleted or is inaccessible
            continue
      
  def _handle_file_event(self, filepath: str, event_type: str):
    """Handle file events"""
    filename = os.path.basename(filepath)
    normalized_path = filepath.replace('\\', '/')
    
    print(f"File {event_type}: {filepath}")
    if filename == 'state.txt':
      self._handle_state_txt(filepath)
    elif filename == 'config.json':
      self._handle_config_json(filepath)
    elif '/outputs/logs/' in normalized_path or '\\outputs\\logs\\' in filepath:
      self._handle_log_file(filepath)
    elif '/outputs/media/' in normalized_path or '\\outputs\\media\\' in filepath:
      self._handle_media_file(filepath)
    elif '/outputs/plots/' in normalized_path or '\\outputs\\plots\\' in filepath:
      self._handle_plot_file(filepath)
      
  def _handle_config_json(self, filepath: str):
    """Handle config.json file changes"""
    try:
      with open(filepath, 'r', encoding='utf-8') as f:
        config = json.load(f)
      
      if 'abort' in config and config['abort']:
        self.logger.error("Aborted by user")
        
        # Set abort flag
        self.runtime_attrs.aborted = True
        
        # Set status to error
        self.server_communicator.set_status('error', 0, 'Aborted by user')
        
        # Call custom abort callback if provided (for remote job cancellation, cleanup, etc.)
        if self.on_abort_callback:
          try:
            self.logger.debug("Calling custom abort callback...")
            self.on_abort_callback(config)
          except Exception as e:
            self.logger.error(f"Error in abort callback: {e}")
        
        # Kill the running main process if it exists
        if self.main_process_ref:
          try:
            main_process = self.main_process_ref()
            if main_process and main_process.poll() is None:  # Process is still running
              self.logger.info("Terminating running solver process...")
              main_process.terminate()
              # Give it 5 seconds to terminate gracefully
              try:
                main_process.wait(timeout=5)
                self.logger.info("Solver process terminated")
              except:
                # Force kill if it doesn't terminate
                self.logger.warning("Force killing solver process...")
                main_process.kill()
                main_process.wait()
          except Exception as e:
            self.logger.error(f"Error terminating main process: {e}")
        
        # Stop watching to prevent further processing
        self.watching = False
    
    except (json.JSONDecodeError, IOError) as e:
      self.logger.error(f"Error reading config.json: {e}")
      
  def _handle_state_txt(self, filepath: str):
    """Handle state.txt file changes - parses CSV format: date & time,progress,text,step,status"""
    try:
      with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
      
      if not lines:
        return
      
      # Get the last non-empty line as the current status
      last_line = None
      for line in reversed(lines):
        stripped_line = line.strip()
        if stripped_line:
          last_line = stripped_line
          break
      
      if last_line:
        # Parse CSV format: date & time,progress(number),text,step,status
        parts = last_line.split(',')
        
        if len(parts) >= 3:
          # Extract fields
          # parts[0] = date & time
          progress_str = parts[1].strip()
          text = parts[2].strip()
          step = parts[3].strip() if len(parts) > 3 else ""
          status = parts[4].strip() if len(parts) > 4 else "running"
          
          # Parse progress as integer (use local variable)
          progress = self.runtime_attrs.progress  # Default to current value
          try:
            progress = int(progress_str)
            progress = max(0, min(100, progress))
          except ValueError:
            # If progress can't be parsed, keep current value
            pass
          
          # Map status string to StepStatus enum values (use local variable)
          status_lower = status.lower()
          if status_lower == 'finished':
            mapped_status = "finished"
          elif status_lower == 'failed':
            mapped_status = "error"  # Map 'failed' to 'error' for runtime_attrs
          elif status_lower == 'running':
            mapped_status = "running"
          elif status_lower == 'pending':
            mapped_status = "pending"
          else:
            # Default to running if status is unclear
            mapped_status = "running"
          
          self.logger.debug(f"Status updated from state file: progress={progress}%, status={mapped_status}, text={text}, step={step}")
          
          # Send status update to server - this will update runtime_attrs if values changed
          self.server_communicator.set_status(
            mapped_status,
            progress,
            text
          )
        else:
          self.logger.warning(f"Invalid state.txt format: {last_line}")
      
    except IOError as e:
      self.logger.error(f"Error reading state.txt: {e}")
      
  def _handle_log_file(self, filepath: str):
    """Handle log file changes"""
    try:
      if filepath not in self.runtime_attrs.log_paths:
        self.runtime_attrs.log_paths.append(filepath)
      
      # For log files, we store metadata rather than content due to size
      # The actual file upload will be handled by the server communicator
      file_stat = os.stat(filepath)
      if filepath not in self.runtime_attrs.logs:
        self.runtime_attrs.logs[filepath] = {
          'size': file_stat.st_size,
          'modified': file_stat.st_mtime,
          'path': filepath,
          'name': f"{uuid.uuid1()}.log",
          'position': 0
        }
      else:
        # Update metadata for existing entry
        self.runtime_attrs.logs[filepath]['size'] = file_stat.st_size
        self.runtime_attrs.logs[filepath]['modified'] = file_stat.st_mtime
      
      # Defer update to avoid blocking the poll loop
      # Update will be called in separate thread via threading.Thread
      thread = threading.Thread(target=self._upload_wrapper, args=(self.server_communicator._update_logs_node,), daemon=False)
      with self.upload_lock:
        self.upload_threads.add(thread)
      thread.start()
        
    except IOError as e:
      self.logger.error(f"Error processing log file {filepath}: {e}")
      
  def _handle_plot_file(self, filepath: str):
    """Handle plot file changes"""
    try:
      if filepath not in self.runtime_attrs.plots_paths:
        self.runtime_attrs.plots_paths.append(filepath)
      
      # For plot files, we store metadata rather than content due to size
      # The actual file upload will be handled by the server communicator
      file_stat = os.stat(filepath)
      if filepath not in self.runtime_attrs.plots:
        self.runtime_attrs.plots[filepath] = {
          'size': file_stat.st_size,
          'modified': file_stat.st_mtime,
          'path': filepath,
          'name': f"{uuid.uuid1()}.{filepath.split('.')[-1]}",
          'position': 0
        }
      else:
        # Update metadata for existing entry
        self.runtime_attrs.plots[filepath]['size'] = file_stat.st_size
        self.runtime_attrs.plots[filepath]['modified'] = file_stat.st_mtime
      
      # Defer update to avoid blocking the poll loop
      # Update will be called in separate thread via threading.Thread
      thread = threading.Thread(target=self._upload_wrapper, args=(self.server_communicator._update_plots_node,), daemon=False)
      with self.upload_lock:
        self.upload_threads.add(thread)
      thread.start()
        
    except IOError as e:
      self.logger.error(f"Error processing plot file {filepath}: {e}")
  
  def _upload_wrapper(self, upload_func):
    """Wrapper to track upload thread lifecycle"""
    try:
      upload_func()
    finally:
      # Remove thread from tracking set when done
      with self.upload_lock:
        self.upload_threads.discard(threading.current_thread())
  
  def _handle_media_file(self, filepath: str):
    """Handle media file changes (binary files)"""
    try:
      if filepath not in self.runtime_attrs.media_paths:
        self.runtime_attrs.media_paths.append(filepath)
      
      # For media files, we store metadata rather than content due to size
      # The actual file upload will be handled by the server communicator
      file_stat = os.stat(filepath)
      if filepath not in self.runtime_attrs.media:
        self.runtime_attrs.media[filepath] = {
          'size': file_stat.st_size,
          'modified': file_stat.st_mtime,
          'path': filepath,
          'name': f"{uuid.uuid1()}.{filepath.split('.')[-1]}",
          'position': 0
        }
      else:
        # Update metadata for existing entry
        self.runtime_attrs.media[filepath]['size'] = file_stat.st_size
        self.runtime_attrs.media[filepath]['modified'] = file_stat.st_mtime
      
      # Defer update to avoid blocking the poll loop
      # Update will be called in separate thread via threading.Thread
      thread = threading.Thread(target=self._upload_wrapper, args=(self.server_communicator._update_media_node,), daemon=False)
      with self.upload_lock:
        self.upload_threads.add(thread)
      thread.start()
        
    except IOError as e:
      self.logger.error(f"Error processing media file {filepath}: {e}")


class FileSystemWatcher:
  """Legacy compatibility wrapper for FileWatcher"""
  
  def __init__(self, runtime_attrs: RuntimeAttributes, server_communicator: ServerCommunicator, 
               logger: DebugLogger, on_abort_callback=None, main_process_ref=None):
    self.watcher = FileWatcher(runtime_attrs, server_communicator, logger, 
                               on_abort_callback=on_abort_callback, main_process_ref=main_process_ref)
  
  def start_watching(self, directories: List[str]):
    """Start watching directories using built-in polling"""
    for directory in directories:
      self.watcher.add_watch_directory(directory)
    self.watcher.start_watching()
  
  def stop_watching(self):
    """Stop watching directories"""
    self.watcher.stop_watching()
  