import sys
import importlib
from pathlib import Path

# Ensure backend path is added
repo_src = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_src))


# ====== LOCAL GUROBI SOLVER JSON OUTPUT ======
def run_gurobi_output():
    solver = importlib.import_module("backend.FullModelV1.15KNodeGurobiLocal")

    model, g, s, x = solver.build_and_solve_gurobi()

    if model.Status != 2:
        return {"ok": False, "error": "No optimal solution"}

    # Return JSON suitable for frontend
    return solver.build_frontend_result(model, g, s, x)


# ====== D-WAVE HYBRID CQM SOLVER ======
def run_cqm_output():
    solver = importlib.import_module("backend.FullModelV1.15KNodeCQM")
    return solver.main()


# ====== D-WAVE NLSAMPLER SOLVER ======
def run_nlq_output():
    solver = importlib.import_module("backend.FullModelV1.15KNodeOnNLSampler")
    return solver.main()

#IQM SOLVER
def run_iqm_output():
    solver = importlib.import_module("backend.solver_5node.run_5node_iqm")
    return solver.main()

#IonQ SOLVER
def run_ionq_output():
    solver = importlib.import_module("backend.solver_5node.run_5node_ionq")
    return solver.main()

# ====== FALLBACK ======
def run_dummy_output():
    return {"ok": True, "actions": ["Dummy solver ran."], "nodes": {}, "flows": []}
