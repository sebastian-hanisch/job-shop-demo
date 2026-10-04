"""Unabhängiges Orakel für den Job Shop: Vollaufzählung aller Maschinenfolgen mit Längster-Weg-Berechnung (statt
CP-SAT-Kreismodell und statt Giffler-Thompson-Verzweigung) für Cmax - ohne und mit Rüstzeiten; dazu eine
Zulässigkeitsprüfung der Giffler-Thompson-Pläne. Der Satz „aktive Pläne enthalten das Optimum“ gilt nur ohne
Rüstzeiten und wird deshalb nur dort geprüft."""

import itertools
import random

import numpy as np

import jsp_algorithm as A
import jsp_scenario as S
import jsp_scenario_logistik as SL


def _longest_path(n, m, routing, proc, seqs, fam, setup):
    pos_of = {(j, int(routing[j, p])): p for j in range(n) for p in range(m)}
    nodes = [(j, p) for j in range(n) for p in range(m)]
    preds = {o: [] for o in nodes}
    for j in range(n):
        for p in range(1, m):
            preds[(j, p)].append(((j, p - 1), 0))
    for k in range(m):
        for a, b in zip(seqs[k], seqs[k][1:]):
            w = int(setup[fam[a]][fam[b]]) if fam is not None else 0
            preds[(b, pos_of[(b, k)])].append(((a, pos_of[(a, k)]), w))
    start, done = {}, 0
    pending = set(nodes)
    while pending:
        ready = [o for o in pending if all(q in start for q, _ in preds[o])]
        if not ready:
            return None                                   # Zyklus: unzulässige Maschinenfolge
        for o in ready:
            start[o] = max([start[q] + int(proc[q]) + w for q, w in preds[o]], default=0)
            pending.discard(o)
    return max(start[o] + int(proc[o]) for o in nodes)


def _brute_force(n, m, routing, proc, fam=None, setup=None):
    values = [_longest_path(n, m, routing, proc, combo, fam, setup)
              for combo in itertools.product(itertools.permutations(range(n)), repeat=m)]
    return min(v for v in values if v is not None)


def _is_feasible(res, routing, proc, fam, setup):
    n, m = routing.shape
    for j in range(n):
        for p in range(m):
            if res.end[j, p] - res.start[j, p] != proc[j, p] or (p and res.start[j, p] < res.end[j, p - 1]):
                return False
    for k in range(m):
        ops = sorted((res.start[j, p], j, p) for j in range(n) for p in range(m) if routing[j, p] == k)
        for a, b in zip(ops, ops[1:]):
            s = int(setup[fam[a[1]], fam[b[1]]]) if fam is not None else 0
            if b[0] < res.end[a[1], a[2]] + s:
                return False
    return res.cmax == res.end.max()


def test_exact_and_active_search_match_brute_force_neutral():
    rng = random.Random(7)
    for _ in range(25):
        n, m = rng.randint(2, 3), rng.randint(2, 3)
        inst = S.generate(n, m, rng.randint(0, 10**6))
        best = _brute_force(n, m, inst.routing, inst.proc)
        res, proven = A.solve_exact(inst.routing, inst.proc, time_limit_seconds=10)
        assert proven and res.cmax == best
        assert A.enumerate_active_schedules(inst.routing, inst.proc) == best        # Giffler-Thompson-Satz
        for prio in (A.mwkr_priority(inst.proc), A.spt_priority(inst.proc), A.fifo_priority):
            g = A.giffler_thompson(inst.routing, inst.proc, prio)
            assert _is_feasible(g, inst.routing, inst.proc, None, None) and g.cmax >= best


def test_exact_and_giffler_thompson_with_setups_match_brute_force():
    rng = random.Random(8)
    for _ in range(20):
        n, m = rng.randint(2, 3), 2
        li = SL.generate(n, m, rng.randint(0, 10**6), n_families=rng.randint(2, 3), setup_time=rng.choice([0, 15, 60]))
        best = _brute_force(n, m, li.routing, li.proc, li.family, li.setup)
        res, proven = A.solve_exact(li.routing, li.proc, li.family, li.setup, 10)
        assert proven and res.cmax == best and _is_feasible(res, li.routing, li.proc, li.family, li.setup)
        g = A.giffler_thompson(li.routing, li.proc, A.mwkr_priority(li.proc), li.family, li.setup)
        assert _is_feasible(g, li.routing, li.proc, li.family, li.setup) and g.cmax >= best


def test_active_schedules_can_miss_the_optimum_with_setups():
    """Gegenbeispiel zum Giffler-Thompson-Satz mit Rüstzeiten (n=3, m=4): die Vollaufzählung der aktiven Pläne liegt
    über dem Optimum der Vollaufzählung aller Maschinenfolgen (app.py behauptet dieses Verfehlen im Text)."""
    li = SL.generate(3, 4, 710865, n_families=2, setup_time=30)
    best = _brute_force(3, 4, li.routing, li.proc, li.family, li.setup)
    assert best == 247
    assert A.enumerate_active_schedules(li.routing, li.proc, li.family, li.setup) == 256
