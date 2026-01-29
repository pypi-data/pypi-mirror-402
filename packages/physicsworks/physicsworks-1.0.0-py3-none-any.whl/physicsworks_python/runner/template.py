"""
Template functions for PhysicsWorks solver scripts.

This module provides reusable functions for solver templates including:
- Progress tracking
- 3-block execution architecture (pre_remote, remote, post_remote)
"""

import json
import os
import time
from typing import Any, Callable, Dict, Optional

from .interface import append_status, StepStatus


def load_run_inputs(inputs_path: str = "") -> list[Dict[str, Any]]:
  """
  Load runInputs.json file and return the raw list.
  
  Args:
    inputs_path: Optional path to inputs directory (overrides PHYSICSWORKS_INPUTS_DIR env var)
    
  Returns:
    List of input dictionaries from runInputs.json
    
  Raises:
    FileNotFoundError: If runInputs.json is not found
    json.JSONDecodeError: If JSON is invalid
  """
  # Use inputs_path parameter if provided, otherwise fall back to environment variable
  inputs_dir = inputs_path if inputs_path else os.getenv("PHYSICSWORKS_INPUTS_DIR")
  
  if not inputs_dir:
    raise ValueError("No inputs directory specified. Provide inputs_path or set PHYSICSWORKS_INPUTS_DIR environment variable")
  
  run_inputs_file = os.path.join(inputs_dir, "runInputs.json")
  
  with open(run_inputs_file, 'r', encoding='utf-8') as f:
    return json.load(f)


def reconstruct_tree_from_run_inputs(inputs_path: str = "") -> Dict[str, Any]:
  """
  Load and reconstruct nested dictionary tree from runInputs.json file.
  
  Args:
    inputs_path: Optional path to inputs directory (overrides PHYSICSWORKS_INPUTS_DIR env var)
    
  Returns:
    Reconstructed tree dictionary where leaves are the values from run_inputs
    
  Raises:
    FileNotFoundError: If runInputs.json is not found
    json.JSONDecodeError: If JSON is invalid
  """
  run_inputs = load_run_inputs(inputs_path)
  
  tree = {}
  
  for item in run_inputs:
    full_path = item.get('fullPath', '')
    value = item.get('value')
    
    # Split the path by underscore, filtering out empty strings
    # fullPath format: "_slug1_slug2_slug3_..."
    path_parts = [part for part in full_path.split('_') if part]
    
    if not path_parts:
      continue
      
    # Navigate/create the nested structure
    current_level = tree
    
    # Traverse through all parts except the last one
    for part in path_parts[:-1]:
      if part not in current_level:
        current_level[part] = {}
      current_level = current_level[part]
    
    # Set the value at the final key
    final_key = path_parts[-1]
    current_level[final_key] = value
  
  return tree


def get_input_value_by_slug(slug: str, inputs_path: str = "") -> Any:
  """
  Get the value of the first item matching the given slug.
  
  Args:
    slug: The slug to search for
    inputs_path: Optional path to inputs directory (overrides PHYSICSWORKS_INPUTS_DIR env var)
    
  Returns:
    The value of the first matching item, or None if not found
  """
  run_inputs = load_run_inputs(inputs_path)
  
  for item in run_inputs:
    if item.get('slug') == slug:
      return item.get('value')
  
  return None


def get_input_values_by_slug(slug: str, inputs_path: str = "") -> list[Dict[str, Any]]:
  """
  Get all items matching the given slug with their values and full paths.
  
  Args:
    slug: The slug to search for
    inputs_path: Optional path to inputs directory (overrides PHYSICSWORKS_INPUTS_DIR env var)
    
  Returns:
    List of dictionaries with 'value' and 'fullPath' keys for all matching items
  """
  run_inputs = load_run_inputs(inputs_path)
  
  results = []
  for item in run_inputs:
    if item.get('slug') == slug:
      results.append({
        'value': item.get('value'),
        'fullPath': item.get('fullPath')
      })
  
  return results


def get_input_value_by_slugs(slugs: list[str], inputs_path: str = "") -> Dict[str, Any]:
  """
  Get values for multiple slugs as a dictionary.
  
  Args:
    slugs: List of slugs to search for
    inputs_path: Optional path to inputs directory (overrides PHYSICSWORKS_INPUTS_DIR env var)
    
  Returns:
    Dictionary mapping each slug to its first matching value
  """
  run_inputs = load_run_inputs(inputs_path)
  
  result = {}
  slug_set = set(slugs)
  
  for item in run_inputs:
    item_slug = item.get('slug')
    if item_slug in slug_set and item_slug not in result:
      result[item_slug] = item.get('value')
  
  return result


def get_input_values_by_slugs(slugs: list[str], inputs_path: str = "") -> Dict[str, Dict[str, Any]]:
  """
  Get objects (value and fullPath) for multiple slugs as a dictionary.
  
  Args:
    slugs: List of slugs to search for
    inputs_path: Optional path to inputs directory (overrides PHYSICSWORKS_INPUTS_DIR env var)
    
  Returns:
    Dictionary mapping each slug to an object with 'value' and 'fullPath' keys
  """
  run_inputs = load_run_inputs(inputs_path)
  
  result = {}
  slug_set = set(slugs)
  
  for item in run_inputs:
    item_slug = item.get('slug')
    if item_slug in slug_set and item_slug not in result:
      result[item_slug] = {
        'value': item.get('value'),
        'fullPath': item.get('fullPath')
      }
  
  return result


def update_solver_progress(progress: int, message: str = "Running solver", step: str = "solver", status: StepStatus = StepStatus.RUNNING, outputs_path: str = ""):
  """
  Update solver progress (0-100%) to status file.
  
  Args:
    progress: Progress percentage (0-100)
    message: Status message describing current operation
    step: Step name
    status: Step status (StepStatus enum)
    outputs_path: Optional path to outputs directory (overrides PHYSICSWORKS_OUTPUTS_DIR env var)
  """
  
  # Use outputs_path parameter if provided, otherwise fall back to environment variable
  outputs_dir = outputs_path if outputs_path else os.getenv("PHYSICSWORKS_OUTPUTS_DIR")
  
  if not outputs_dir:
    return
  
  # Scale solver progress from 0-100% to 10-90% overall progress
  overall_progress = int(10 + (progress * 0.8))
  
  append_status(outputs_dir, overall_progress, message, step, status)
  print(f"Progress: {progress}% - {message}")


def add_to_simulation_results(name: str, value: Any, outputs_path: str = ""):
  """
  Add a name-value pair to results.csv in the outputs directory.
  
  Creates the file with headers if it doesn't exist, otherwise appends to it.
  
  Args:
    name: The name/label for the result
    value: The value to record
    outputs_path: Optional path to outputs directory (overrides PHYSICSWORKS_OUTPUTS_DIR env var)
    
  Raises:
    ValueError: If no outputs directory is specified
  """
  # Use outputs_path parameter if provided, otherwise fall back to environment variable
  outputs_dir = outputs_path if outputs_path else os.getenv("PHYSICSWORKS_OUTPUTS_DIR")
  
  if not outputs_dir:
    raise ValueError("No outputs directory specified. Provide outputs_path or set PHYSICSWORKS_OUTPUTS_DIR environment variable")
  
  results_file = os.path.join(outputs_dir, "results.csv")
  
  # Check if file exists to determine if we need to write headers
  file_exists = os.path.exists(results_file)
  
  # Open in append mode
  with open(results_file, 'a', encoding='utf-8') as f:
    # Write header if file is new
    if not file_exists:
      f.write("name,value\n")
    
    # Write the data row
    f.write(f"{name},{value}\n")


def replace_placeholders_in_file(file_path: str, replacements: Dict[str, Any]) -> None:
  """
  Replace placeholders in a file with actual values.
  
  Args:
    file_path: Path to the file to modify
    replacements: Dictionary mapping placeholder strings to their replacement values
    
  Example:
    replace_placeholders_in_file(
      "script.py",
      {"{{ITERATIONS}}": 100, "{{STEP_SIZE}}": 0.01}
    )
  """
  # Read the file content
  with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
  
  # Replace all placeholders
  for placeholder, value in replacements.items():
    content = content.replace(placeholder, str(value))
  
  # Write back to file
  with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)


def pre_remote(callback: Optional[Callable[[], None]] = None):
  """
  Pre-Remote Block: Setup and preparation tasks.
  
  This block runs before the main computation and handles:
  - Input file validation
  - Parameter preprocessing
  - Environment setup
  - Data preparation
  
  Args:
    callback: Optional user-defined function to execute custom pre-remote code
  """
  print("=== Pre-Remote Phase ===")
  update_solver_progress(0, "Starting pre-remote phase")
  
  if callback:
    print("Executing user-defined pre-remote code...")
    callback()
  else:
    print("No custom pre-remote code provided")
    time.sleep(0.5)  # Simulate work
  
  update_solver_progress(10, "Pre-remote phase completed")
  print("Pre-remote phase completed")


def remote(callback: Optional[Callable[[], None]] = None):
  """
  Remote Block: Main computation/solver execution.
  
  This is the core processing block that handles:
  - Main solver execution
  - Numerical computations
  - Remote environment execution (Docker, Slurm, etc.)
  - Heavy computational tasks
  
  Args:
    callback: Optional user-defined function to execute custom remote/solver code
  """
  print("=== Remote Phase ===")
  update_solver_progress(15, "Starting remote phase")
  
  if callback:
    print("Executing user-defined remote code...")
    callback()
  else:
    print("No custom remote code provided, running simulation...")
    # Default simulation with progress updates
    phases = [
      ("Initializing computation", 20),
      ("Setting up solver", 30),
      ("Running main solver", 50),
      ("Computing results", 70),
      ("Finalizing computation", 85)
    ]
    
    for phase_name, progress in phases:
      update_solver_progress(progress, phase_name)
      time.sleep(0.5)  # Simulate work
  
  update_solver_progress(90, "Remote phase completed")
  print("Remote phase completed")


def post_remote(callback: Optional[Callable[[], None]] = None):
  """
  Post-Remote Block: Post-processing and cleanup.
  
  This block runs after main computation and handles:
  - Result post-processing
  - Output file generation
  - Data cleanup
  - Report generation
  
  Args:
    callback: Optional user-defined function to execute custom post-remote code
  """
  print("=== Post-Remote Phase ===")
  
  if callback:
    print("Executing user-defined post-remote code...")
    callback()
  else:
    print("No custom post-remote code provided")
    time.sleep(0.5)  # Simulate work
  
  print("Post-remote phase completed")

def run_solver(
  pre_remote_fn: Optional[Callable[[], None]] = None,
  remote_fn: Optional[Callable[[], None]] = None,
  post_remote_fn: Optional[Callable[[], None]] = None
) -> int:
  """
  Execute the 3-block solver architecture.
  
  This is the main entry point that runs all three blocks sequentially:
  1. Pre-Remote (setup and preparation)
  2. Remote (main computation)
  3. Post-Remote (post-processing and cleanup)
  
  Args:
    pre_remote_fn: Optional callback for pre-remote phase
    remote_fn: Optional callback for remote phase
    post_remote_fn: Optional callback for post-remote phase
  
  Returns:
    0 on success, 1 on failure
  """
  print("=== PhysicsWorks Solver Script ===")
  
  try:
    # Block 1: Pre-Remote
    pre_remote(pre_remote_fn)
    
    # Block 2: Remote (Main computation)
    remote(remote_fn)
    
    # Block 3: Post-Remote
    post_remote(post_remote_fn)
    
    print("=== All phases completed successfully ===")
    return 0
    
  except Exception as e:
    print(f"Error in solver execution: {e}")
    # Try to update status, but don't fail if environment variable is not set
    try:
      update_solver_progress(0, f"Error: {e}", status=StepStatus.FAILED)
    except:
      pass
    return 1
