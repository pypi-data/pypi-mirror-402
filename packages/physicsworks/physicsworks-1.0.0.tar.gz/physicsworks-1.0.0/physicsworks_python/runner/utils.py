"""
Utility functions for the runner package.
Post-processing, file operations, and other helper functions.
"""

import json
import os
import subprocess
import zipfile
import tarfile
import uuid
import base64
from typing import Dict, List, Any

from .config import RuntimeAttributes
from .logger import DebugLogger
from .server import ServerCommunicator


class PostProcessor:
  """Handles post-processing operations"""
  
  def __init__(self, config, runtime_attrs: RuntimeAttributes, 
               server_comm: ServerCommunicator, logger: DebugLogger):
    self.config = config
    self.runtime_attrs = runtime_attrs
    self.server_comm = server_comm
    self.logger = logger
  
  def create_visualization_archives(self):
    """Create visualization archives from available files"""
    try:
      # Create VTP archive if VTP files exist
      vtp_files = []
      for root, dirs, files in os.walk(self.config.outputs_path):
        vtp_files.extend([f for f in files if f.endswith('.vtp')])
      
      if vtp_files:
        vtp_filename = f"vtp{uuid.uuid1()}.tar.gz"
        self.tar_files(self.config.outputs_path, vtp_filename, 'vtp')
        self.logger.debug(f"Created VTP archive: {vtp_filename}")
      
      # Create GLTF archive if GLTF files exist
      files_dir = os.path.join(self.config.outputs_path, "files")
      if os.path.exists(files_dir):
        gltf_files = [f for f in os.listdir(files_dir) if f.endswith('.gltf')]
        if gltf_files:
          gltf_filename = f"gltf{uuid.uuid1()}.tar.gz"
          self.tar_files(files_dir, gltf_filename, 'gltf')
          self.logger.debug(f"Created GLTF archive: {gltf_filename}")
          
    except Exception as e:
      self.logger.error(f"Error creating visualization archives: {e}")
  
  def set_results(self):
    """Set results from results.csv"""
    try:
      results_path = os.path.join(self.config.outputs_path, "results.csv")
      with open(results_path, 'r') as results_file:
        lines = results_file.readlines()
        if len(lines) < 2:
          return
      
      columns = lines[0].strip().split(",")
      values = lines[1].strip().split(",")
      results = []
      
      for i, (col, val) in enumerate(zip(columns, values)):
        val = val.strip()
        try:
          results.append({"name": col, "type": "scalar", "value": int(val)})
        except ValueError:
          try:
            results.append({"name": col, "type": "scalar", "value": float(val)})
          except ValueError:
            if val.lower() in ["true", "false"]:
              results.append({"name": col, "type": "boolean", "value": val.lower() == "true"})
            else:
              results.append({"name": col, "type": "ascii", "value": val})
      
      # Send results to server
      import requests
      config = self.config.config
      requests.put(
        f"{config['host']}simulation/run/patch/{self.runtime_attrs.run_id}",
        json={"results": results},
        headers={'auth-token': config['token']}
      )
      
      self.logger.debug(f"Set {len(results)} results")
      
    except FileNotFoundError:
      self.logger.debug("Results.csv file not found")
    except Exception as e:
      self.logger.error(f"Error setting results: {e}")
  
  def tar_files(self, compress_path: str, compress_filename: str, type_filter: str = None):
    """Create tar.gz archive of files"""
    try:
      full_path = os.path.join(compress_path, compress_filename)
      with tarfile.open(full_path, 'w:gz') as tar:
        for filename in os.listdir(compress_path):
          if not type_filter or filename.endswith(type_filter):
            file_path = os.path.join(compress_path, filename)
            tar.add(file_path, arcname=filename)
        
      self.runtime_attrs.output_files.append(full_path)
        
    except Exception as e:
      self.logger.error(f"Error creating tar file {compress_filename}: {e}")


class FileUploader:
  """Handles file upload operations"""
  
  def __init__(self, config, runtime_attrs: RuntimeAttributes, 
               server_comm: ServerCommunicator, logger: DebugLogger, progress_callback=None):
    self.config = config
    self.runtime_attrs = runtime_attrs
    self.server_comm = server_comm
    self.logger = logger
    self.progress_callback = progress_callback
  
  def upload_file(self, path: str, metadata: Dict[str, Any], filename: str = None):
    """Upload file to server in chunks"""
    try:
      import requests
      chunk_size = 5242880 # = 1024 * 1024 * 5 -> 5MB chunks
      file_size = os.path.getsize(path)
      chunks_number = int(file_size / chunk_size) + 1
      
      if not filename:
        filename = os.path.basename(path)
        if path.endswith(".drc") and path in self.server_comm.geometries:
          filename = self.server_comm.geometries[os.path.basename(path)]
      
      for i in range(chunks_number):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, file_size)
        
        with open(path, 'rb') as file:
          file.seek(start)
          chunk = file.read(end - start)
        
        chunk_bytes = end - start
        
        payload = {
          'filename': filename,
          'fileSize': file_size,
          'chunkIndex': i,
          'chunk': base64.b64encode(chunk).decode('utf-8'),
          'metadata': metadata
        }
        
        config = self.config.config
        response = requests.post(
          f"{config['host']}storage/chunks",
          data={'json': json.dumps(payload)},
          headers={'auth-token': config['token'], 'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        # Call progress callback after successful chunk upload
        if self.progress_callback:
          self.progress_callback(chunk_bytes)
        
    except Exception as e:
      self.logger.error(f"Error uploading file {filename}: {e}")


class ResultsZipper:
  """Handles result packaging and zipping"""
  
  def __init__(self, config, runtime_attrs: RuntimeAttributes, 
               server_comm: ServerCommunicator, logger: DebugLogger):
    self.config = config
    self.runtime_attrs = runtime_attrs
    self.server_comm = server_comm
    self.logger = logger
  
  def zip_results(self):
    """Create result zip files"""
    try:
      package_id = str(uuid.uuid1())
      
      if self.server_comm.solver_config and 'downloadable' in self.server_comm.solver_config:
        basic_paths = self.server_comm.solver_config['downloadable'].get('basic', {})
        
        self.create_zip_file(
          f"{package_id}.zip",
          os.path.join(self.config.outputs_path, "result.zip"),
          basic_paths
        )
                
    except Exception as e:
      self.logger.error(f"Error zipping results: {e}")
  
  def create_zip_file(self, name: str, path: str, paths_schema: Dict[str, Any]):
    """Create a zip file from paths schema"""
    try:
      paths = self.parse_paths(paths_schema)
      
      with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in paths:
          item_path = os.path.join(self.config.work_dir, item.lstrip('/'))
          
          if os.path.isfile(item_path):
            arcname = os.path.relpath(item_path, self.config.work_dir)
            zipf.write(item_path, arcname)
          elif os.path.isdir(item_path):
            for root, dirs, files in os.walk(item_path):
              for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, self.config.work_dir)
                zipf.write(full_path, arcname)
        
      self.runtime_attrs.output_files.append(path)
      self.runtime_attrs.filenames[path] = name
        
    except Exception as e:
      self.logger.error(f"Error creating zip file {name}: {e}")
  
  def parse_paths(self, schema: Dict[str, Any], route: str = '') -> List[str]:
    """Parse paths from schema"""
    paths = []
    
    if isinstance(schema, dict) and schema:
      for key in schema:
        new_route = f"{route}/{key}" if route else f"/{key}"
        paths.extend(self.parse_paths(schema[key], new_route))
    else:
      if schema and route:
        paths.append(route)
    
    return paths