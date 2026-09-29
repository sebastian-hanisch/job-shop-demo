"""Job Shop (allgemeines Modell): n Aufträge, m Maschinen, JEDER Auftrag besucht jede Maschine genau einmal,
aber in AUFTRAGSEIGENER Reihenfolge (anders als Johnson/F2: gleiche Reihenfolge für alle; anders als LPT/Pm: eine
Operation je Auftrag) - der Konvergenzpunkt dieser Linie: Reihenfolge (Stück 1-5) UND serielle Maschinen
(Stück 6) UND parallele Maschinen (Stück 7) kommen hier zusammen. Stark NP-schwer.

Drei Bausteine:
1. **Giffler-Thompson** (1960): konstruiert einen AKTIVEN Zeitplan (keine Operation lässt sich nach links
   schieben, ohne eine andere zu verzögern) mittels einer Prioritätsregel bei jedem "Konflikt" - eine
   Simulation, kein Optimalitätsbeweis. Hier mit SPT als Regel (Wiedersehen mit der Wurzel dieser Linie) und
   FIFO als falsche Regel hier.
2. **Der Beweis, der hier zählt, ist über den SUCHRAUM, nicht über eine Regel**: Giffler & Thompson (1960)
   zeigen, dass die Menge ALLER aktiven Zeitpläne mindestens einen optimalen enthält - `enumerate_active_
   schedules` prüft das empirisch für kleine Instanzen (volle Verzweigung über alle Konfliktauflösungen, nicht
   nur eine Regel).
3. **CP-SAT** als exakte Gegenprobe - ein Kreis-Modell JE MASCHINE (wie `johnson-rule-demo`/`lpt-scheduling-demo`,
   hier aber einfacher: die Operationen je Maschine sind durch die Instanz FEST vorgegeben, keine Zuordnungs-
   Entscheidung mehr nötig) plus Vorrang-Bedingungen zwischen den Operationen jedes Auftrags."""

import os
from dataclasses import dataclass

import numpy as np
from ortools.sat.python import cp_model

NUM_SEARCH_WORKERS = min(8, os.cpu_count() or 1)  # NIE hart auf eine Zahl setzen - siehe project memory
# (weighted-tardiness-demo brach auf einem 4-Kern-CI-Runner durch Oversubscription bei hart kodierten 8 Workern)


@dataclass
class Result:
    start: np.ndarray          # (n, m): Startzeit je Operation
    end: np.ndarray            # (n, m): Fertigstellung je Operation
    cmax: float
    machine_finish: np.ndarray  # (m,): Fertigstellung der letzten Operation je Maschine


def _schedulable(routing, job_ptr):
    n, m = routing.shape
    return [(j, job_ptr[j]) for j in range(n) if job_ptr[j] < m]


def _setup_cost(family, setup, prev_family_on_machine, j):
    if family is None or prev_family_on_machine is None:
        return 0
    return int(setup[prev_family_on_machine, family[j]])


def giffler_thompson(routing, proc, priority, family=None, setup=None):
    """Konstruiert EINEN aktiven Zeitplan. `priority(j, pos)` bewertet einen Kandidaten - kleiner heißt höhere
    Priorität im Konfliktfall. Mit Familien/Rüstzeit (Vehikel B) kostet ein Familienwechsel auf DERSELBEN
    Maschine zusätzliche Zeit, bevor die nächste Operation dort beginnt."""
    n, m = routing.shape
    job_ptr = [0] * n
    job_free = np.zeros(n)
    machine_free = np.zeros(m)
    prev_family_on_machine = [None] * m
    start = np.zeros((n, m))
    end = np.zeros((n, m))
    for _ in range(n * m):
        ops = _schedulable(routing, job_ptr)
        best = None
        for (j, pos) in ops:
            k = routing[j, pos]
            s = _setup_cost(family, setup, prev_family_on_machine[k], j)
            st = max(job_free[j], machine_free[k] + s)
            ct = st + proc[j, pos]
            if best is None or ct < best[0]:
                best = (ct, k)
        cstar, mstar = best
        conflict = []
        for (j, pos) in ops:
            k = routing[j, pos]
            if k != mstar:
                continue
            s = _setup_cost(family, setup, prev_family_on_machine[k], j)
            st = max(job_free[j], machine_free[k] + s)
            if st < cstar:
                conflict.append((j, pos))
        j, pos = min(conflict, key=lambda jp: priority(jp[0], jp[1]))
        k = routing[j, pos]
        s = _setup_cost(family, setup, prev_family_on_machine[k], j)
        st = max(job_free[j], machine_free[k] + s)
        start[j, pos], end[j, pos] = st, st + proc[j, pos]
        job_free[j] = end[j, pos]
        machine_free[k] = end[j, pos]
        if family is not None:
            prev_family_on_machine[k] = family[j]
        job_ptr[j] += 1
    machine_finish = np.zeros(m)
    for j in range(n):
        for pos in range(m):
            machine_finish[routing[j, pos]] = max(machine_finish[routing[j, pos]], end[j, pos])
    return Result(start, end, float(end.max()), machine_finish)


def mwkr_priority(proc):
    """Most Work Remaining: die verbleibende Bearbeitungszeit des Auftrags (diese UND alle folgenden
    Operationen) - je mehr Arbeit noch aussteht, desto höher die Priorität. Empirisch die beste einfache Regel
    für Cmax im Job Shop (Pinedo, "Scheduling") - anders als SPT, das für EINE Maschine (Stück 1 dieser Linie)
    beweisbar optimal ist, hier aber nachweislich SCHLECHTER abschneidet als sogar FIFO (siehe Messreihe/README):
    SPT lässt lange Aufträge systematisch bis zuletzt liegen, was gerade bei Cmax bestraft wird."""
    def key(j, pos):
        return -float(proc[j, pos:].sum())
    return key


def spt_priority(proc):
    return lambda j, pos: proc[j, pos]


def fifo_priority(j, pos):
    return j


def random_priority(n, rng):
    order = rng.permutation(n)
    rank = {j: r for r, j in enumerate(order)}
    return lambda j, pos: rank[j]


# --- Beweis über den Suchraum: enthalten aktive Zeitpläne wirklich das Optimum? ---------------------------------


def enumerate_active_schedules(routing, proc, family=None, setup=None, max_leaves=200_000):
    """Volle Verzweigung über ALLE Konfliktauflösungen (nicht nur eine Regel) - liefert das Minimum über JEDEN
    aktiven Zeitplan. NUR für kleine Instanzen praktikabel (siehe jsp_constants.ACTIVE_CHECK_NS) - `max_leaves`
    ist ein Sicherheitsnetz, das die Suche abbricht, falls eine Instanz doch explodiert."""
    n, m = routing.shape
    best = [None]
    leaves = [0]

    def rec(job_ptr, job_free, machine_free, prev_family, scheduled):
        if leaves[0] > max_leaves:
            return
        if scheduled == n * m:
            leaves[0] += 1
            cmax = max(job_free)
            if best[0] is None or cmax < best[0]:
                best[0] = cmax
            return
        ops = _schedulable(routing, job_ptr)
        b = None
        for (j, pos) in ops:
            k = routing[j, pos]
            s = _setup_cost(family, setup, prev_family[k], j)
            st = max(job_free[j], machine_free[k] + s)
            ct = st + proc[j, pos]
            if b is None or ct < b[0]:
                b = (ct, k)
        cstar, mstar = b
        conflict = []
        for (j, pos) in ops:
            k = routing[j, pos]
            if k != mstar:
                continue
            s = _setup_cost(family, setup, prev_family[k], j)
            st = max(job_free[j], machine_free[k] + s)
            if st < cstar:
                conflict.append((j, pos))
        for (j, pos) in conflict:
            k = routing[j, pos]
            s = _setup_cost(family, setup, prev_family[k], j)
            st = max(job_free[j], machine_free[k] + s)
            new_job_free = list(job_free)
            new_job_free[j] = st + proc[j, pos]
            new_machine_free = list(machine_free)
            new_machine_free[k] = st + proc[j, pos]
            new_job_ptr = list(job_ptr)
            new_job_ptr[j] += 1
            new_prev_family = list(prev_family)
            if family is not None:
                new_prev_family[k] = family[j]
            rec(new_job_ptr, new_job_free, new_machine_free, new_prev_family, scheduled + 1)

    rec([0] * n, [0.0] * n, [0.0] * m, [None] * m, 0)
    return best[0]


# --- CP-SAT (exakte Gegenprobe, ein Modell für beide Vehikel) ---------------------------------------------------


def solve_exact(routing, proc, family=None, setup=None, time_limit_seconds=15.0):
    """Ein Kreis-Modell JE MASCHINE - anders als `lpt-scheduling-demo` (Zuordnung + Reihenfolge) ist hier NUR
    die Reihenfolge je Maschine frei, welche Operationen zu welcher Maschine gehören legt die Instanz (das
    Routing) fest. Zusätzlich Vorrang-Bedingungen zwischen den Operationen jedes Auftrags (job's eigene
    Reihenfolge über die Maschinen). Bei Rüstzeit 0 kollabiert dasselbe Modell exakt zum rüstzeitfreien Fall."""
    n, m = routing.shape
    if family is None:
        family = np.zeros(n, dtype=np.int64)
        setup = np.zeros((1, 1), dtype=np.int64)
    horizon = int(np.sum(proc)) + int(np.max(setup)) * n * m + 1

    model = cp_model.CpModel()
    start = {}
    end = {}
    for j in range(n):
        for pos in range(m):
            start[j, pos] = model.NewIntVar(0, horizon, f"s{j}_{pos}")
            end[j, pos] = model.NewIntVar(0, horizon, f"e{j}_{pos}")
            model.Add(end[j, pos] == start[j, pos] + int(proc[j, pos]))
            if pos > 0:
                model.Add(start[j, pos] >= end[j, pos - 1])

    ops_per_machine = [[] for _ in range(m)]
    for j in range(n):
        for pos in range(m):
            ops_per_machine[routing[j, pos]].append((j, pos))

    for k in range(m):
        ops = ops_per_machine[k]
        arcs = []
        for idx, (j, pos) in enumerate(ops):
            lit = model.NewBoolVar(f"a0_{k}_{idx}")
            arcs.append((0, idx + 1, lit))
            lit_back = model.NewBoolVar(f"a{k}_{idx}_0")
            arcs.append((idx + 1, 0, lit_back))
        for i2, (j1, p1_) in enumerate(ops):
            for j2idx, (j2, p2_) in enumerate(ops):
                if i2 == j2idx:
                    continue
                lit = model.NewBoolVar(f"a{k}_{i2}_{j2idx}")
                arcs.append((i2 + 1, j2idx + 1, lit))
                s = int(setup[family[j1], family[j2]])
                model.Add(start[j2, p2_] >= end[j1, p1_] + s).OnlyEnforceIf(lit)
        model.AddCircuit(arcs)

    cmax = model.NewIntVar(0, horizon, "cmax")
    model.AddMaxEquality(cmax, list(end.values()))
    model.Minimize(cmax)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = NUM_SEARCH_WORKERS
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None, False

    start_arr = np.zeros((n, m))
    end_arr = np.zeros((n, m))
    machine_finish = np.zeros(m)
    for j in range(n):
        for pos in range(m):
            start_arr[j, pos] = solver.Value(start[j, pos])
            end_arr[j, pos] = solver.Value(end[j, pos])
            machine_finish[routing[j, pos]] = max(machine_finish[routing[j, pos]], end_arr[j, pos])
    result = Result(start_arr, end_arr, float(solver.Value(cmax)), machine_finish)
    return result, status == cp_model.OPTIMAL
