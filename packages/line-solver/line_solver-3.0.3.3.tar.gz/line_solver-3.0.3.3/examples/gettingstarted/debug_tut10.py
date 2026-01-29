#!/usr/bin/env python3
"""Debug script for tut10 layer model analysis"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from line_solver.layered import LayeredNetwork, Processor, Task, Entry, Activity
from line_solver.constants import SchedStrategy
from line_solver.distributions import Exp
from line_solver.solvers import LN, MVA

def main():
    # Create the layered network model
    model = LayeredNetwork('ClientDBSystem')

    # Create processors
    P1 = Processor(model, 'ClientProcessor', 1, SchedStrategy.PS)
    P2 = Processor(model, 'DBProcessor', 1, SchedStrategy.PS)

    # Create tasks
    T1 = Task(model, 'ClientTask', 10, SchedStrategy.REF).on(P1)
    T1.set_think_time(Exp.fit_mean(5.0))
    T2 = Task(model, 'DBTask', float('inf'), SchedStrategy.INF).on(P2)

    # Create entries
    E1 = Entry(model, 'ClientEntry').on(T1)
    E2 = Entry(model, 'DBEntry').on(T2)

    # Define activities
    A1 = Activity(model, 'ClientActivity', Exp.fit_mean(1.0)).on(T1)
    A1.bound_to(E1).synch_call(E2, 2.5)

    A2 = Activity(model, 'DBActivity', Exp.fit_mean(0.8)).on(T2)
    A2.bound_to(E2).replies_to(E2)

    # Create solver
    solver = LN(model, lambda m: MVA(m))

    # Build layers but don't iterate yet
    solver._build_layers()

    # Print layer details
    print(f"\n=== Number of layers: {solver.nlayers} ===")
    print(f"=== Ensemble size: {len(solver.ensemble)} ===\n")

    for e, layer in enumerate(solver.ensemble):
        if layer is None:
            continue
        print(f"\n--- Layer {e}: {layer.name} ---")
        print(f"  clientIdx: {layer.attribute.get('clientIdx')}")
        print(f"  serverIdx: {layer.attribute.get('serverIdx')}")
        print(f"  ishost: {layer.attribute.get('ishost')}")

        nodes = layer.get_nodes()
        classes = layer.get_classes()

        print(f"\n  Nodes ({len(nodes)}):")
        for i, node in enumerate(nodes):
            print(f"    [{i+1}] {node.name} ({type(node).__name__})")

        print(f"\n  Classes ({len(classes)}):")
        for cls in classes:
            pop = cls.number_of_jobs if hasattr(cls, 'number_of_jobs') else 0
            attr = cls.attribute if hasattr(cls, 'attribute') else None
            print(f"    {cls.name}: pop={pop}, attr={attr}")

            # Print service times at each node
            for i, node in enumerate(nodes):
                if hasattr(node, 'service_processes') and node.service_processes:
                    servt = node.service_processes.get(cls.index - 1) if cls.index - 1 < len(node.service_processes) else None
                    if servt is None and hasattr(node, 'get_service'):
                        try:
                            servt = node.get_service(cls)
                        except:
                            servt = None
                    if servt is not None:
                        if hasattr(servt, 'getMean'):
                            mean = servt.getMean()
                        elif hasattr(servt, 'mean'):
                            mean = servt.mean
                        else:
                            mean = str(servt)
                        print(f"      @ {node.name}: {type(servt).__name__}(mean={mean})")

    # Now run the solver and check first iteration results
    print("\n\n=== Running solver iteration 1 ===")
    solver.iterate()

    # Print first iteration results for each layer
    if solver.results:
        for e, result in enumerate(solver.results[-1]):
            if result is None:
                continue
            layer = solver.ensemble[e]
            print(f"\n--- Layer {e} ({layer.name}) results ---")

            RN = result.get('RN')
            WN = result.get('WN')
            TN = result.get('TN')
            UN = result.get('UN')

            classes = layer.get_classes()
            nodes = layer.get_nodes()

            if RN is not None:
                print(f"  RN (response times per visit):")
                for i, node in enumerate(nodes):
                    for j, cls in enumerate(classes):
                        if RN.shape[0] > i and RN.shape[1] > j:
                            rn = RN[i, j]
                            if rn > 0:
                                print(f"    {node.name}, {cls.name}: RN={rn:.6f}")

            if WN is not None and not (RN is not None and (WN == RN).all()):
                print(f"  WN (residence times):")
                for i, node in enumerate(nodes):
                    for j, cls in enumerate(classes):
                        if WN.shape[0] > i and WN.shape[1] > j:
                            wn = WN[i, j]
                            if wn > 0:
                                print(f"    {node.name}, {cls.name}: WN={wn:.6f}")

            if UN is not None:
                print(f"  UN (utilizations):")
                for i, node in enumerate(nodes):
                    for j, cls in enumerate(classes):
                        if UN.shape[0] > i and UN.shape[1] > j:
                            un = UN[i, j]
                            if un > 0:
                                print(f"    {node.name}, {cls.name}: UN={un:.6f}")

    # Print servt/residt
    print("\n\n=== Activity servt/residt ===")
    lqn = solver.lqn
    for a in range(1, lqn.nacts + 1):
        aidx = lqn.ashift + a
        if solver.servt[aidx] > 0 or solver.residt[aidx] > 0:
            print(f"  Activity {a} (aidx={aidx}): servt={solver.servt[aidx]:.6f}, residt={solver.residt[aidx]:.6f}")

    print("\n=== Call servt/residt ===")
    for cidx in range(1, lqn.ncalls + 1):
        if solver.callservt[cidx] > 0 or solver.callresidt[cidx] > 0:
            print(f"  Call {cidx}: callservt={solver.callservt[cidx]:.6f}, callresidt={solver.callresidt[cidx]:.6f}")

if __name__ == '__main__':
    main()
