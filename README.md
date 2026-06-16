power-system-simulation
This is a student project for Power System Simulation.

Overview:
Power System Simulation is a Python package for analyzing low-voltage distribution grids. It combines graph-based topology processing with time-series power flow simulations using power-grid-model (PGM), enabling advanced analytics such as contingency analysis, EV integration studies, and transformer tap optimization.

Features:

Graph-based grid topology analysis
Time-series power flow simulation using PGM
Aggregation of voltage and line performance metrics
Validation of low-voltage grid data
N‑1 contingency analysis (line failure scenarios)
Transformer tap position optimization
Modular and reusable design for scalable workflows


Installation:
This project uses https://docs.astral.sh/uv/ for dependency management.
In the root of the repository, sync all dependencies using:
    uv sync

After installation, run the tests:
    uv run pytest

Quick Start:

from power_system_simulation.grid_model import (
    load_input_data,
    construct_model,
    create_batch_update,
    run_power_flow,
    aggregate_voltage_results,
)

# Load grid data
input_data = load_input_data("grid.json")

# Build model
model = construct_model(input_data)

# Create time-series updates
update_data, timestamps = create_batch_update(active_profile, reactive_profile)

# Run power flow
output = run_power_flow(model, input_data, update_data)

# Aggregate results
voltage_results = aggregate_voltage_results(output, timestamps)

Modules:
graph_processing:
Provides graph algorithms for grid topology:

Downstream node detection:
Alternative edge identification
Input validation for graph consistency


grid_model:
Core interface to power-grid-model:

Load and validate input data
Construct simulation models
Run time-series power flow
Aggregate voltage and line results


lv_validation:
Validation utilities for LV grid data:

Topology checks (connected, radial structure)
Component constraints (single source and transformer)
Profile consistency verification


n1_calculation:
Performs N‑1 contingency analysis:

Simulates line outages
Identifies valid reconnection options
Evaluates worst-case loading scenarios


tap_optimization:
Transformer tap optimization tools:

Evaluate multiple tap positions
Minimize energy losses or voltage deviations
Automate selection of optimal tap setting


Code style and quality check:
This project uses https://docs.astral.sh/ruff/ for linting and formatting.
Check and automatically fix code issues:
    uv run ruff check --fix 

Format your code:
    uv run ruff format

Working with Jupyter Notebooks:
Jupyter notebooks in the example/ folder can be opened directly in VS Code. The project includes ipykernel in the development dependencies, allowing VS Code to run notebook cells using the .venv environment.

Folder structure of the repository:

./src/power_system_simulation – main package source code
./tests – test suite
./example – example notebook for demonstration
./.vscode – VS Code configuration
./.github/workflows – CI configuration


Example Use Cases:

Distribution grid performance analysis
EV charging impact studies
Grid resilience and contingency planning
Operational optimization (tap settings)
Time-series load flow simulations


License:
Ensure compatibility with the licenses of the following dependencies:

power-grid-model
networkx
pandas
numpy

