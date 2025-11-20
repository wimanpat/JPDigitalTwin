import sys
import importlib
from pathlib import Path
from io import StringIO

repo_src = Path(__file__).resolve().parent / "backend" / "NirajDwave" / "src"
sys.path.insert(0, str(repo_src))


def capture_output(func, *args):
    """Utility that captures printed output from a solver."""
    buffer = StringIO()
    real_stdout = sys.stdout
    sys.stdout = buffer

    try:
        func(*args)
    except Exception as e:
        sys.stdout = real_stdout
        raise e
    finally:
        sys.stdout = real_stdout

    return buffer.getvalue()


# ====== LOCAL GUROBI SOLVER ======
def run_gurobi_raw_output():
    solver = importlib.import_module("FullModelv1.15KNodeGurobiLocal")

    def run():
        model, g, s, x = solver.build_and_solve_gurobi()
        if model.Status == 2:
            solver.print_solution_gurobi(model, g, s, x)

    return capture_output(run)


# ====== D-WAVE HYBRID CQM SOLVER ======
def run_cqm_output():
    solver = importlib.import_module("FullModelv1.15KNodeCQM")
    return capture_output(solver.main)   # Or solver.run(), depending on file


# ====== D-WAVE NLSAMPLER (QUANTUM ANNEALER) ======
def run_nlq_output():
    solver = importlib.import_module("FullModelv1.15KNodeOnNLSampler")
    return capture_output(solver.main)


# ====== FALLBACK (NO DEPENDENCIES) ======
def run_dummy_output():
    return "Dummy solver executed successfully.\n(No Gurobi / No D-Wave required.)"
