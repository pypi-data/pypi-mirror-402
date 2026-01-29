# PhysicsWorks Python Package

A comprehensive Python package for running physics simulations with remote and native support, providing server communication, file management, and real-time monitoring capabilities for the PhysicsWorks platform.

## Installation

### Install from PyPI

```bash
pip install physicsworks-python
```

### Install Manually from Source

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sprime-common/python
   ```

2. **Install in development mode** (recommended for development):
   ```bash
   pip install -e .
   ```

3. **Or build and install from wheel**:
   ```bash
   # Build the package
   python setup.py sdist bdist_wheel
   
   # Install from the built wheel
   pip install dist/physicsworks_python-<version>-py3-none-any.whl
   ```

4. **Or install directly**:
   ```bash
   python setup.py install
   ```

### Dependencies

The package requires:
- Python >= 3.6
- pymongo
- python-socketio
- asyncio-nats-streaming
- PyJWT
- requests
- PyYAML

## Package Overview

The PhysicsWorks Python package provides tools for:

- **Runner Framework**: Execute physics simulations with file monitoring and server communication
- **Event System**: NATS-based event publishing and listening
- **Middleware**: Authentication, authorization, and access control helpers
- **Wrappers**: Helper functions for common platform operations

## Runner Package Usage

The runner package is the core component for executing simulations and managing their lifecycle.

### Quick Start

```python
from physicsworks_python.runner import run_solver

# Basic usage - automatically parses command line arguments
success = run_solver()

# With specific parameters
success = run_solver(
    config_path="config.json",
    debug_mode=True,
    skip_stages="upload"
)
```

**Important**: When calling `run_solver()`, the runner expects a script named `main.py` to be present under the `./scripts` directory. This script can either:
- Already exist in the `./scripts` directory before running
- Be downloaded automatically from the server using information in `config.json` (via `scriptsArchive` or `mainScript` fields)

### Command Line Usage

```bash
# Basic execution
python -m physicsworks_python.runner --configPath=config.json

# Start from specific stage
python -m physicsworks_python.runner --configPath=config.json --startingStage=download

# Skip certain stages
python -m physicsworks_python.runner --configPath=config.json --skipStages=upload,watch

# Debug mode with verbose logging
python -m physicsworks_python.runner --configPath=config.json --debugMode
```

### Configuration File

The runner requires a JSON configuration file with the following structure:

```json
{
  "workDir": "/path/to/work/directory",
  "host": "https://api.physicsworks.io/",
  "token": "your_auth_token",
  "project": "project_id",
  "simulation": "simulation_id",
  "job": "job_id",
  "owner": "user_id",
  "scriptsArchive": "scripts.zip",
  "inputsArchive": "inputs.zip",
  "mainScript": "main.py"
}
```

### Workflow Stages

The runner executes simulations in 5 stages:

1. **Initialization**: Parse arguments and create directory structure
   - `debug/` - Debug logs
   - `inputs/` - Input files
   - `outputs/` - All output files with subdirectories:
     - `outputs/graphics/` - Visualization files
     - `outputs/logs/` - Log files
     - `outputs/media/` - Media files (videos, images, PDFs)
     - `outputs/plots/` - Plot files and charts
   - `raw/` - Raw data (meshes, etc.)
   - `scripts/` - User scripts including main.py

2. **Download**: Fetch inputs from server
   - Downloads configuration, materials, and simulation tree
   - Downloads mesh files to `raw/`
   - Extracts input and script archives

3. **File Watching**: Monitor outputs in real-time (parallel thread)
   - Watches for changes in `outputs/` directory
   - Automatically uploads new files
   - Monitors `state.txt` for progress updates

4. **Script Execution**: Run your main.py script
   - Expects `scripts/main.py` to exist (either pre-existing or downloaded)
   - Executes with standard arguments: `--inputsPath`, `--outputsPath`, `--rawPath`

5. **Post-processing**: Finalize and upload results
   - Zip results for download
   - Upload visualization data
   - Set final status

### Writing Your Simulation Script

Your `main.py` should accept standard arguments and update status via `state.txt`:

```python
import argparse
from pathlib import Path

def update_status(outputs_path, status_message):
    """Append status message to state file"""
    with open(Path(outputs_path) / "state.txt", 'a') as f:
        f.write(f"{status_message}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--inputsPath', required=True)
    parser.add_argument('--outputsPath', required=True)
    parser.add_argument('--rawPath', required=True)
    args = parser.parse_args()
    
    # Update progress
    update_status(args.outputsPath, "Initializing simulation")
    
    # Your simulation code here
    # ...
    
    update_status(args.outputsPath, "Processing - 50% complete")
    
    # More simulation work
    # ...
    
    update_status(args.outputsPath, "Simulation completed successfully - 100%")
    
    # Write outputs to appropriate directories:
    # - Logs → outputs/logs/
    # - Media → outputs/media/
    # - Plots → outputs/plots/
    # - Graphics → outputs/graphics/

if __name__ == '__main__':
    main()
```

### Status Updates

The `state.txt` file is text-based. Each line represents a status update, and the **last line** is the current status. The runner automatically detects:

- **Progress percentages**: "50%", "25 percent"
- **Completion keywords**: "finished", "completed", "done", "success"
- **Error keywords**: "error", "failed", "abort", "crash"

### Server API Communication

You can make direct server API calls from your scripts:

```python
import requests
import json

config = json.load(open('config.json'))

# Get simulation data
response = requests.get(
    f"{config['host']}simulation/run_data/read/{config['project']}/{config['simulation']}",
    headers={'auth-token': config['token']}
)
simulation_data = response.json()

# Update run status
run_node = {"status": "running", "progress": 75, "statusLabel": "Processing"}
requests.put(
    f"{config['host']}simulation/run/update/{config['simulation']}/{run_id}",
    json={'node': run_node},
    headers={'auth-token': config['token']}
)

# Upload results
results = [
    {"name": "temperature_max", "type": "scalar", "value": 273.15},
    {"name": "converged", "type": "boolean", "value": True}
]
requests.put(
    f"{config['host']}simulation/run/patch/{run_id}",
    json={"results": results},
    headers={'auth-token': config['token']}
)
```

### File Upload

Upload files in chunks for large files:

```python
import base64

def upload_file_chunked(file_path, filename, metadata, config):
    """Upload large files in chunks"""
    chunk_size = 5 * 1024 * 1024  # 5MB chunks
    file_size = os.path.getsize(file_path)
    chunks_number = int(file_size / chunk_size) + 1

    for i in range(chunks_number):
        start = i * chunk_size
        end = min((i + 1) * chunk_size, file_size)

        with open(file_path, 'rb') as file:
            file.seek(start)
            chunk = file.read(end - start)

        payload = {
            'filename': filename,
            'fileSize': file_size,
            'chunkIndex': i,
            'chunk': base64.b64encode(chunk).decode('utf-8'),
            'metadata': metadata
        }

        response = requests.post(
            f"{config['host']}storage/chunks",
            data={'json': json.dumps(payload)},
            headers={'auth-token': config['token']}
        )

metadata = {
    "project": config['project'],
    "owner": config['owner'],
    "originalname": "results.vtk",
    "resource": config['job'],
    "resourceKind": "Run",
    "simulation": config['simulation']
}
upload_file_chunked("outputs/results.vtk", "results.vtk", metadata, config)
```

## Event System

Subscribe to and publish events via NATS:

```python
from physicsworks_python.events import JobCreatedPublisher, JobCreatedListener

# Publishing events
publisher = JobCreatedPublisher(nats_client)
await publisher.publish({
    'id': 'job_123',
    'status': 'created'
})

# Listening to events
class MyJobListener(JobCreatedListener):
    async def on_message(self, data, msg):
        print(f"Job created: {data}")

listener = MyJobListener(nats_client)
await listener.listen()
```

## Middleware

Use authentication and permission middleware:

```python
from physicsworks_python.middlewares import auth_guard, permission_guard

# Example usage in web frameworks
@auth_guard
def protected_route(request):
    # Access authenticated user via request.current_user
    pass

@permission_guard('resource:write')
def admin_route(request):
    # Only accessible with proper permissions
    pass
```

## Development

### Build Package

```bash
# Clean previous builds
rm -rf build dist physicsworks_python.egg-info

# Build new distribution
python setup.py sdist bdist_wheel
```

### Publish to PyPI

```bash
# Install twine if needed
pip install twine

# Upload to PyPI
twine upload dist/*

# Or to a private registry
python -m twine upload --repository gitlab dist/* --verbose
```

### Running Tests

```bash
# Run tests (if test suite exists)
python -m pytest tests/
```

## Features

- ✅ **Unified Execution**: Support for remote and native solver execution
- ✅ **Modular Architecture**: Clean separation of concerns
- ✅ **Stage-based Execution**: Configurable execution stages
- ✅ **File Watching**: Real-time monitoring of output files
- ✅ **Server Communication**: Integrated server status updates
- ✅ **Debug Support**: Comprehensive logging
- ✅ **Post-processing**: Built-in visualization generation
- ✅ **Event System**: NATS-based pub/sub
- ✅ **Authentication**: JWT-based auth helpers

## Support

For issues, questions, or contributions:
- Contact: contact@physicsworks.io
- Documentation: Check the `/runner/` subdirectory for detailed workflow documentation

## License

MIT License
