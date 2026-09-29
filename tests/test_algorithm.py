"""jsp_algorithm: Giffler-Thompson-Konstruktion, CP-SAT gegen unabhängige Brute-Force-Vollaufzählung (nur für
kleine n), der Beweis-Check über den Suchraum aktiver Zeitpläne, Rüstzeit-Variante, Handrechnung."""

import itertools

import numpy as np
import pytest

import jsp_algorithm as A


def _instance(seed, n, m):
    rng = np.random.default_rng(seed)
    routing = np.array([rng.permutation(m) for _ in range(n)])
    proc = rng.integers(1, 30, size=(n, m)).astype(np.int64)
    return routing, proc


def _brute_force(routing, proc, family=None, setup=None):
    """Alle Permutationen der Operationen je Maschine, nur zulässige (azyklische) Kombinationen ausgewertet."""
    n, m = routing.shape
    ops_per_machine = [[] for _ in range(m)]
    for j in range(n):
        for pos in range(m):
            ops_per_machine[routing[j, pos]].append((j, pos))
    best = None
    for combo in itertools.product(*(list(itertools.permutations(ops)) for ops in ops_per_machine)):
        machine_order = {k: list(combo[k]) for k in range(m)}
        machine_ptr = {k: 0 for k in range(m)}
        job_ptr = {j: 0 for j in range(n)}
        machine_free = [0] * m
        job_free = [0] * n
        prev_family = [None] * m
        end_time = {}
        scheduled, total = 0, n * m
        progress = True
        while scheduled < total and progress:
            progress = False
            for k in range(m):
                if machine_ptr[k] >= len(machine_order[k]):
                    continue
                j, pos = machine_order[k][machine_ptr[k]]
                if job_ptr[j] == pos:
                    s = int(setup[prev_family[k], family[j]]) if family is not None and prev_family[k] is not None else 0
                    st = max(machine_free[k] + s, job_free[j])
                    dur = int(proc[j, pos])
                    end_time[j, pos] = st + dur
                    machine_free[k] = st + dur
                    job_free[j] = st + dur
                    if family is not None:
                        prev_family[k] = family[j]
                    machine_ptr[k] += 1
                    job_ptr[j] += 1
                    scheduled += 1
                    progress = True
        if scheduled < total:
            continue
        cmax = max(end_time.values())
        if best is None or cmax < best:
            best = cmax
    return best


@pytest.mark.parametrize("n,m", [(2, 2), (2, 3), (3, 2), (3, 3)])
def test_cp_sat_matches_brute_force_for_every_seed(n, m):
    for seed in range(5):
        routing, proc = _instance(seed * 10 + n + m, n, m)
        bf = _brute_force(routing, proc)
        result, proven = A.solve_exact(routing, proc, time_limit_seconds=10)
        assert proven
        assert result.cmax == pytest.approx(bf, abs=1e-6)


def test_giffler_thompson_produces_a_feasible_precedence_respecting_schedule():
    routing, proc = _instance(5, 6, 3)
    result = A.giffler_thompson(routing, proc, A.mwkr_priority(proc))
    n, m = routing.shape
    for j in range(n):
        for pos in range(1, m):
            assert result.start[j, pos] >= result.end[j, pos - 1] - 1e-9
    for k in range(m):
        ops_k = sorted([(j, pos) for j in range(n) for pos in range(m) if routing[j, pos] == k], key=lambda jp: result.start[jp])
        for a, b in zip(ops_k, ops_k[1:]):
            assert result.start[b] >= result.end[a] - 1e-9


def test_enumerate_active_schedules_matches_cp_sat_optimum():
    """Der zentrale Beweis-Check dieses Stücks: Giffler & Thompson (1960) - der Suchraum aktiver Zeitpläne
    enthält bewiesen das Optimum. Hier gegen CP-SAT geprüft, nicht nur behauptet."""
    for n, m in [(2, 2), (3, 2), (3, 3), (4, 3)]:
        for seed in range(3):
            routing, proc = _instance(seed * 10 + n + m, n, m)
            best_active = A.enumerate_active_schedules(routing, proc)
            opt, proven = A.solve_exact(routing, proc, time_limit_seconds=10)
            assert proven
            assert best_active == pytest.approx(opt.cmax, abs=1e-6)


def test_mwkr_priority_favours_the_job_with_the_most_remaining_work():
    proc = np.array([[5, 5], [1, 1]])       # Auftrag 0 hat insgesamt mehr Arbeit als Auftrag 1
    priority = A.mwkr_priority(proc)
    assert priority(0, 0) < priority(1, 0)  # kleinerer Wert = höhere Priorität


def test_spt_priority_is_the_processing_time_itself():
    proc = np.array([[5, 2], [1, 9]])
    priority = A.spt_priority(proc)
    assert priority(0, 0) == 5 and priority(1, 0) == 1


def test_fifo_priority_is_the_job_index():
    assert A.fifo_priority(3, 1) == 3


def test_random_priority_is_deterministic_given_the_rng_state():
    a = A.random_priority(5, np.random.default_rng(0))
    b = A.random_priority(5, np.random.default_rng(0))
    assert [a(j, 0) for j in range(5)] == [b(j, 0) for j in range(5)]


def test_mwkr_beats_spt_on_a_hand_picked_instance():
    """Handrechnung: zwei Aufträge, zwei Maschinen. Auftrag 0 hat insgesamt viel Arbeit (8+8), Auftrag 1 wenig
    (1+1). SPT stellt fälschlich den kurzen Auftrag konsequent voran und lässt den langen bis zuletzt liegen -
    MWKR erkennt, dass der lange Auftrag zuerst starten sollte."""
    routing = np.array([[0, 1], [1, 0]])
    proc = np.array([[8, 8], [1, 1]])
    mwkr = A.giffler_thompson(routing, proc, A.mwkr_priority(proc))
    spt = A.giffler_thompson(routing, proc, A.spt_priority(proc))
    assert mwkr.cmax <= spt.cmax


# --- Mit Rüstzeiten (Vehikel B) --------------------------------------------------------------------------------


def test_mwkr_at_zero_setup_time_matches_the_neutral_vehicle_exactly():
    """Die richtige Konsistenzprüfung: MWKR ist keine bewiesene Regel, der Kollaps-Test prüft deshalb NICHT
    'trifft MWKR das Optimum', sondern nur, dass Vehikel B bei Rüstzeit 0 strukturell exakt auf Vehikel A
    zurückfällt."""
    routing, proc = _instance(7, 8, 4)
    rng = np.random.default_rng(1)
    family = rng.integers(0, 3, size=8)
    setup = np.zeros((3, 3))
    neutral = A.giffler_thompson(routing, proc, A.mwkr_priority(proc))
    logistik = A.giffler_thompson(routing, proc, A.mwkr_priority(proc), family, setup)
    assert np.array_equal(neutral.start, logistik.start)
    assert neutral.cmax == pytest.approx(logistik.cmax)


def test_setup_time_is_only_charged_on_a_family_change_on_the_same_machine():
    routing = np.array([[0], [0], [0]])
    proc = np.array([[2], [2], [2]])
    family = np.array([0, 0, 1])
    setup = np.array([[0, 10], [10, 0]])
    result = A.giffler_thompson(routing, proc, A.fifo_priority, family, setup)
    assert result.end[0, 0] == pytest.approx(2)
    assert result.end[1, 0] == pytest.approx(4)
    assert result.end[2, 0] == pytest.approx(4 + 10 + 2)


def test_cp_sat_with_setup_matches_independent_brute_force():
    routing, proc = _instance(11, 3, 3)
    rng = np.random.default_rng(11)
    family = rng.integers(0, 2, size=3)
    setup = np.array([[0, 6], [6, 0]])
    bf = _brute_force(routing, proc, family, setup)
    result, proven = A.solve_exact(routing, proc, family, setup, time_limit_seconds=10)
    assert proven
    assert result.cmax == pytest.approx(bf, abs=1e-6)


def test_cp_sat_setup_matches_no_setup_when_setup_is_zero():
    routing, proc = _instance(13, 4, 3)
    family = np.array([0, 1, 0, 1])
    setup0 = np.zeros((2, 2))
    plain, proven1 = A.solve_exact(routing, proc, time_limit_seconds=10)
    with_setup, proven2 = A.solve_exact(routing, proc, family, setup0, time_limit_seconds=10)
    assert proven1 and proven2
    assert with_setup.cmax == pytest.approx(plain.cmax, abs=1e-6)
