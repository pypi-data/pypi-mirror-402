# %%
from line_solver import *
import numpy as np
GlobalConstants.set_verbose(VerboseLevel.STD)
# %%
def circul(c):
    """Returns a circulant matrix of order c.
    
    Args:
        c: Either an integer (order) or a vector for the first row
        
    Returns:
        numpy.ndarray: Circulant matrix
    """
    if np.isscalar(c):
        if c == 1:
            return np.array([[1]])
        else:
            v = np.zeros(c)
            v[-1] = 1  # Last element = 1
            return circul(v)
    
    # c is a vector
    n = len(c)
    C = np.zeros((n, n))
    
    for i in range(n):
        for j in range(n):
            C[i, j] = c[(j - i) % n]
    
    return C

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
N = 2  # Job population  
M = 2  # Number of stations
E = 3  # Number of environment stages

# Create environment model
envModel = Environment('MyEnv', E)
envName = ['Stage1', 'Stage2', 'Stage3']
envType = ['UP', 'DOWN', 'FAST']

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

envSubModel = [qn1, qn2, qn3]

# Add stages to environment model
for e in range(E):
    envModel.add_stage(e, envName[e], envType[e], envSubModel[e])
# %%
# Define environment transition rates using circulant matrix
envRates = circul(3)  # Creates a 3x3 circulant matrix

print(f"Environment transition rates (circulant matrix):")
print(envRates)

# Add transitions with Erlang distributions
for e in range(E):
    for h in range(E):
        if envRates[e, h] > 0:
            mean_time = 1.0 / envRates[e, h]
            order = e + h  # Erlang order based on stage indices
            if order == 0:
                order = 1  # Minimum order is 1
            envModel.add_transition(e, h, Erlang.fit_mean_and_order(mean_time, order))
# %% [markdown]
# The metasolver considers an environment with 3 stages and a queueing network with 2 stations.
# This example illustrates the computation of the infinitesimal generator of the system.
# %%
# Create solvers for each submodel using CTMCsolvers = np.empty(E, dtype=object)for e in range(E):    solvers[e] = CTMC(envSubModel[e])# Create environment solverenvSolver = ENV(envModel, solvers)# Get resultstry:    # Try to get the generator (infinitesimal generator matrix)    try:        generator_result = envSolver.generator()        print("Infinitesimal generator computation completed")        print(f"Generator result type: {type(generator_result)}")        if hasattr(generator_result, 'shape'):            print(f"Generator shape: {generator_result.shape}")        else:            print(f"Generator result: {generator_result}")    except Exception as gen_error:        print(f"Generator computation error: {gen_error}")        print("Note: getGenerator() may not be fully implemented in Python version")        # Alternative: Get ensemble averages    try:        avgTable = envSolver.ensemble_avg()        print("\nEnsemble average performance metrics:")        print(avgTable)    except Exception as avg_error:        print(f"\nEnsemble average error: {avg_error}")        except Exception as e:    print(f"Error during solving: {e}")    print("Note: Some environment solver features may not be fully implemented in the Python version")