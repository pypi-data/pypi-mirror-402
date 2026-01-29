#!/usr/bin/env python3
"""Debug visit ratios in the layer model"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from line_solver.layered import LayeredNetwork, Processor, Task, Entry, Activity
from line_solver.constants import SchedStrategy
from line_solver.distributions import Exp
from line_solver.solvers import LN, MVA
# sn_get_struct not available directly

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

    print("\n=== Layer 0 (ClientProcessor - Host layer) ===")
    layer = solver.ensemble[0]
    mva = MVA(layer)
    sn = mva._sn  # Get network structure from MVA solver

    print(f"\nNetwork structure:")
    print(f"  nstations={sn.nstations}")
    print(f"  nclasses={sn.nclasses}")
    print(f"  nchains={sn.nchains}")
    print(f"  refstat={sn.refstat}")

    print(f"\nClasses:")
    for i, cls in enumerate(layer.get_classes()):
        print(f"  [{i}] {cls.name}: pop={cls.number_of_jobs if hasattr(cls, 'number_of_jobs') else 0}")

    print(f"\nStations:")
    for i, station in enumerate(layer.get_stations()):
        print(f"  [{i}] {station.name}")

    print(f"\nVisits (sn.visits):")
    if sn.visits:
        for chain_id, visits in sn.visits.items():
            print(f"  Chain {chain_id}: shape={visits.shape}")
            print(f"    {visits}")

    print(f"\nChains:")
    print(f"  sn.chains={sn.chains}")
    print(f"  sn.inchain={sn.inchain}")

    # Run MVA to get results
    mva.run_analyzer()
    result = mva._result

    print(f"\nMVA result keys: {result.keys() if result else 'None'}")

    RN = result.get('RN') if result else None
    WN = result.get('WN') if result else None

    print(f"\nRN (response times):")
    classes = layer.get_classes()
    stations = layer.get_stations()
    if RN is not None:
        for i, station in enumerate(stations):
            for j, cls in enumerate(classes):
                if i < RN.shape[0] and j < RN.shape[1]:
                    rn = RN[i, j]
                    if rn > 0:
                        print(f"  [{i}] {station.name}, [{j}] {cls.name}: RN={rn:.6f}")

    print(f"\nWN (residence times):")
    if WN is not None:
        for i, station in enumerate(stations):
            for j, cls in enumerate(classes):
                if i < WN.shape[0] and j < WN.shape[1]:
                    wn = WN[i, j]
                    if wn > 0:
                        print(f"  [{i}] {station.name}, [{j}] {cls.name}: WN={wn:.6f}")

    print(f"\nRatio WN/RN (should be visits ratio):")
    if RN is not None and WN is not None:
        for i, station in enumerate(stations):
            for j, cls in enumerate(classes):
                if i < RN.shape[0] and j < RN.shape[1]:
                    rn = RN[i, j]
                    wn = WN[i, j] if i < WN.shape[0] and j < WN.shape[1] else 0
                    if rn > 0:
                        ratio = wn / rn if rn > 0 else 0
                        print(f"  [{i}] {station.name}, [{j}] {cls.name}: WN/RN={ratio:.6f}")

if __name__ == '__main__':
    main()
