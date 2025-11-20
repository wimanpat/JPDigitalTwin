import sys
import importlib
from pathlib import Path

# Add external repo to PYTHONPATH
repo_src = Path(__file__).resolve().parent / "backend" / "NirajDwave" / "src"
if repo_src not in sys.path:
    sys.path.insert(0, str(repo_src))


def import_solver(module_name):
    """
    Dynamically import solver files whose names start with numbers.
    Example module_name: "FullModelv1.15KNodeGurobiLocal"
    """
    return importlib.import_module(module_name)


def calculate(data, model="FullModel-Gurobi"):
    """
    data = Python dictionary from upload
    model = one of:
        - "FullModel-Gurobi"
        - "FullModel-CQM"
        - "FullModel-NLQ"
    """

    # MODEL 1: Gurobi (Local classical solver)
    if model == "FullModel-Gurobi":
        solver = import_solver("FullModelv1.15KNodeGurobiLocal")
        return solver.main(data) if hasattr(solver, "main") else solver.run(data)

    # MODEL 2: CQM (Quantum Hybrid - requires keys)
    if model == "FullModel-CQM":
        solver = import_solver("FullModelv1.15KNodeCQM")
        return solver.main(data) if hasattr(solver, "main") else solver.run(data)

    # MODEL 3: OnNLSampler (Quantum QA - requires keys)
    if model == "FullModel-NLQ":
        solver = import_solver("FullModelv1.15KNodeOnNLSampler")
        return solver.main(data) if hasattr(solver, "main") else solver.run(data)

    else:
        raise ValueError(f"Unknown model type: {model}")
