# %%
from line_solver import *
GlobalConstants.set_verbose(VerboseLevel.STD)
# %%
model = Network('M/M/1')
# Block 1: nodes
source = Source(model, 'mySource')
queue = Queue(model, 'myQueue', SchedStrategy.FCFS)
sink = Sink(model, 'mySink')
# Block 2: classes
jobclass = OpenClass(model, 'myClass')
source.set_arrival(jobclass, Exp(1))
queue.set_service(jobclass, Exp(2))
# Block 3: topology
model.link(Network.serial_routing(source, queue, sink))
# %%
# Block 4: solution
AvgTable = JMT(model, seed=23000, samples=10000, verbose=VerboseLevel.SILENT).avg_table()
# %%
# select a particular table row
print(tget(AvgTable, queue, jobclass))
# %%
# select a particular table row by node and class label
print(tget(AvgTable, 'myQueue', 'myClass'))
# %%
print(AvgTable['RespT'].tolist())
# %%
print(tget(AvgTable,'myQueue','myClass')['RespT'].tolist())