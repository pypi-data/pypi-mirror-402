"""
SPRIME Runner Package

A comprehensive package for running physics simulations with remote and native support.
Provides a clean, modular architecture for solver execution with debugging capabilities.
"""

from .core import UnifiedRunner
from .template import (
    load_run_inputs,
    reconstruct_tree_from_run_inputs,
    get_input_value_by_slug,
    get_input_values_by_slug,
    get_input_value_by_slugs,
    get_input_values_by_slugs,
    update_solver_progress,
    add_to_simulation_results,
    replace_placeholders_in_file,
    pre_remote,
    remote,
    post_remote,
    run_solver
)

__version__ = "1.0.0"
__all__ = [
  # Main runner class
  "UnifiedRunner",
  
  # Template functions for solver scripts (all exported)
  "load_run_inputs",
  "reconstruct_tree_from_run_inputs",
  "get_input_value_by_slug",
  "get_input_values_by_slug",
  "get_input_value_by_slugs",
  "get_input_values_by_slugs",
  "update_solver_progress",
  "add_to_simulation_results",
  "replace_placeholders_in_file",
  "pre_remote",
  "remote",
  "post_remote",
  "run_solver"
]