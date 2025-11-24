import os
import itertools
import time
from dotenv import load_dotenv
from scipy.optimize import minimize

load_dotenv()

IQM_SERVER_URL = os.getenv("IQM_SERVER_URL") or os.getenv("SERVER_URL")
IQM_API_TOKEN = os.getenv("IQM_API_TOKEN") or os.getenv("RESONANCE_API_TOKEN")

if not IQM_SERVER_URL or not IQM_API_TOKEN:
    raise RuntimeError("Set IQM_SERVER_URL and IQM_API_TOKEN in .env or environment.")

# Problem definition
sources = ['A', 'B']
sinks = {'C': 3, 'D': 2}
battery = 'E'
battery_capacity = 4
initial_soc = 0.5

Gmax = {'A': 3, 'B': 2}
cost = {'A': 2.0, 'B': 3.0}

nodes = ['A', 'B', 'C', 'D', 'E']
arcs = [(i, j) for i in nodes for j in nodes if i != j]

valid_arcs = [
    (i, j) for (i, j) in arcs
    if (i in sources and j in sinks.keys())
    or (i in sources and j == battery)
    or (i == battery and j in sinks.keys())
]

var_names = [f"f_{i}_{j}" for (i, j) in valid_arcs]
n_vars = len(var_names)
print(f"Problem uses {n_vars} binary variables:\n  {var_names}")

# Build QUBO with penalty terms (same idea as earlier)
import dimod
penalty = 8.0

linear = {}
quadratic = {}

# source cost terms
for v in var_names:
    src = v.split('_')[1]
    if src in sources:
        linear[v] = linear.get(v, 0.0) + cost[src]

# sink demand constraints
for sink, demand in sinks.items():
    incoming = [v for v in var_names if v.endswith("_" + sink)]
    for v in incoming:
        linear[v] = linear.get(v, 0.0) + penalty - 2.0 * penalty * demand
    for v1, v2 in itertools.combinations(incoming, 2):
        quadratic[tuple(sorted([v1, v2]))] = quadratic.get(tuple(sorted([v1, v2])), 0.0) + 2.0 * penalty

# source generation limits
for src in sources:
    outgoing = [v for v in var_names if v.startswith(f"f_{src}_")]
    gmax = Gmax[src]
    for v in outgoing:
        linear[v] = linear.get(v, 0.0) + penalty - 2.0 * penalty * gmax
    for v1, v2 in itertools.combinations(outgoing, 2):
        quadratic[tuple(sorted([v1, v2]))] = quadratic.get(tuple(sorted([v1, v2])), 0.0) + 2.0 * penalty

# battery SOC balancing (pull SOC toward target_soc)
incoming_to_bat = [v for v in var_names if v.endswith("_E")]
outgoing_from_bat = [v for v in var_names if v.startswith("f_E_")]
target_soc = 0.5 * battery_capacity

for v in incoming_to_bat + outgoing_from_bat:
    coeff = 1.0 if v in incoming_to_bat else -1.0
    linear[v] = linear.get(v, 0.0) + penalty * (coeff**2) - 2.0 * penalty * target_soc * coeff

for v1, v2 in itertools.combinations(incoming_to_bat + outgoing_from_bat, 2):
    coeff1 = 1.0 if v1 in incoming_to_bat else -1.0
    coeff2 = 1.0 if v2 in incoming_to_bat else -1.0
    quadratic[tuple(sorted([v1, v2]))] = (
        quadratic.get(tuple(sorted([v1, v2])), 0.0) + 2.0 * penalty * (coeff1 * coeff2)
    )

bqm = dimod.BinaryQuadraticModel(linear, quadratic, 0.0, dimod.BINARY)
print("Built BQM:", len(bqm.linear), "linear terms;", len(bqm.quadratic), "quadratic terms")

# IQM connection
from iqm.qiskit_iqm import IQMProvider, transpile_to_IQM
from qiskit import QuantumCircuit

provider = IQMProvider(IQM_SERVER_URL, token=IQM_API_TOKEN)
backend = provider.get_backend()
print("Connected to IQM backend:", backend.name, "  qubits:", getattr(backend, "num_qubits", "unknown"))

# mapping var->qubit index
var_to_idx = {v: i for i, v in enumerate(var_names)}
n_qubits = n_vars
shots = 512  

# build QAOA-like ansatz (parametrized)
p = 1

def build_qaoa_circuit(params):
    gammas = params[:p]
    betas = params[p:2*p]
    qc = QuantumCircuit(n_qubits)
    qc.h(range(n_qubits))
    for level in range(p):
        gamma = float(gammas[level])
        for (label, coeff) in [(k, v) for k, v in list(bqm.quadratic.items())]:
            u, vv = label
            q1 = var_to_idx[u]
            q2 = var_to_idx[vv]
            angle = -2.0 * gamma * coeff
            qc.cx(q1, q2)
            qc.rz(angle, q2)
            qc.cx(q1, q2)
        for vname, coeff in bqm.linear.items():
            q = var_to_idx[vname]
            angle = -gamma * coeff
            qc.rz(angle, q)
        beta = float(betas[level])
        for q in range(n_qubits):
            qc.rx(2.0 * beta, q)
    qc.measure_all()
    return qc

# energy estimation function using hardware counts
def energy_from_counts(counts):
    total = sum(counts.values())
    avg = 0.0
    for bitstr, cnt in counts.items():
        sample = {v: int(bitstr[i]) for i, v in enumerate(var_names)}
        e = bqm.energy(sample)
        avg += (cnt / total) * e
    return avg

def hardware_eval(params):
    qc = build_qaoa_circuit(params)
    qc_iqm = transpile_to_IQM(qc, backend)
    job = backend.run(qc_iqm, shots=shots)
    res = job.result()
    counts = res.get_counts()
    e = energy_from_counts(counts)
    print("params:", [round(float(x), 4) for x in params], "-> energy:", round(e, 4))
    return e

# classical outer optimization (COBYLA)
init = [0.5] * (2 * p)
print("Starting optimization on IQM (this will run hardware multiple times).")
t0 = time.time()
res = minimize(hardware_eval, x0=init, method='COBYLA', options={'maxiter': 6})
t1 = time.time()
print("Optimization finished in", round(t1 - t0, 1), "s; result:", res)

# final run with best params and output processing
best_params = res.x
final_qc = build_qaoa_circuit(best_params)
final_qc_iqm = transpile_to_IQM(final_qc, backend)
job = backend.run(final_qc_iqm, shots=shots)
res_final = job.result()
counts = res_final.get_counts()
print("\nFinal counts:", counts)

best_bs = max(counts, key=counts.get)
best_sample = {v: int(best_bs[i]) for i, v in enumerate(var_names)}
print("\nBest measured bitstring:", best_bs)
print("Energy:", bqm.energy(best_sample))

print("\nActive flows (1 == flow on arc):")
for v in var_names:
    if best_sample[v] == 1:
        src, dst = v.split('_')[1], v.split('_')[2]
        print(f"  {src} -> {dst}")

print("\nDemand checks:")
for sink_node, demand in sinks.items():
    received = sum(best_sample[v] for v in var_names if v.endswith("_" + sink_node))
    print(f"  {sink_node}: {received}/{demand} {'✓' if received >= demand else '✗'}")

print("\nSource caps:")
for s in sources:
    gen = sum(best_sample[v] for v in var_names if v.startswith(f"f_{s}_"))
    print(f"  {s}: {gen}/{Gmax[s]} {'✓' if gen <= Gmax[s] else '✗'}")
