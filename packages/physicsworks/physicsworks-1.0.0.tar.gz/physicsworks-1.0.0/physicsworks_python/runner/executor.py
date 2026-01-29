"""
Stage execution logic for the runner package.
"""

import requests
import json
import os
import shutil
import zipfile
import uuid
from pathlib import Path
from typing import Dict, List, Any

from .config import Configuration, RuntimeAttributes, Stage, ExecutionMode
from .logger import DebugLogger
from .server import ServerCommunicator
from .watcher import FileSystemWatcher


class StageExecutor:
  """Executes individual stages with debug support"""
  
  def __init__(self, config: Configuration, runtime_attrs: RuntimeAttributes, 
               server_comm: ServerCommunicator, watcher: FileSystemWatcher, 
               logger: DebugLogger):
    self.config = config
    self.runtime_attrs = runtime_attrs
    self.server_comm = server_comm
    self.watcher = watcher
    self.logger = logger
  
  def should_execute_stage(self, stage: Stage) -> bool:
    """Check if stage should be executed based on starting stage and skip list"""
    stage_order = [Stage.START, Stage.INPUT, Stage.DOWNLOAD, Stage.UPLOAD, Stage.POSTPROCESS]
    starting_index = stage_order.index(self.config.starting_stage)
    current_index = stage_order.index(stage)
    
    return current_index >= starting_index and stage not in self.config.skip_stages
  
  def execute_stage(self, stage: Stage) -> bool:
    """Execute a specific stage"""
    if not self.should_execute_stage(stage):
      self.logger.stage_skip(stage)
      return True
    
    self.logger.stage_start(stage)
    
    try:
      if stage == Stage.INPUT:
        return self._execute_input_stage()
      elif stage == Stage.DOWNLOAD:
        return self._execute_download_stage()
      elif stage == Stage.UPLOAD:
        return self._execute_upload_stage()
      elif stage == Stage.POSTPROCESS:
        return self._execute_postprocess_stage()
      else:
        self.logger.error(f"Unknown stage: {stage}")
        return False
        
    except Exception as e:
      self.logger.error(f"Error in stage {stage.value}: {e}")
      if self.config.debug_mode:
        import traceback
        traceback.print_exc()
      return False
    finally:
      self.logger.stage_complete(stage)
  
  def _execute_input_stage(self) -> bool:
    """Execute input retrieval stage"""
    self.logger.info("Retrieving input data from server")
    self._prepare_location(self.config.inputs_path)
    return self._get_inputs()
  
  def _execute_download_stage(self) -> bool:
    """Execute download stage"""
    self.logger.info("Downloading input files")
    
    # Get input data from server first
    if not self._get_inputs():
      return False
    
    # Create all required directories
    self._prepare_location(self.config.downloads_path)
    self._prepare_location(self.config.inputs_path)
    self._prepare_location(self.config.outputs_path)
    self._prepare_location(self.config.raw_path)
    self._prepare_location(self.config.scripts_path)
    
    # Create output subdirectories: graphics, logs, media, plots
    for subdir in ['graphics', 'logs', 'media', 'plots']:
      self._prepare_location(os.path.join(self.config.outputs_path, subdir))
    
    # Copy state.json from inputs to outputs if it exists
    self._copy_state_json_template()
    
    return self._download_input_files()
  
  def _execute_upload_stage(self) -> bool:
    """Execute upload stage"""
    self.logger.info("Uploading output files")
    return self._upload_output_files()
  
  def _execute_postprocess_stage(self) -> bool:
    """Execute post-processing stage (excluding pvbatch - user-defined)"""
    self.logger.info("Running post-processing")
    
    # Run unified post-processing with configurable features (no pvbatch)
    return self._postprocess_unified()
  
  def _copy_state_json_template(self):
    """Copy state.txt template from inputs to outputs"""
    try:
      state_txt_input = os.path.join(self.config.inputs_path, "state.txt")
      state_txt_output = os.path.join(self.config.outputs_path, "state.txt")
      
      if os.path.exists(state_txt_input):
        shutil.copy2(state_txt_input, state_txt_output)
        self.logger.debug(f"Copied state.txt template from {state_txt_input} to {state_txt_output}")
      else:
        self.logger.debug(f"No state.txt template found at {state_txt_input}, skipping")
        
    except Exception as e:
      self.logger.error(f"Error copying state.txt template: {e}")

  # The rest of the methods follow the same pattern...
  # For brevity, I'll include the essential structure and key methods
  
  def _get_inputs(self) -> bool:
    """Get input data from server"""
    try:
      config = self.config.config
      response = requests.get(
        f"{config['host']}simulation/run_data/read/{config['project']}/{config['simulation']}",
        headers={'auth-token': config['token']}
      )
      
      if response.status_code != 200:
        self.logger.error(f"Failed to get inputs: {response.text}")
        return False
      
      server_data = response.json()
      simulation = server_data.get('simulation')
      
      if not simulation:
        raise Exception("Simulation not found")
      
      # Create and extract run node
      self.server_comm.run_node = requests.put(
        f"{config['host']}simulation/run/update/{config['simulation']}",
        json={},
        headers={'auth-token': config['token']}
      ).json()
      
      self.runtime_attrs.run_id = self.server_comm.run_node['id']
      
      # Update config with resource info
      config['resource'] = {
        'id': self.server_comm.run_node['id'],
        'name': self.server_comm.run_node['name']
      }
      
      with open(self.config.config_path, 'w') as config_file:
        config_file.write(json.dumps(config))
      
      # Process materials, tree, inputs, etc.
      materials = server_data.get('materials', [])
      materials_data = self._process_materials(materials)
      self._dump_file(materials_data, os.path.join(self.config.inputs_path, "variants.json"))
      
      tree = simulation.get('tree', {})
      run_inputs = server_data.get('inputs', {})
      self._dump_file(tree, os.path.join(self.config.inputs_path, "workbench.json"))
      self._dump_file(run_inputs, os.path.join(self.config.inputs_path, "runInputs.json"))
      
      # Extract meshes
      if "meshes" in simulation:
        self.server_comm.meshes = simulation['meshes']
      
      # Write simulation config
      self._dump_file(self.runtime_attrs.compression, os.path.join(self.config.inputs_path, "config.json"))
      
      # Store solver config
      self.server_comm.solver_config = server_data.get('physicsFeature', {}).get('config', {})
      self.server_comm.inputs = server_data.get('physicsFeature', {}).get('inputs', {})
      self.server_comm.scripts = server_data.get('physicsFeature', {}).get('scripts', {})
      
      # Write solver config to file for use by scripts
      self._dump_file(self.server_comm.solver_config, os.path.join(self.config.inputs_path, "solverConfig.json"))
      
      # Detect execution mode
      if 'container' in self.server_comm.solver_config:
        self.config.execution_mode = ExecutionMode.REMOTE
        self.logger.info("Detected Remote execution mode")
      else:
        self.config.execution_mode = ExecutionMode.NATIVE
        self.logger.info("Detected native execution mode")
      
      # Store config reference for server communicator
      self.server_comm.config = config
      
      return True
      
    except Exception as e:
      self.logger.error(f"Error getting inputs: {e}")
      return False
  
  def _process_materials(self, materials: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process materials data"""
    materials_data = {}
    for current in materials:
      composition = current.get('composition', {})
      variant = {key: current[key] for key in current if key != 'composition'}
      properties = variant.get('properties', [])
      
      # Process properties
      for i, prop in enumerate(properties):
        values = prop.get('values', [])
        if prop.get('type') == 'SingleValue' and values:
          properties[i] = {**prop, 'variantId': current.get('id'), 'value': values[0].get('y')}
        else:
          properties[i] = {**prop, 'variantId': current.get('id'), 'values': values}
      
      variant['properties'] = properties
      materials_data[current.get('id')] = {'composition': composition, 'variant': variant}
    
    return materials_data
  
  def _download_input_files(self) -> bool:
    """Download input files"""
    try:
      # Download mesh files
      if hasattr(self.server_comm, 'meshes') and self.server_comm.meshes:
        for mesh in self.server_comm.meshes:
          if 'rawMeshFile' in mesh and 'id' in mesh:
            mesh_ext = mesh['rawMeshFile'].split(".")[-1]
            mesh_path = os.path.join(self.config.downloads_path, f"{mesh['id']}.{mesh_ext}")
            self._download_file(
              f"{self.config.config['host']}storage/runner/{mesh['rawMeshFile']}",
              mesh_path
            )
            self.logger.debug(f"Downloaded mesh file to {mesh_path}")
      
      # Download inputs archive if specified
      if 'inputsArchive' in self.config.config and self.server_comm.inputs:
        inputs_zip_path = os.path.join(self.config.downloads_path, 'inputs.zip')
        self._download_file(
          f"{self.config.config['host']}storage/runner/{self.server_comm.inputs}",
          inputs_zip_path
        )
        
        # Extract inputs archive
        with zipfile.ZipFile(inputs_zip_path, 'r') as zip_ref:
          zip_ref.extractall(self.config.inputs_path)
        
        self.logger.debug("Downloaded and extracted inputs archive")
      
      # Download scripts archive if specified
      if self.server_comm.scripts:
        scripts_zip_path = os.path.join(self.config.downloads_path, 'scripts.zip')
        self._download_file(
          f"{self.config.config['host']}storage/runner/{self.server_comm.scripts}",
          scripts_zip_path
        )
        
        # Extract scripts archive to scripts directory
        with zipfile.ZipFile(scripts_zip_path, 'r') as zip_ref:
          zip_ref.extractall(self.config.scripts_path)
        
        self.logger.debug("Downloaded and extracted scripts archive")
      
      return True
      
    except Exception as e:
      self.logger.error(f"Error downloading input files: {e}")
      return False
  
  # Helper methods
  def _prepare_location(self, path: str):
    """Create directory if it doesn't exist"""
    try:
      Path(path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
      self.logger.error(f"Error creating directory {path}: {e}")
      raise
  
  def _dump_file(self, obj: Any, path: str):
    """Dump object to JSON file"""
    try:
      with open(path, 'w') as file:
        json.dump(obj, file, indent=2)
    except Exception as e:
      self.logger.error(f"Error writing file {path}: {e}")
      raise
  
  def _download_file(self, url: str, file_path: str):
    """Download file from URL"""
    try:
      response = requests.get(url, allow_redirects=True, headers={'auth-token': self.config.config['token']})
      response.raise_for_status()
      
      with open(file_path, 'wb') as file:
        file.write(response.content)
        
    except Exception as e:
      self.logger.error(f"Error downloading file to {file_path}: {e}")
      raise
  
  # Placeholder methods for the remaining functionality
  # These would contain the full implementation from the original wrapper
  
  def _upload_output_files(self) -> bool:
    """Upload output files to server"""
    try:
      from .utils import FileUploader
      
      # Calculate total size of all files to upload
      total_size = sum(os.path.getsize(file_path) for file_path in self.runtime_attrs.output_files)
      uploaded_size = 0
      
      # Format sizes for display
      def format_size(size_bytes):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
          if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
          size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"
      
      # Create progress callback
      def on_chunk_uploaded(chunk_bytes):
        nonlocal uploaded_size
        uploaded_size += chunk_bytes
        # Calculate progress from 92% to 100% based on uploaded size
        progress = int(92 + (uploaded_size / total_size * 8))
        # Cap at 99% - only final status update will set 100%
        if progress >= 100:
          progress = 99
        
        # Set label based on upload completion
        if uploaded_size >= total_size:
          label = "upload complete"
        else:
          label = f"uploading results {format_size(uploaded_size)}/{format_size(total_size)}"
        
        self.server_comm.set_status("running", progress, label)
      
      uploader = FileUploader(self.config, self.runtime_attrs, self.server_comm, self.logger, on_chunk_uploaded)
      
      self.server_comm.set_status("running", 92, f"uploading results {format_size(0)}/{format_size(total_size)}")
      
      for file_path in self.runtime_attrs.output_files:
        self.logger.debug(f"Uploading file: {file_path}")
        
        metadata = {
          "project": self.config.config['project'],
          "owner": self.config.config['owner'],
          "originalname": os.path.basename(file_path),
          "resource": self.config.config['job'],
          "resourceKind": "Run",
          "simulation": self.config.config['simulation'],
        }
        
        if file_path.endswith(".zip"):
          filename = self.runtime_attrs.filenames.get(file_path)
          uploader.upload_file(file_path, metadata, filename)
        else:
          uploader.upload_file(file_path, metadata)
      
      return True
      
    except Exception as e:
      self.logger.error(f"Error uploading files: {e}")
      return False
  
  def _postprocess_unified(self) -> bool:
    """Unified post-processing with configurable features (excluding pvbatch)"""
    try:
      from .utils import PostProcessor, ResultsZipper
      
      post_processor = PostProcessor(self.config, self.runtime_attrs, self.server_comm, self.logger)
      zipper = ResultsZipper(self.config, self.runtime_attrs, self.server_comm, self.logger)
      
      # Set initial progress for post-processing stage
      self.server_comm.set_status("running", 90, "post-processing")
      
      # Set results first (always done)
      post_processor.set_results()
      
      # Note: pvbatch processing should be handled by user-defined scripts
      # not in the post-processing stage
      
      # Create visualization archives based on available files
      post_processor.create_visualization_archives()
      
      # Zip results if downloadable paths are configured
      if self.server_comm.solver_config.get('downloadable'):
        self.server_comm.set_status("running", 90, "zipping results")
        zipper.zip_results()
      
      # Upload all output files
      self._upload_output_files()
      
      # Update downloadables node with results.zip
      self._update_downloadables_node()
      
      # Update graphics node with any visualization data
      self._update_graphics_node()
      
      # Set final status
      if self.runtime_attrs.run_succeeded:
        self.server_comm.set_status("finished", 100, "finished")
      else:
        raise Exception("The run failed")
      
      return True
      
    except Exception as e:
      self.logger.error(f"Error in post-processing: {e}")
      return False

  def _update_graphics_node(self):
    """Update graphics node with visualization data"""
    try:
      graphics_node = next(
        (node for node in self.server_comm.run_node.get('children', []) if node.get('slug') == "graphics"), 
        None
      )
      
      if not graphics_node:
        return
      
      if not graphics_node.get('children'):
        graphics_node['children'] = []
      
      # Check for pvbatch_output.json from pvbatch processing
      output_json_path = os.path.join(self.config.outputs_path, "pvbatch_output.json")
      if os.path.exists(output_json_path):
        self._process_pvbatch_output(graphics_node, output_json_path)
      else:
        # Create basic visualization entries for VTP files
        self._create_basic_visualization_entries(graphics_node)
        
    except Exception as e:
      self.logger.error(f"Error updating graphics node: {e}")
  
  def _update_downloadables_node(self):
    """Update downloadables node with results.zip"""
    try:
      # Find the downloadables node
      downloadables_node = next(
        (node for node in self.server_comm.run_node.get('children', []) if node.get('slug') == 'downloadables'), 
        None
      )
      
      if not downloadables_node:
        self.logger.debug("No downloadables node found, skipping update")
        return
      
      # Find the results.zip filename from uploaded files
      result_zip_name = None
      for file_path in self.runtime_attrs.output_files:
        if file_path.endswith("result.zip"):
          result_zip_name = self.runtime_attrs.filenames.get(file_path)
          break
      
      if not result_zip_name:
        self.logger.debug("No result.zip found, skipping downloadables update")
        return
      
      # Update the downloadables node with the specified structure
      simulation_id = self.config.config['simulation']
      downloadables_node['id'] = str(uuid.uuid1())
      downloadables_node['name'] = 'Downloadables'
      downloadables_node['slug'] = 'downloadables'
      downloadables_node['simulationId'] = simulation_id
      downloadables_node['children'] = [
        {
          'id': str(uuid.uuid1()),
          'name': 'Result.zip',
          'slug': 'result.zip',
          'isFile': True,
          'filename': result_zip_name,
          'simulationId': simulation_id,
          'actions': {
            'type': 'command',
            'list': [{'name': 'Download', 'slug': 'download'}]
          }
        }
      ]
      
      self.logger.debug(f"Updated downloadables node with {result_zip_name}")
        
    except Exception as e:
      self.logger.error(f"Error updating downloadables node: {e}")
  
  def _process_pvbatch_output(self, graphics_node, output_json_path):
    """Process pvbatch pvbatch_output.json and update graphics node"""
    try:
      with open(output_json_path, 'r') as outfile:
        output = json.load(outfile)
      
      # Update plots with CSV data if available
      if 'csv' in output and self.runtime_attrs.plots_paths:
        plots_node = next(
          (node for node in self.server_comm.run_node.get('children', []) if node.get('slug') == 'plots'), 
          None
        )
        if plots_node and plots_node.get('children'):
          for plot in plots_node['children']:
            if plot['name'] in output['csv']:
              plot['columns'] = output['csv'][plot['name']]
      
      # Find the corresponding archive file
      tar_filename = None
      for output_file in self.runtime_attrs.output_files:
        if 'gltf' in output_file or 'pvbatch' in output_file:
          tar_filename = os.path.basename(output_file)
          break
      
      if tar_filename:
        # Prepare metadata
        metadata = {'times': {}, 'regions': {}}
        if 'bBox' in output:
          metadata['bBox'] = output['bBox']
        
        items = output.get('items', [])
        for output_item in items:
          time_index = str(output_item['timeIndex'])
          metadata['times'][time_index] = output_item['time']
          
          region = output_item['region']
          field = output_item['field']
          if region not in metadata['regions']:
            metadata['regions'][region] = [field]
          else:
            metadata['regions'][region] = list(set([field] + metadata['regions'][region]))
        
        # Add graphics entry
        gltf_id = str(uuid.uuid1())
        graphics_node['children'].append({
          'id': gltf_id,
          'name': output.get('type', 'Visualization'),
          'slug': output.get('slug', 'visualization'),
          'simulationId': self.config.config['simulation'],
          'value': {
            'id': str(uuid.uuid1()),
            'title': output.get('type', 'Visualization'),
            'slug': output.get('slug', 'visualization'),
            'simulationFields': True,
            'data': {
              'filename': tar_filename,
              'items': items,
              'metadata': metadata
            }
          }
        })
        
        # Update simulation with gltf ID reference
        # This allows the workbench to find the GLTF node for rendering
        self.server_comm.set_status(
          self.server_comm.runtime_attrs.status,
          self.server_comm.runtime_attrs.progress,
          self.server_comm.runtime_attrs.status_label,
          extras={'gltf': gltf_id}
        )
        
    except Exception as e:
      self.logger.error(f"Error processing pvbatch output: {e}")
  
  def _create_basic_visualization_entries(self, graphics_node):
    """Create basic visualization entries for VTP files"""
    try:
      # Look for VTP archive
      vtp_archive = None
      for output_file in self.runtime_attrs.output_files:
        if 'vtp' in output_file and output_file.endswith('.tar.gz'):
          vtp_archive = os.path.basename(output_file)
          break
      
      if vtp_archive:
        vtp_metadata = {
          "id": str(uuid.uuid1()),
          "type": "VTP",
          "slug": "vtp",
        }
        
        graphics_node['children'].append({
          'id': vtp_metadata["id"],
          'name': vtp_metadata['type'],
          'slug': vtp_metadata['slug'],
          'simulationId': self.config.config['simulation'],
          'value': {
            'id': str(uuid.uuid1()),
            'title': vtp_metadata['type'],
            'slug': vtp_metadata['slug'],
            'simulationFields': True,
            'data': {
              'filename': vtp_archive
            }
          }
        })
        
    except Exception as e:
      self.logger.error(f"Error creating basic visualization entries: {e}")