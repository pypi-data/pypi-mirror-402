#!/usr/bin/env python3
"""Debug servt_classes_updmap to see which layer provides activity results"""

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
    solver._build_layers()

    lqn = solver.lqn
    print("=== LQN Structure ===")
    print(f"  nhosts={lqn.nhosts}, ntasks={lqn.ntasks}, nentries={lqn.nentries}, nacts={lqn.nacts}, ncalls={lqn.ncalls}")
    print(f"  tshift={lqn.tshift}, eshift={lqn.eshift}, ashift={lqn.ashift}")

    print("\n=== servt_classes_updmap ===")
    print("  Format: [model_idx, aidx, nodeidx, classidx]")
    if solver.servt_classes_updmap is not None:
        for row in solver.servt_classes_updmap:
            idx, aidx, nodeidx, classidx = int(row[0]), int(row[1]), int(row[2]), int(row[3])
            layer_idx = int(solver.idxhash[idx])
            layer_name = solver.ensemble[layer_idx].name if 0 <= layer_idx < len(solver.ensemble) else "?"
            # Get activity name
            act_name = lqn.hashnames.get(aidx, f"idx_{aidx}") if hasattr(lqn, 'hashnames') and isinstance(lqn.hashnames, dict) else f"idx_{aidx}"
            print(f"  [{idx}] aidx={aidx} ({act_name}), nodeidx={nodeidx}, classidx={classidx}, layer={layer_name} (layer_idx={layer_idx})")

    print("\n=== idxhash mapping ===")
    for i in range(len(solver.idxhash)):
        if not (solver.idxhash[i] == float('nan') or (hasattr(solver.idxhash[i], 'item') and solver.idxhash[i] != solver.idxhash[i])):
            val = solver.idxhash[i]
            if val >= 0 and val < len(solver.ensemble):
                layer_name = solver.ensemble[int(val)].name
                print(f"  idx={i} -> layer={int(val)} ({layer_name})")

    # Print what each layer's model index (idx) corresponds to
    print("\n=== Layer idx values ===")
    for e, layer in enumerate(solver.ensemble):
        if layer is None:
            continue
        # Find which idx maps to this layer
        for i in range(len(solver.idxhash)):
            if solver.idxhash[i] == e:
                print(f"  Layer {e} ({layer.name}): idx={i}")
                break

if __name__ == '__main__':
    main()
