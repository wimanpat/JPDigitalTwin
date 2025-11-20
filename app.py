from flask import Flask, render_template, jsonify, session, request
from backend.node_calc import (
    run_gurobi_output,
    run_cqm_output,
    run_nlq_output,
    run_dummy_output,
)

app = Flask(__name__)
app.secret_key = "some_random_secret_key"


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
    return render_template("settings.html", active="settings")


@app.route("/set-solver", methods=["POST"])
def set_solver():
    session["solver"] = request.json.get("solver", "gurobi")
    return jsonify({"ok": True})


@app.route("/run-solver", methods=["POST"])
def run_solver():

    solver = session.get("solver", "gurobi")

    try:
        if solver == "gurobi":
            return jsonify(run_gurobi_output())

        elif solver == "cqm":
            return jsonify(run_cqm_output())

        elif solver == "nlq":
            return jsonify(run_nlq_output())

        else:
            return jsonify(run_dummy_output())

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
