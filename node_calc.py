import sys
import importlib
from io import StringIO
from pathlib import Path

# Add external repo to PYTHONPATH
repo_src = Path(__file__).resolve().parent / "backend" / "NirajDwave" / "src"
if repo_src not in sys.path:
    sys.path.insert(0, str(repo_src))

def run_gurobi_raw_output():
    """
    Runs the local Gurobi solver AND captures its console output.
    Returns: A big raw text string.
    """

    # Load solver module even though file starts with number
    solver = importlib.import_module("FullModelv1.15KNodeGurobiLocal")

    # Capture stdout
    buffer = StringIO()
    sys_stdout_original = sys.stdout
    sys.stdout = buffer

    try:
        model, g, s, x = solver.build_and_solve_gurobi()

        if model and model.Status == 2:  # GRB.OPTIMAL
            solver.print_solution_gurobi(model, g, s, x)

    finally:
        sys.stdout = sys_stdout_original

    # Raw solver text output
    return buffer.getvalue()

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
