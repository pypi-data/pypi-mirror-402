"""
Server communication utilities for the runner package.
"""

import requests
import json
import os
import base64
import uuid
import threading
from typing import Dict, Optional, Any

from .config import RuntimeAttributes
from .logger import DebugLogger


class ServerCommunicator:
  """Handles all server communication"""
  
  def __init__(self, runtime_attrs: RuntimeAttributes, logger: DebugLogger):
    self.runtime_attrs = runtime_attrs
    self.logger = logger
    self.run_node = None
    self.logs_node = None
    self.solver_config = None
    self.inputs = None
    self.scripts = None
    self.meshes = []
    self.geometries = {}
    self.node_lock = threading.Lock()  # Protect run_node modifications
  
  def set_status(self, status: str, progress: int, status_label: str, extras: Optional[Dict] = None):
    """Update status and communicate with server"""
    with self.node_lock:
      if (status != self.runtime_attrs.status or 
          progress != self.runtime_attrs.progress or 
          status_label != self.runtime_attrs.status_label):
          
          self.runtime_attrs.status = status
          self.runtime_attrs.progress = progress
          self.runtime_attrs.status_label = status_label
          
          self.logger.debug(f"Status: {status} ({progress}%) - {status_label}")
          
          if self.run_node:
            self.run_node['status'] = status
            self.run_node['progress'] = progress
            self.run_node['statusLabel'] = status_label
        
      if status in ['error', 'finished']:
        self.run_node['actions'] = None
        
      try:
        config = getattr(self, 'config', {})
        if config and 'host' in config:
          requests.put(
            f"{config['host']}simulation/run/update/{config['simulation']}/{self.runtime_attrs.run_id}",
            json={'node': self.run_node, 'extras': extras},
            headers={'auth-token': config['token']}
          )
        # print(f"Run node updated: {self.run_node}")
      except Exception as e:
        self.logger.error(f"Failed to update server status: {e}")
  
  def _sync_node_to_server(self):
    """Explicitly sync run_node to server (called after node updates)"""
    try:
      config = getattr(self, 'config', {})
      if config and 'host' in config and self.run_node:
        requests.put(
          f"{config['host']}simulation/run/update/{config['simulation']}/{self.runtime_attrs.run_id}",
          json={'node': self.run_node},
          headers={'auth-token': config['token']}
        )
        self.logger.debug("Node tree synced to server")
    except Exception as e:
      self.logger.error(f"Failed to sync node to server: {e}")
  
  def _update_logs_node(self):
    """Update logs node with current log files"""
    with self.node_lock:
      self.logs_node = next((node for node in self.run_node.get('children', []) if node.get('slug') == 'logs'), None)
      if not self.logs_node:
        return
          
      logs_children = []
      for log_path in self.runtime_attrs.log_paths:
        if log_path not in self.runtime_attrs.logs:
          filename = f"{uuid.uuid1()}.log"
          self.runtime_attrs.logs[log_path] = {"name": filename, "position": 0}
        else:
          filename = self.runtime_attrs.logs[log_path]['name']
          
        # Update file position and upload changes
        config = getattr(self, 'config', {})
        if config:
          metadata = {
            "project": config.get('project'),
            "owner": config.get('owner'),
            "originalname": os.path.basename(log_path),
            "resource": config.get('job'),
            "resourceKind": "Run",
            "simulation": config.get('simulation'),
          }
          self.runtime_attrs.logs[log_path]['position'] = self._add_to_file(
            log_path, self.runtime_attrs.logs[log_path]['position'], filename, metadata
          )
          
        if os.path.exists(log_path):
          log_name = os.path.basename(log_path).split(".")[0]
          logs_children.append({
            'id': filename.split(".")[0],
            'name': log_name,
            'isLog': True,
            'resource': config.get('resource', {}),
            'simulation': config.get('simulation'),
            'status': self.runtime_attrs.logs_status.get(log_name, ''),
            'filename': filename
          })
      
      self.logs_node['children'] = logs_children
      
    # Sync to server immediately - lock ensures we send the latest status
    self._sync_node_to_server()
  
  def _update_plots_node(self):
    """Update plots node with current plot files"""
    with self.node_lock:
      plots_node = next((node for node in self.run_node.get('children', []) if node.get('slug') == 'plots'), None)
      if not plots_node:
        return
          
      plots_children = []
      for plot_path in self.runtime_attrs.plots_paths:
        if plot_path not in self.runtime_attrs.plots:
          filename = f"{uuid.uuid1()}.{plot_path.split('.')[-1]}"
          self.runtime_attrs.plots[plot_path] = {"name": filename, "position": 0}
        else:
          filename = self.runtime_attrs.plots[plot_path]['name']
          
        plot_name = os.path.basename(plot_path).split(".")[0]
        plots_children.append({
          'id': str(uuid.uuid1()),
          'name': plot_name,
          'filename': filename,
          'simulationId': getattr(self, 'config', {}).get('simulation'),
          'isPlot': True,
        })
          
        # Update file position and upload changes
        config = getattr(self, 'config', {})
        if config:
          metadata = {
            "project": config.get('project'),
            "owner": config.get('owner'),
            "originalname": os.path.basename(plot_path),
            "resource": config.get('job'),
            "resourceKind": "Run",
            "simulation": config.get('simulation'),
          }
          self.runtime_attrs.plots[plot_path]['position'] = self._add_to_file(
            plot_path, self.runtime_attrs.plots[plot_path]['position'], filename, metadata
          )
      
      plots_node['children'] = plots_children
      
    # Sync to server immediately - lock ensures we send the latest status
    self._sync_node_to_server()
  
  def _update_media_node(self):
    """Update media node with current media files"""
    with self.node_lock:
      media_node = next((node for node in self.run_node.get('children', []) if node.get('slug') == 'media'), None)
      if not media_node:
        return
          
      media_children = []
      for media_path in self.runtime_attrs.media_paths:
        media_to_upload = self.runtime_attrs.media[media_path]
        media_name = os.path.basename(media_path)
        media_children.append({
          'id': str(uuid.uuid1()),
          'name': media_name,
          'filename': media_to_upload['name'],
          'simulation': getattr(self, 'config', {}).get('simulation'),
          'isMedia': True,
          'mediaType': media_to_upload['name'].split('.')[-1]
        })
          
        # Update file position and upload changes (binary mode for media)
        config = getattr(self, 'config', {})
        if config:
          metadata = {
            "project": config.get('project'),
            "owner": config.get('owner'),
            "originalname": os.path.basename(media_path),
            "resource": config.get('job'),
            "resourceKind": "Run",
            "simulation": config.get('simulation'),
          }
          media_to_upload['position'] = self._add_to_file(
            media_path, media_to_upload['position'], media_to_upload['name'], metadata, is_ascii=False
          )
      media_node['children'] = media_children
      
    # Sync to server immediately - lock ensures we send the latest status
    self._sync_node_to_server()
  
  def _add_to_file(self, path: str, position: int, filename: str, metadata: Dict[str, Any], is_ascii: bool = True) -> int:
    """Add file changes to server (supports both ASCII and binary files)"""
    try:
      changes = self._read_file_changes(path, position, is_ascii)
      if not changes['newContent']:
        return position
        
      # Handle encoding based on file type
      if is_ascii:
        chunk_data = base64.b64encode(changes['newContent'].encode('utf-8')).decode('utf-8')
      else:
        # Binary files are already bytes, encode directly
        chunk_data = base64.b64encode(changes['newContent']).decode('utf-8')
        
      payload = {
        'filename': filename,
        'chunk': chunk_data,
        'isNew': position == 0,
        'metadata': metadata,
        'isAscii': is_ascii
      }
        
      self.runtime_attrs.current_uploads.append(filename)
      config = getattr(self, 'config', {})
      if config and 'host' in config:
        response = requests.post(
          f"{config['host']}storage/append",
          data={'json': json.dumps(payload)},
          headers={'auth-token': config['token'], 'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
      if filename in self.runtime_attrs.current_uploads:
        self.runtime_attrs.current_uploads.remove(filename)
      return changes['lastPosition']
        
    except Exception as e:
      self.logger.error(f"Error adding to file {filename}: {e}")
      if filename in self.runtime_attrs.current_uploads:
        self.runtime_attrs.current_uploads.remove(filename)
      return position
  
  def _read_file_changes(self, path: str, old_position: int, is_ascii: bool = True) -> Dict[str, Any]:
    """Read file changes from a specific position (supports both ASCII and binary files)"""
    try:
      read_mode = 'r' if is_ascii else 'rb'
      with open(path, read_mode) as file:
        file.seek(old_position)
        new_content = file.read()
        new_position = file.tell()
      return {'lastPosition': new_position, 'newContent': new_content}
    except Exception:
      return {'lastPosition': old_position, 'newContent': '' if is_ascii else b''}