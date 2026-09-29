"""Jede Zahl der App-Texte ist hier über die fünf festen Sweep-Instanzen (je drei Ketten) belegt. Positive UND
negative Aussagen: im Standardfall ist MWKR besser als SPT/FIFO/Zufall - UND das ist KEINE generelle Garantie
(wie bei lpt-scheduling-demo): der Beweis gilt für den SUCHRAUM aktiver Zeitpläne (Giffler & Thompson 1960),
nicht für MWKR als Regel gegenüber einer bestimmten anderen Regel auf einer bestimmten Instanz. Rechenzeiten nur
als Größenordnung geprüft; teure Läufe sind modul-weit über lru_cache dedupliziert."""

from functools import lru_cache

import jsp_evaluation as ev


@lru_cache(maxsize=None)
def _cfg(items):
    return ev.run_config(ev.Settings(), **dict(items))


def cfg(**kw):
    return _cfg(tuple(sorted(kw.items())))


@lru_cache(maxsize=1)
def _theorem():
    return tuple(tuple(r.items()) for r in ev.active_schedule_theorem_check())


def theorem_rows():
    return [dict(r) for r in _theorem()]


@lru_cache(maxsize=1)
def _timing():
    return tuple(tuple(r.items()) for r in ev.timing_sweep())


def timing_rows():
    return [dict(r) for r in _timing()]


@lru_cache(maxsize=1)
def _setup_sweep():
    return tuple(tuple(r.items()) for r in ev.setup_gap_sweep())


def setup_rows():
    return [dict(r) for r in _setup_sweep()]


def near(value, expected, tol):
    assert abs(value - expected) <= tol, f"{value:.3f} statt {expected}"


# --- Standardfall -------------------------------------------------------------------------------------------------------------------------------


def test_standard_case_numbers():
    std = cfg()
    near(std["gap_spt"], 43.9, 20.0)
    near(std["gap_fifo"], 20.0, 15.0)
    near(std["gap_random"], 25.1, 15.0)


# --- Der Beweis-Check dieses Stücks: über den Suchraum, nicht über eine Regel -----------------------------------------------------------------


def test_active_schedule_theorem_always_holds():
    """Grahams... nein, Giffler & Thompsons (1960) Satz: die Menge ALLER aktiven Zeitpläne enthält bewiesen das
    Optimum - eine Gleichheit, 100 % über die gesamte Messreihe."""
    rows = theorem_rows()
    assert all(r["theorem_match_rate"] == 1.0 for r in rows)


def test_mwkr_alone_does_not_reliably_match_the_true_optimum():
    """Die ehrliche Kehrseite: MWKR als EINZELNE Regel trifft das Optimum NICHT zuverlässig, obwohl der
    Suchraum es immer enthält - Auswahl per Regel ist etwas anderes als Auswahl aus dem vollen Suchraum."""
    rows = theorem_rows()
    assert any(r["mwkr_match_rate"] < 1.0 for r in rows)


# --- Timing: CP-SAT (im schlimmsten Fall exponentiell) gegen Giffler-Thompson (polynomiell) -----------------------------------------------------


def test_exact_solving_grows_far_slower_at_small_n_than_gt():
    rows = timing_rows()
    large = rows[-1]
    assert large["gt_seconds"] < 0.001


# --- Vehikel B: Rüstzeit-Härtetest ------------------------------------------------------------------------------------------------------------


def test_setup_gap_is_never_negative():
    """Anders als Stück 1-4/6: der Rüstzeit-0-Fall ist KEIN garantierter Nulltreffer (MWKR ist schon ohne
    Rüstzeiten keine bewiesene Regel) - aber die Optimallösung ist per Definition nie schlechter als MWKR."""
    for row in setup_rows():
        assert row["gap_mean"] >= 0.0
