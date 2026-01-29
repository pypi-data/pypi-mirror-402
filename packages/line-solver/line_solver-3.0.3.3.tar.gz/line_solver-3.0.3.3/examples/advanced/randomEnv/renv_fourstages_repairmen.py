# %%
from line_solver import *
import numpy as np
GlobalConstants.set_verbose(VerboseLevel.STD)
# %%
def renv_genqn(rate, N):
    """Helper function to generate a queueing network for random environment advanced."""
    qnet = Network('qn1')
    
    node = np.empty(2, dtype=object)
    node[0] = Delay(qnet, 'Queue1')
    node[1] = Queue(qnet, 'Queue2', SchedStrategy.PS)
    
    jobclass = np.empty(1, dtype=object)
    jobclass[0] = ClosedClass(qnet, 'Class1', N, node[0], 0)
    
    node[0].set_service(jobclass[0], Exp(rate[0]))
    node[1].set_service(jobclass[0], Exp(rate[1]))
    
    P = qnet.init_routing_matrix()
    P.set(jobclass[0], jobclass[0], [[0, 1], [1, 0]])
    qnet.link(P)
    
    return qnet
# %%
# Model parameters
N = 30  # Job population
M = 3   # Number of stations
E = 4   # Number of environment stages

# Create environment model
envModel = Environment('MyEnv', E)
envName = ['Stage1', 'Stage2', 'Stage3', 'Stage4']
envType = ['UP', 'DOWN', 'FAST', 'SLOW']

# Create rate matrix
rate = np.ones((M, E))
rate[M-1, :] = np.arange(1, E+1)  # rate(M,1:E)=(1:E)
rate[0, :] = np.arange(E, 0, -1)  # rate(1,1:E)=(E:-1:1)

print(f"Rate matrix:")
print(rate)
# %%
# Create queueing networks for each environment stage
qn1 = renv_genqn(rate[:, 0], N)
qn2 = renv_genqn(rate[:, 1], N)
qn3 = renv_genqn(rate[:, 2], N)
qn4 = renv_genqn(rate[:, 3], N)
envSubModel = [qn1, qn2, qn3, qn4]

# Add stages to environment model
for e in range(E):
    envModel.add_stage(e, envName[e], envType[e], envSubModel[e])
# %%
# Define environment transition rates
envRates = np.array([[0, 1, 0, 0],
                     [0, 0, 1, 1],
                     [1, 0, 0, 1],
                     [1, 1, 0, 0]]) / 2

print(f"Environment transition rates:")
print(envRates)

# Add transitions with APH distributions
for e in range(E):
    for h in range(E):
        if envRates[e, h] > 0:
            # Use Erlang distribution as approximation for APH.fitMeanAndSCV
            mean_time = 1.0 / envRates[e, h]
            # APH.fit_mean_and_scv(mean, 0.5) approximated with Erlang of order 2
            envModel.add_transition(e, h, Erlang.fit_mean_and_order(mean_time, 2))
# %% [markdown]
# The metasolver considers an environment with 4 stages and a queueing network with 3 stations.
# Every time the stage changes, the queueing network will modify the service rates of the stations.
# %%
# Create solvers for each submodelsolvers = np.empty(E, dtype=object)for e in range(E):    solvers[e] = FLD(envSubModel[e])# Create environment solverenvSolver = ENV(envModel, solvers)# Get resultstry:    # Note: Some methods may not be fully implemented in Python version    avgTable = envSolver.ensemble_avg()    print("Average performance metrics:")    print(avgTable)        # Try to get ensemble average tables    try:        ensembleAvgTables = envSolver.ensemble_avg_tables()        print("\nEnsemble average tables:")        print(ensembleAvgTables)    except:        print("\nEnsemble average tables not available in this version")        except Exception as e:    print(f"Error during solving: {e}")    print("Note: Some environment solver features may not be fully implemented in the Python version")