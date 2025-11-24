from flask import Flask, render_template, jsonify, session, request
from backend.node_calc import (
    run_gurobi_output,
    run_cqm_output,
    run_nlq_output,
    run_dummy_output, #run_iqm_output, run_ionq_output,
)
#from backend.solver_5node.run_5node_ionq import result

app = Flask(__name__)
app.secret_key = "some_random_secret_key"


# ================================
# PAGE ROUTES
# ================================
@app.route("/")
def command_center():
    return render_template("command_center.html", active="command")


@app.route("/topology")
def topology():
    return render_template("topology.html", active="topology")


@app.route("/operations")
def operations():
    return render_template("operations.html", active="operations")


@app.route("/settings")
def settings():
    saved = session.get("solver", "gurobi")
    return render_template("settings.html", active="settings", saved_solver=saved)


# ================================
# SET SOLVER
# ================================
@app.route("/set-solver", methods=["POST"])
def set_solver():
    session["solver"] = request.json.get("solver", "gurobi")
    return jsonify({"ok": True})


# ================================
# RUN SOLVER + SAVE TOPOLOGY
# ================================
@app.route("/run-solver", methods=["POST"])
def run_solver():

    solver = session.get("solver", "gurobi")

    try:
        # Select solver
        if solver == "gurobi":
            result = run_gurobi_output()
        elif solver == "cqm":
            result = run_cqm_output()
        elif solver == "nlq":
            result = run_nlq_output()
        elif solver == "iqm":
            result = run_iqm_output()
        elif solver == "ionq":
            result = run_ionq_output()
        else:
            result = run_dummy_output()

        # If failed, return
        if not result.get("ok"):
            return jsonify(result)

        # SAVE LATEST GRID (for topology page)
        session["latest_topology"] = {
            "nodes": result.get("nodes", {}),
            "flows": result.get("flows", [])
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ================================
# GET TOPOLOGY FOR TOPOLOGY VIEW
# ================================
@app.route("/get-topology")
def get_topology():
    topo = session.get("latest_topology")

    if not topo:
        return jsonify({"ok": False, "error": "No solved topology available yet."})

    return jsonify({"ok": True, **topo})


# ================================
# MAIN
# ================================
if __name__ == "__main__":
    app.run(debug=True)
