from flask import Flask, render_template, jsonify

app = Flask(__name__)

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

@app.route("/run-solver", methods=["POST"])
def run_solver():
    from node_calc import run_gurobi_raw_output

    try:
        output = run_gurobi_raw_output()
        return jsonify({"ok": True, "output": output})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)
