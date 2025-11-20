from flask import Flask, render_template, jsonify, session, request

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
    data = request.json
    session["solver"] = data.get("solver")
    return jsonify({"ok": True})

@app.route("/run-solver", methods=["POST"])
def run_solver():
    from node_calc import run_gurobi_raw_output, run_cqm_output, run_nlq_output, run_dummy_output

    solver = session.get("solver", "dummy")

    try:
        if solver == "gurobi":
            output = run_gurobi_raw_output()

        elif solver == "cqm":
            output = run_cqm_output()

        elif solver == "nlq":
            output = run_nlq_output()

        else:
            output = run_dummy_output()

        return jsonify({"ok": True, "output": output})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
