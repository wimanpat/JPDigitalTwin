import os
import itertools
from dotenv import load_dotenv
from scipy.optimize import minimize
import dimod

load_dotenv()

# CONFIGURATION
IONQ_API_KEY = os.getenv("IONQ_API_KEY")
if not IONQ_API_KEY:
    raise RuntimeError("Set IONQ_API_KEY in .env file")

# Problem definition
sources = ['A', 'B']
sinks = {'C': 3, 'D': 2}
battery = 'E'
Gmax = {'A': 3, 'B': 2}
cost = {'A': 2.0, 'B': 3.0}

nodes = ['A', 'B', 'C', 'D', 'E']
valid_arcs = [
    (i, j) for i in nodes for j in nodes if i != j
    and ((i in sources and j in ['C', 'D', 'E']) or (i == 'E' and j in ['C', 'D']))
]

var_names = [f"f_{i}_{j}" for (i, j) in valid_arcs]
n_vars = len(var_names)
print(f"Problem: {n_vars} binary variables")
print(f"Variables: {var_names}\n")

# BUILD QUBO
penalty = 8.0
linear = {}
quadratic = {}

# Source costs
for v in var_names:
    src = v.split('_')[1]
    if src in sources:
        linear[v] = linear.get(v, 0.0) + cost[src]

# Demand constraints
for sink, demand in sinks.items():
    incoming = [v for v in var_names if v.endswith(f"_{sink}")]
    for v in incoming:
        linear[v] = linear.get(v, 0.0) + penalty - 2.0 * penalty * demand
    for v1, v2 in itertools.combinations(incoming, 2):
        k = tuple(sorted([v1, v2]))
        quadratic[k] = quadratic.get(k, 0.0) + 2.0 * penalty

# Capacity constraints
for src in sources:
    outgoing = [v for v in var_names if v.startswith(f"f_{src}_")]
    for v in outgoing:
        linear[v] = linear.get(v, 0.0) + penalty - 2.0 * penalty * Gmax[src]
    for v1, v2 in itertools.combinations(outgoing, 2):
        k = tuple(sorted([v1, v2]))
        quadratic[k] = quadratic.get(k, 0.0) + 2.0 * penalty

# Build BQM
bqm = dimod.BinaryQuadraticModel(linear, quadratic, 0.0, dimod.BINARY)
print(f"Built BQM: {len(bqm.linear)} linear, {len(bqm.quadratic)} quadratic terms\n")

# CONNECT TO IONQ
from qiskit_ionq import IonQProvider
from qiskit import QuantumCircuit, transpile

provider = IonQProvider(token=IONQ_API_KEY)
backend = provider.get_backend("ionq_simulator") 
# backend = provider.get_backend("ionq_qpu")      # Uncomment for real hardware

print(f"Connected to: {backend.name}\n")

# BUILD QAOA CIRCUIT
var_to_idx = {v: i for i, v in enumerate(var_names)}
n_qubits = n_vars
shots = 512
p = 1 

def build_qaoa_circuit(params):
    """Build QAOA ansatz circuit"""
    gammas = params[:p]
    betas = params[p:2*p]
    
    qc = QuantumCircuit(n_qubits)
    
    # Initial superposition
    qc.h(range(n_qubits))
    
    for level in range(p):
        gamma = float(gammas[level])
        
        # Apply problem Hamiltonian (quadratic terms)
        for (u, v), coeff in bqm.quadratic.items():
            q1 = var_to_idx[u]
            q2 = var_to_idx[v]
            angle = -2.0 * gamma * coeff
            qc.cx(q1, q2)
            qc.rz(angle, q2)
            qc.cx(q1, q2)
        
        # Apply problem Hamiltonian (linear terms)
        for vname, coeff in bqm.linear.items():
            q = var_to_idx[vname]
            angle = -gamma * coeff
            qc.rz(angle, q)
        
        # Apply mixer Hamiltonian
        beta = float(betas[level])
        for q in range(n_qubits):
            qc.rx(2.0 * beta, q)
    
    qc.measure_all()
    return qc

# ENERGY EVALUATION ON IONQ
def energy_from_counts(counts):
    """Calculate expected energy from measurement counts"""
    total = sum(counts.values())
    avg_energy = 0.0
    for bitstr, cnt in counts.items():
        # Convert bitstring to variable assignment
        sample = {v: int(bitstr[i]) for i, v in enumerate(var_names)}
        e = bqm.energy(sample)
        avg_energy += (cnt / total) * e
    return avg_energy

def hardware_eval(params):
    """Evaluate energy on IonQ hardware"""
    qc = build_qaoa_circuit(params)
    
    # Transpile for IonQ
    qc_transpiled = transpile(qc, backend=backend, optimization_level=1)
    
    # Run on IonQ
    job = backend.run(qc_transpiled, shots=shots)
    result = job.result()
    counts = result.get_counts()
    
    energy = energy_from_counts(counts)
    print(f"  params: {[round(float(x), 4) for x in params]} -> energy: {round(energy, 4)}")
    return energy

# RUN OPTIMIZATION
print("Starting QAOA optimization on IonQ...")
print("(Each iteration runs a quantum circuit on hardware)\n")

init_params = [0.5] * (2 * p)
result = minimize(
    hardware_eval,
    x0=init_params,
    method='COBYLA',
    options={'maxiter': 6}
)

print(f"\nOptimization complete!")
print(f"Best parameters: {[round(x, 4) for x in result.x]}\n")

# FINAL RUN WITH BEST PARAMETERS
print("Running final circuit with optimized parameters...")
best_params = result.x
final_qc = build_qaoa_circuit(best_params)
final_qc_transpiled = transpile(final_qc, backend=backend, optimization_level=1)

job = backend.run(final_qc_transpiled, shots=shots)
final_result = job.result()
counts = final_result.get_counts()

print(f"Final counts: {counts}\n")

# Get best bitstring
best_bitstring = max(counts, key=counts.get)
best_sample = {v: int(best_bitstring[i]) for i, v in enumerate(var_names)}
best_energy = bqm.energy(best_sample)

# DISPLAY RESULTS
print("="*70)
print("SOLUTION")
print("="*70)
print(f"\nBest bitstring: {best_bitstring}")
print(f"Energy: {best_energy:.2f}\n")

print("Active flows:")
total_cost = 0.0
for v in var_names:
    if best_sample[v] == 1:
        src, dst = v.split('_')[1], v.split('_')[2]
        print(f"  {src} → {dst}")
        if src in sources:
            total_cost += cost[src]

print(f"\nTotal cost: {total_cost:.2f}\n")

print("Demand checks:")
for sink, demand in sinks.items():
    received = sum(best_sample[v] for v in var_names if v.endswith(f"_{sink}"))
    status = "✓" if received >= demand else "✗"
    print(f"  {status} {sink}: {received}/{demand}")

print("\nCapacity checks:")
for src in sources:
    generated = sum(best_sample[v] for v in var_names if v.startswith(f"f_{src}_"))
    status = "✓" if generated <= Gmax[src] else "✗"
    print(f"  {status} {src}: {generated}/{Gmax[src]}")

print("\n" + "="*70)