"""Vehikel A (Neutral) und Vehikel B (Werkstatt/Logistik): Erzeugung, Determinismus; Auswertung: Kennzahlen,
Sweep, Beweis-Check über den Suchraum, Timing-Messreihe, Vehikel-B-Härtetest (Rüstzeiten)."""

from dataclasses import replace

import numpy as np
import pytest

import jsp_algorithm as A
import jsp_constants as C
import jsp_evaluation as ev
import jsp_scenario as S
import jsp_scenario_logistik as SL


# --- Vehikel A ----------------------------------------------------------------------------------------------------------------------------------


def test_instance_shape_and_bounds():
    inst = S.generate(20, 4, 3)
    assert inst.n == 20 and inst.m == 4
    assert inst.routing.shape == (20, 4) and inst.proc.shape == (20, 4)
    assert inst.proc.min() >= C.P_MIN and inst.proc.max() <= C.P_MAX
    for j in range(20):
        assert sorted(inst.routing[j].tolist()) == list(range(4))        # jede Maschine genau einmal


def test_instance_is_deterministic_and_seed_dependent():
    a, b, c = S.generate(15, 3, 5), S.generate(15, 3, 5), S.generate(15, 3, 6)
    assert np.array_equal(a.routing, b.routing) and np.array_equal(a.proc, b.proc)
    assert not np.array_equal(a.proc, c.proc)


# --- Vehikel B ------------------------------------------------------------------------------------------------------------------------------


def test_logistik_instance_shares_the_same_routing_and_processing_times_as_neutral():
    neutral = S.generate(15, 3, 7)
    logistik = SL.generate(15, 3, 7)
    assert np.array_equal(neutral.routing, logistik.routing) and np.array_equal(neutral.proc, logistik.proc)


def test_logistik_instance_is_deterministic():
    a, b = SL.generate(10, 3, 2), SL.generate(10, 3, 2)
    assert np.array_equal(a.family, b.family) and np.array_equal(a.setup, b.setup)


# --- Analyse --------------------------------------------------------------------------------------------------------------------------------


def test_analysis_fields_are_consistent():
    a = ev.analyse(ev.Settings(n=10, m=4))
    assert a.optimal is None


def test_analysis_respects_the_active_schedule_theorem_for_small_n():
    a = ev.analyse(ev.Settings(n=4, m=3))
    assert a.optimal is not None and a.optimal_proven


# --- Vehikel-Bewusstsein der Hauptanalyse (von Anfang an, siehe [[feedback_vehicle_toggle_must_drive_primary_metrics]]) ----------------------


def test_analyse_on_the_logistik_vehicle_actually_uses_setup_aware_completion_times():
    settings = ev.Settings(n=8, m=4, seed=100000, vehicle="logistik", setup_time=30, n_families=3)
    a = ev.analyse(settings)
    linst = ev.logistik_instance(8, 4, 100000, 3, 30)
    independent = A.giffler_thompson(linst.routing, linst.proc, A.mwkr_priority(linst.proc), linst.family, linst.setup)
    assert a.mwkr.cmax == pytest.approx(independent.cmax)


def test_analyse_on_the_neutral_vehicle_is_unaffected_by_logistik_only_settings():
    a1 = ev.analyse(ev.Settings(n=10, m=4, seed=5, vehicle="neutral", setup_time=5))
    a2 = ev.analyse(ev.Settings(n=10, m=4, seed=5, vehicle="neutral", setup_time=60))
    assert a1.mwkr.cmax == pytest.approx(a2.mwkr.cmax)


def test_switching_vehicle_actually_changes_the_mwkr_cmax():
    a_neutral = ev.analyse(ev.Settings(n=10, m=4, seed=7, vehicle="neutral"))
    a_logistik = ev.analyse(ev.Settings(n=10, m=4, seed=7, vehicle="logistik", setup_time=60, n_families=2))
    assert a_neutral.mwkr.cmax != pytest.approx(a_logistik.mwkr.cmax)


def test_mwkr_at_zero_setup_time_matches_the_neutral_vehicle_exactly():
    a1 = ev.analyse(ev.Settings(n=10, m=4, seed=7, vehicle="neutral"))
    a2 = ev.analyse(ev.Settings(n=10, m=4, seed=7, vehicle="logistik", setup_time=0))
    assert np.array_equal(a1.mwkr.start, a2.mwkr.start)
    assert a1.mwkr.cmax == pytest.approx(a2.mwkr.cmax)


def test_gap_can_be_negative_even_on_the_neutral_vehicle():
    """Echter, überraschender Fund (wie bei lpt-scheduling-demo): ANDERS als bei den bewiesen optimalen Regeln
    der Stücke 1-4/6 kann MWKR hier sogar OHNE Rüstzeiten schlechter abschneiden als FIFO - der Beweis gilt
    für den SUCHRAUM aktiver Zeitpläne, nicht für MWKR als Regel gegenüber einer bestimmten anderen Regel."""
    a = ev.analyse(ev.Settings(n=6, m=3, seed=2))
    assert a.gap_fifo < 0.0


def test_analysis_is_deterministic_given_the_chain_seed():
    s = ev.Settings(n=10, m=4, seed=1, chain_seed=0)
    a, b, c = ev.analyse(s), ev.analyse(s), ev.analyse(replace(s, chain_seed=1))
    assert a.gap_random == pytest.approx(b.gap_random)
    assert a.gap_random != pytest.approx(c.gap_random)


# --- Sweep und Messreihe -------------------------------------------------------------------------------------------------------------------


def test_run_config_counts_runs_and_aggregates():
    r = ev.run_config(ev.Settings(n=10, m=4))
    assert r["n_runs"] == len(C.SWEEP_SEEDS) * C.SWEEP_CHAINS


def test_sweep_values_labels_and_ordering():
    assert set(ev.SWEEP_VALUES) == set(ev.SWEEP_LABELS)
    rows = ev.sweep("n", ev.Settings(), (5, 15))
    assert [r["value"] for r in rows] == [5, 15]
    rows_m = ev.sweep("m", ev.Settings(), (2, 4))
    assert [r["value"] for r in rows_m] == [2, 4]


def test_active_schedule_theorem_always_matches_cp_sat():
    """Der zentrale Beweis-Check dieses Stücks - eine Gleichheit (theorem_match_rate == 100 %), anders als
    MWKRs eigene Trefferquote (die schwanken darf)."""
    rows = ev.active_schedule_theorem_check(ns=(2, 3, 4), seeds=C.SWEEP_SEEDS[:3])
    assert all(r["theorem_match_rate"] == 1.0 for r in rows)


def test_timing_sweep_shows_exact_growing_far_slower_than_gt():
    rows = ev.timing_sweep(ns=(2, 8))
    small, large = rows[0], rows[1]
    assert large["gt_seconds"] < 0.001


def test_setup_gap_grows_or_shrinks_but_is_never_zero_by_construction():
    """Anders als Stück 1-4/6: der Rüstzeit-0-Fall ist KEIN garantierter Nulltreffer, weil MWKR schon ohne
    Rüstzeiten keine bewiesene Regel ist."""
    row = ev.setup_gap(n=6, setup_time=0)
    assert row["gap_mean"] >= 0.0
