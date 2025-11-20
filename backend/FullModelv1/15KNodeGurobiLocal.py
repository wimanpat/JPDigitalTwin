# --- Large-Scale Gurobi MIP Solver (Local) ---
#
# Raw output kept but commented out.
# Only human-readable output is displayed.
#

import gurobipy as gp
from gurobipy import GRB
import sys
import time

# --- 1. Hard-Coded Problem Data ---

SOURCE_DATA = [
    {"type": "Solar",   "cost": 2.0, "max_gen": 3000},
    {"type": "Solar",   "cost": 2.1, "max_gen": 3000},
    {"type": "Wind",    "cost": 2.2, "max_gen": 4000},
    {"type": "Wind",    "cost": 2.3, "max_gen": 4000},
    {"type": "Nuclear", "cost": 3.0, "max_gen": 10000},
    {"type": "Thermal", "cost": 3.5, "max_gen": 8000},
    {"type": "Thermal", "cost": 3.6, "max_gen": 8000},
    {"type": "Hydro",   "cost": 5.0, "max_gen": 12000}
]
NUM_SOURCES = len(SOURCE_DATA)

BATTERY_DATA = [
    {"max_cap": 10000, "initial_cap": 10000, "min_cap": 1000},
    {"max_cap": 8000,  "initial_cap":  8000, "min_cap": 800}
]
NUM_BATTERIES = len(BATTERY_DATA)

DEMAND_PER_SINK_NODE = 4500
NUM_SINK_NODES = 15
TOTAL_DEMAND = NUM_SINK_NODES * DEMAND_PER_SINK_NODE

NODE_NAMES = [f"TS_S{i}" for i in range(NUM_SOURCES)] + \
             [f"TS_B{j}" for j in range(NUM_BATTERIES)] + \
             [f"TS_D{k}" for k in range(NUM_SINK_NODES)]

NUM_TS_NODES = len(NODE_NAMES)
MAX_ARC_FLOW = 10000


# -----------------------------------------------------------
# BUILD MODEL
# -----------------------------------------------------------

def build_and_solve_gurobi():

    try:
        # print("--- Building Large-Scale Gurobi MIP Model ---")
        model = gp.Model("Large_Network_Flow_Gurobi")

        # GENERATION VARS
        g = {}
        for i in range(NUM_SOURCES):
            g[i] = model.addVar(vtype=GRB.INTEGER, lb=0,
                ub=SOURCE_DATA[i]["max_gen"], name=f"g{i}")

        # BATTERY VARS
        s = {}
        for j in range(NUM_BATTERIES):
            s[j] = model.addVar(vtype=GRB.INTEGER,
                lb=BATTERY_DATA[j]["min_cap"],
                ub=BATTERY_DATA[j]["max_cap"],
                name=f"s{j}")

        # ARC FLOW VARS
        x = {}
        for k_idx, k_name in enumerate(NODE_NAMES):
            for l_idx, l_name in enumerate(NODE_NAMES):
                if k_idx == l_idx:
                    continue
                x[(k_name, l_name)] = model.addVar(
                    vtype=GRB.INTEGER, lb=0, ub=MAX_ARC_FLOW,
                    name=f"x_{k_name}_{l_name}"
                )

        # print(f"Total variables: {model.NumVars}")

        # OBJECTIVE
        objective = gp.quicksum(
            SOURCE_DATA[i]["cost"] * g[i] for i in range(NUM_SOURCES)
        )
        model.setObjective(objective, GRB.MINIMIZE)

        # FLOW BALANCE
        for k_idx, k_name in enumerate(NODE_NAMES):

            flow_in = gp.quicksum(
                x[(l_name, k_name)] for l_idx, l_name in enumerate(NODE_NAMES)
                if l_idx != k_idx
            )

            flow_out = gp.quicksum(
                x[(k_name, l_name)] for l_idx, l_name in enumerate(NODE_NAMES)
                if l_idx != k_idx
            )

            if k_idx < 8:
                # Source node
                model.addConstr(flow_in - flow_out + g[k_idx] == 0)

            elif 8 <= k_idx < 10:
                # Battery node
                j = k_idx - 8
                initial_storage = BATTERY_DATA[j]["initial_cap"]
                model.addConstr(
                    flow_in - flow_out + (initial_storage - s[j]) == 0
                )

            else:
                # Sink node
                model.addConstr(flow_in - flow_out == DEMAND_PER_SINK_NODE)

        # print(f"Total constraints: {model.NumConstrs}")

        # SOLVE
        # print("\n--- Solving with Gurobi MIP Solver ---")
        start = time.time()
        model.optimize()
        # print(f"...Solving complete in {time.time() - start:.2f}s")

        return model, g, s, x

    except Exception as e:
        print("ERROR:", e)
        sys.exit(1)


# -----------------------------------------------------------
# HUMAN-READABLE DESCRIPTION FUNCTIONS
# -----------------------------------------------------------

def describe_generators(g_vars):
    lines = []
    for i in range(NUM_SOURCES):
        gen = int(g_vars[i].X)
        info = SOURCE_DATA[i]
        max_gen = info["max_gen"]
        gtype = info["type"]
        utilization = gen / max_gen if max_gen > 0 else 0

        if gen == 0:
            lines.append(
                f"Switch OFF {gtype} generator S{i} (0 / {max_gen:,} units)."
            )
        elif utilization < 0.3:
            lines.append(
                f"Run {gtype} generator S{i} at LOW output "
                f"({gen:,} / {max_gen:,} units)."
            )
        elif utilization < 0.9:
            lines.append(
                f"Run {gtype} generator S{i} at MEDIUM output "
                f"({gen:,} / {max_gen:,} units)."
            )
        else:
            lines.append(
                f"Run {gtype} generator S{i} at FULL output "
                f"({gen:,} / {max_gen:,} units)."
            )
    return lines


def describe_batteries(s_vars):
    lines = []
    for j in range(NUM_BATTERIES):
        final = int(s_vars[j].X)
        initial = BATTERY_DATA[j]["initial_cap"]
        max_cap = BATTERY_DATA[j]["max_cap"]
        delta = final - initial
        pct = final / max_cap * 100

        if delta < 0:
            lines.append(
                f"Discharge Battery {j} by {abs(delta):,} units "
                f"(final {final:,} / {max_cap:,}, {pct:.1f}%)."
            )
        elif delta > 0:
            lines.append(
                f"Charge Battery {j} by {delta:,} units "
                f"(final {final:,} / {max_cap:,}, {pct:.1f}%)."
            )
        else:
            lines.append(
                f"Keep Battery {j} unchanged at "
                f"{final:,} / {max_cap:,} units ({pct:.1f}%)."
            )

    return lines


def describe_major_flows(x_vars, top_n=10, min_threshold=5000):
    flows = []
    for (src, dst), xvar in x_vars.items():
        flow = int(xvar.X)
        if flow >= min_threshold:
            flows.append((flow, src, dst))

    flows.sort(reverse=True)
    flows = flows[:top_n]

    return [f"Send {f:,} units from {s} to {d}." for f, s, d in flows]


def explain_cost_logic(g_vars):
    lines = []
    sorted_idx = sorted(
        range(NUM_SOURCES),
        key=lambda i: SOURCE_DATA[i]["cost"]
    )

    lines.append("Cheapest generators are used first:")

    for i in sorted_idx:
        info = SOURCE_DATA[i]
        gen = int(g_vars[i].X)
        max_gen = info["max_gen"]
        cost = info["cost"]
        pct = gen / max_gen * 100 if max_gen else 0
        lines.append(
            f"- {info['type']} S{i} (cost ${cost}/unit): "
            f"{gen:,} / {max_gen:,} units ({pct:.1f}%)."
        )

    return lines


# -----------------------------------------------------------
# PRINT HUMAN-READABLE ONLY
# -----------------------------------------------------------

def print_solution_gurobi(model, g_vars, s_vars, x_vars):

    if model.Status != GRB.OPTIMAL:
        print("No optimal solution found.")
        return

    # -------------------------------------------------------
    # RAW OUTPUT BLOCK — now fully commented out
    # -------------------------------------------------------

    """
    print("\nSource Generation:")
    for i in range(NUM_SOURCES):
        gen = int(g_vars[i].X)
        cost = SOURCE_DATA[i]['cost']
        max_gen = SOURCE_DATA[i]['max_gen']
        print(f"  - S{i} ({SOURCE_DATA[i]['type']:<7} Cost ${cost:.2f}): "
              f"{gen: >7,} / {max_gen: >7,} units")

    # (All the raw numerical outputs commented out…)
    """

    # -------------------------------------------------------
    # HUMAN-READABLE OUTPUT (only this prints)
    #--------------------------------------------------------

    print("\n=== Human-Readable Operational Plan ===\n")

    print("Generator Actions:")
    for line in describe_generators(g_vars):
        print("  - " + line)

    print("\nBattery Actions:")
    for line in describe_batteries(s_vars):
        print("  - " + line)

    print("\nMajor Routing Decisions:")
    for line in describe_major_flows(x_vars):
        print("  - " + line)

    print("\nReasoning (Why this mix was chosen):")
    for line in explain_cost_logic(g_vars):
        print("  " + line)


# -----------------------------------------------------------
# MAIN
# -----------------------------------------------------------

if __name__ == "__main__":

    model, g, s, x = build_and_solve_gurobi()

    if model and model.Status == GRB.OPTIMAL:
        print_solution_gurobi(model, g, s, x)