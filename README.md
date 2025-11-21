# Digital Twin Power Grid Optimizer
Built by Jakob & Patrick

## Interactive UI with local Gurobi Solver
This is a **Flask-based web application** designed to visualize and execute a large-scale node optimization models.
It has a hard-coded real **25-node / 600-arc minimum-cost-flow model**, originally developed by Niraj:
[NirajDwave Repository](https://github.com/NirajDayama/NirajDwave/)

The goal of the project is to build a **interactive Digital Twin** interface where different solvers can be selected and executed, making a easy-to-understand interface for potential customers.

The solvers that are included is:
- Local Gurobi Solver (CPU-based) **<-- This one is currently integrated**
- D-Wave Hybrid CQM Solver (Both CPU & QPU) <-- This is not integrated yet
- D-Wave Wuantom Annealer (QPU-based) <-- This is also not yet integrated
- Dummy Solver **<-- This is only for development and UI-testing**

## Features
- Interactive web UI
- Dashboard for running solvers
- Human-readable logs
- Dark/light theme
- Interactive system settings
- Solver switching
- Node & Flow Visualization

## Future Development
  
For future development, the other two solvers from `NirajDwave/src/FullModelv1` should be integrated, almost everything else is ready. For this ust place the `.py` solvers in  `JPDigitalTwin/backend/FullModelV1`, and integrate the API-keys as necessary.
For a better UI there should also be added more functionality to **settings, topology and operations view**.
For a final product we need to add functionality to upload custom sources, nodes, batteries and sinks.
