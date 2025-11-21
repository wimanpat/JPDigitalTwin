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
# VISUALIZATION: Extract large non-zero flows
# -----------------------------------------------------------

def get_visual_flows(x_vars, min_flow=2000):
    flow_list = []
    for (src, dst), xvar in x_vars.items():
        f = int(xvar.X)
        if f >= min_flow:
            flow_list.append({
                "src": src,
                "dst": dst,
                "flow": f
            })
    return flow_list


# -----------------------------------------------------------
# BUILD MODEL
# -----------------------------------------------------------

def build_and_solve_gurobi():

    try:
        model = gp.Model("Large_Network_Flow_Gurobi")

        # GENERATION VARS
        g = {
            i: model.addVar(
                vtype=GRB.INTEGER,
                lb=0,
                ub=SOURCE_DATA[i]["max_gen"],
                name=f"g{i}"
            )
            for i in range(NUM_SOURCES)
        }

        # BATTERY VARS
        s = {
            j: model.addVar(
                vtype=GRB.INTEGER,
                lb=BATTERY_DATA[j]["min_cap"],
                ub=BATTERY_DATA[j]["max_cap"],
                name=f"s{j}"
            )
            for j in range(NUM_BATTERIES)
        }

        # ARC FLOWS
        x = {}
        for k_idx, k_name in enumerate(NODE_NAMES):
            for l_idx, l_name in enumerate(NODE_NAMES):
                if k_idx == l_idx:
                    continue

                x[(k_name, l_name)] = model.addVar(
                    vtype=GRB.INTEGER,
                    lb=0,
                    ub=MAX_ARC_FLOW,
                    name=f"x_{k_name}_{l_name}"
                )

        # OBJECTIVE (min cost)
        model.setObjective(
            gp.quicksum(
                SOURCE_DATA[i]["cost"] * g[i]
                for i in range(NUM_SOURCES)
            ),
            GRB.MINIMIZE
        )

        # FLOW BALANCE CONSTRAINTS
        for k_idx, k_name in enumerate(NODE_NAMES):

            flow_in = gp.quicksum(
                x[(l_name, k_name)]
                for l_idx, l_name in enumerate(NODE_NAMES)
                if l_idx != k_idx
            )
            flow_out = gp.quicksum(
                x[(k_name, l_name)]
                for l_idx, l_name in enumerate(NODE_NAMES)
                if l_idx != k_idx
            )

            # Source node
            if k_idx < 8:
                model.addConstr(flow_in - flow_out + g[k_idx] == 0)

            # Battery node
            elif 8 <= k_idx < 10:
                j = k_idx - 8
                initial_storage = BATTERY_DATA[j]["initial_cap"]
                model.addConstr(flow_in - flow_out + (initial_storage - s[j]) == 0)

            # Sink node
            else:
                model.addConstr(flow_in - flow_out == DEMAND_PER_SINK_NODE)

        # SOLVE
        model.optimize()
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
        typ = info["type"]
        util = gen / max_gen if max_gen else 0

        if gen == 0:
            lines.append(f"Switch OFF {typ} generator S{i} (0 / {max_gen:,} units).")
        elif util < 0.3:
            lines.append(f"Run {typ} generator S{i} at LOW output ({gen:,}/{max_gen:,}).")
        elif util < 0.9:
            lines.append(f"Run {typ} generator S{i} at MEDIUM output ({gen:,}/{max_gen:,}).")
        else:
            lines.append(f"Run {typ} generator S{i} at FULL output ({gen:,}/{max_gen:,}).")

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
            lines.append(f"Discharge Battery {j} by {abs(delta):,} units ({final}/{max_cap}, {pct:.1f}%).")
        elif delta > 0:
            lines.append(f"Charge Battery {j} by {delta:,} units ({final}/{max_cap}, {pct:.1f}%).")
        else:
            lines.append(f"Battery {j} remains unchanged ({final}/{max_cap}, {pct:.1f}%).")

    return lines


def describe_major_flows(x_vars, top_n=10, min_threshold=5000):
    flows = [
        (int(xvar.X), src, dst)
        for (src, dst), xvar in x_vars.items()
        if int(xvar.X) >= min_threshold
    ]

    flows.sort(reverse=True)
    flows = flows[:top_n]

    return [f"Send {amt:,} units from {s} → {d}" for amt, s, d in flows]


def explain_cost_logic(g_vars):
    lines = ["Cheapest generators used first:"]
    sorted_idx = sorted(range(NUM_SOURCES), key=lambda i: SOURCE_DATA[i]["cost"])

    for i in sorted_idx:
        gen = int(g_vars[i].X)
        max_gen = SOURCE_DATA[i]["max_gen"]
        cost = SOURCE_DATA[i]["cost"]
        pct = gen / max_gen * 100
        lines.append(f"- {SOURCE_DATA[i]['type']} S{i}: {gen:,}/{max_gen:,} units (cost ${cost}, {pct:.1f}%)")

    return lines


# -----------------------------------------------------------
# VISUALIZATION NODE POSITIONS
# -----------------------------------------------------------

def get_node_positions():
    return {

        # ============================================================
        # GENERATION (Left side vertical)
        # ============================================================
        "TS_S0": {"x": 150, "y": 80,  "type": "Gen"},
        "TS_S1": {"x": 150, "y": 150, "type": "Gen"},
        "TS_S2": {"x": 150, "y": 220, "type": "Gen"},
        "TS_S3": {"x": 150, "y": 290, "type": "Gen"},
        "TS_S4": {"x": 150, "y": 360, "type": "Gen"},
        "TS_S5": {"x": 150, "y": 430, "type": "Gen"},
        "TS_S6": {"x": 150, "y": 500, "type": "Gen"},
        "TS_S7": {"x": 150, "y": 570, "type": "Gen"},

        # ============================================================
        # SUBSTATION BUSES / TRANSFORMERS (Center spine)
        # ============================================================
        "TS_B0": {"x": 350, "y": 250, "type": "Bus"},
        "TS_B1": {"x": 350, "y": 400, "type": "Bus"},

        # ============================================================
        # LOADS / FEEDERS (Right side)
        # ============================================================
        "TS_D0": {"x": 600, "y": 80,  "type": "Load"},
        "TS_D1": {"x": 600, "y": 130, "type": "Load"},
        "TS_D2": {"x": 600, "y": 180, "type": "Load"},
        "TS_D3": {"x": 600, "y": 230, "type": "Load"},
        "TS_D4": {"x": 600, "y": 280, "type": "Load"},
        "TS_D5": {"x": 600, "y": 330, "type": "Load"},
        "TS_D6": {"x": 600, "y": 380, "type": "Load"},
        "TS_D7": {"x": 600, "y": 430, "type": "Load"},
        "TS_D8": {"x": 600, "y": 480, "type": "Load"},
        "TS_D9": {"x": 600, "y": 530, "type": "Load"},
        "TS_D10": {"x": 750, "y": 200, "type": "Load"},
        "TS_D11": {"x": 750, "y": 260, "type": "Load"},
        "TS_D12": {"x": 750, "y": 320, "type": "Load"},
        "TS_D13": {"x": 750, "y": 380, "type": "Load"},
        "TS_D14": {"x": 750, "y": 440, "type": "Load"},
    }

def get_primary_edges():
    """Defines the real electrical one-line topology, not solver flows"""
    return [
        # GENERATORS FEED SUBSTATION BUSES
        ("TS_S0", "TS_B0"),
        ("TS_S1", "TS_B0"),
        ("TS_S2", "TS_B0"),
        ("TS_S3", "TS_B0"),

        ("TS_S4", "TS_B1"),
        ("TS_S5", "TS_B1"),
        ("TS_S6", "TS_B1"),
        ("TS_S7", "TS_B1"),

        # BUSES FEED LOAD BLOCKS
        ("TS_B0", "TS_D0"),
        ("TS_B0", "TS_D1"),
        ("TS_B0", "TS_D2"),
        ("TS_B0", "TS_D3"),
        ("TS_B0", "TS_D4"),
        ("TS_B0", "TS_D5"),

        ("TS_B1", "TS_D6"),
        ("TS_B1", "TS_D7"),
        ("TS_B1", "TS_D8"),
        ("TS_B1", "TS_D9"),
        ("TS_B1", "TS_D10"),
        ("TS_B1", "TS_D11"),
        ("TS_B1", "TS_D12"),
        ("TS_B1", "TS_D13"),
        ("TS_B1", "TS_D14"),
    ]




# -----------------------------------------------------------
# FRONTEND JSON BUILDER
# -----------------------------------------------------------

def build_frontend_result(model, g_vars, s_vars, x_vars):
    return {
        "ok": True,
        "nodes": get_node_positions(),
        "primary_edges": get_primary_edges(),
        "flows": get_visual_flows(x_vars),
        "actions": (
            describe_generators(g_vars)
            + describe_batteries(s_vars)
            + describe_major_flows(x_vars)
            + explain_cost_logic(g_vars)
        )
    }


# -----------------------------------------------------------
# PRINT HUMAN-READABLE
# -----------------------------------------------------------

def print_solution_gurobi(model, g_vars, s_vars, x_vars):

    print("\n=== Human-Readable Operational Plan ===\n")

    print("Generator Actions:")
    for line in describe_generators(g_vars):
        print("  -", line)

    print("\nBattery Actions:")
    for line in describe_batteries(s_vars):
        print("  -", line)

    print("\nMajor Routing Decisions:")
    for line in describe_major_flows(x_vars):
        print("  -", line)

    print("\nReasoning:")
    for line in explain_cost_logic(g_vars):
        print(" ", line)


# -----------------------------------------------------------
# MAIN (debug mode)
# -----------------------------------------------------------

if __name__ == "__main__":
    model, g, s, x = build_and_solve_gurobi()
    if model.Status == GRB.OPTIMAL:
        print_solution_gurobi(model, g, s, x)
