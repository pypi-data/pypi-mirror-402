# %%
from line_solver import *
import numpy as np
GlobalConstants.set_verbose(VerboseLevel.STD)
# %%
# Create network
model = Network('model')

# Block 1: nodes
node = np.empty(3, dtype=object)
node[0] = Delay(model, 'Delay')
node[1] = Queue(model, 'Queue1', SchedStrategy.PS)
node[2] = Queue(model, 'Queue2', SchedStrategy.PS)

# Block 2: classes (1 job each)
jobclass = np.empty(2, dtype=object)
jobclass[0] = ClosedClass(model, 'Class1', 1, node[0], 0)
jobclass[1] = ClosedClass(model, 'Class2', 1, node[0], 0)

print("Network created with 3 nodes and 2 classes (1 job each)")
print(f"  {node[0].get_name()}: Delay node")
print(f"  {node[1].get_name()}: PS Queue")
print(f"  {node[2].get_name()}: PS Queue")
# %%
# Set advanced service distributions
# Delay node - mixed distributions
node[0].set_service(jobclass[0], Erlang.fit_mean_and_order(3, 2))  # Erlang with mean=3, shape=2
node[0].set_service(jobclass[1], HyperExp(0.5, 3.0, 10.0))     # HyperExp with prob=0.5, rates=3.0,10.0
print("Delay node distributions:")
print("  Class1: Erlang(mean=3, shape=2) - Low variability")
print("  Class2: HyperExp(p=0.5, λ1=3, λ2=10) - High variability")

# Queue1 - HyperExp and MMPP2
node[1].set_service(jobclass[0], HyperExp(0.1, 1.0, 10.0))     # HyperExp with prob=0.1, rates=1.0,10.0
node[1].set_service(jobclass[1], MMPP2(1, 2, 3, 4))           # MMPP2 with parameters λ0=1, λ1=2, σ01=3, σ10=4
print("\nQueue1 distributions:")
print("  Class1: HyperExp(p=0.1, λ1=1, λ2=10) - Very high variability")
print("  Class2: MMPP2(λ0=1, λ1=2, σ01=3, σ10=4) - Markov Modulated Poisson Process")

# Queue2 - HyperExp and Erlang
node[2].set_service(jobclass[0], HyperExp(0.1, 1.0, 10.0))     # Same as Queue1 for Class1
node[2].set_service(jobclass[1], Erlang(1, 2))                 # Erlang with rate=1, shape=2
print("\nQueue2 distributions:")
print("  Class1: HyperExp(p=0.1, λ1=1, λ2=10) - Same as Queue1")
print("  Class2: Erlang(rate=1, shape=2) - Low variability")
# %%
# Set up connectivity
model.add_link(node[0], node[0])  # Delay can route to itself
model.add_link(node[0], node[1])  # Delay -> Queue1
model.add_link(node[0], node[2])  # Delay -> Queue2
model.add_link(node[1], node[0])  # Queue1 -> Delay
model.add_link(node[2], node[0])  # Queue2 -> Delay

print("\n=== Configuring Routing Strategies ===")

# Class1: Probabilistic routing from Delay
node[0].set_prob_routing(jobclass[0], node[0], 0.0)  # No self-loop for Class1
node[0].set_prob_routing(jobclass[0], node[1], 0.3)  # 30% to Queue1
node[0].set_prob_routing(jobclass[0], node[2], 0.7)  # 70% to Queue2
node[1].set_prob_routing(jobclass[0], node[0], 1.0)  # Queue1 -> Delay (deterministic)
node[2].set_prob_routing(jobclass[0], node[0], 1.0)  # Queue2 -> Delay (deterministic)

print("Class1 routing (Probabilistic):")
print("  From Delay: 30% Queue1, 70% Queue2")
print("  From Queues: 100% back to Delay")

# Class2: Random routing strategy
node[0].set_routing(jobclass[1], RoutingStrategy.RAND)  # Random from Delay
node[1].set_routing(jobclass[1], RoutingStrategy.RAND)  # Random from Queue1
node[2].set_routing(jobclass[1], RoutingStrategy.RAND)  # Random from Queue2

print("\nClass2 routing (Random):")
print("  All nodes use random routing among connected destinations")
# Note: When using add_link() + set_prob_routing()/set_routing(),
# do NOT call model.link(P) - routing is already configured.

print("Routing configured successfully")
print("\nModel configuration complete!")
# %%
# Aligned with JAR test scenarios for cqn_mmpp2_service
# JAR tests: JMT(seed=23000), DES(seed=23000)

# Configure solvers
solver = np.array([], dtype=object)

# JMT with seed=23000 (matches JAR)
solver = np.append(solver, JMT(model, seed=23000))

# DES with seed=23000 (matches MATLAB)
solver = np.append(solver, DES(model, seed=23000))

print("Solvers configured with seed=23000 (matches JAR)")
# %%
# Solve with each solver
for s in range(len(solver)):
    print(f'\n=== SOLVER: {solver[s].get_name()} ===')
    avg_table = solver[s].avg_table()
    print(avg_table)