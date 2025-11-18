from flask import Flask, render_template

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
if __name__ == "__main__":
    app.run(debug=True)
