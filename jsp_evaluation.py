"""Auswertung der Job-Shop-Demo: Giffler-Thompson mit SPT gegen dieselbe Konstruktion mit FIFO (die falsche
Regel hier) und gegen zufällige Prioritäten, gegen CP-SAT als exakte Gegenprobe (nur kleine n), gegen den
Beweis-Check über den Suchraum (enthalten aktive Zeitpläne wirklich das Optimum?), und das Vehikel-B-Experiment
(bleibt SPT nahe am Optimum, sobald Rüstzeiten dazukommen)."""

import time
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

import jsp_algorithm as A
import jsp_constants as C
import jsp_scenario as S
import jsp_scenario_logistik as SL


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    m: int = C.DEFAULT_M
    seed: int = C.DEFAULT_SEED
    chain_seed: int = 0
    vehicle: str = C.DEFAULT_VEHICLE
    setup_time: int = C.DEFAULT_SETUP_TIME
    n_families: int = C.DEFAULT_N_FAMILIES


@lru_cache(maxsize=512)
def instance(n, m, seed):
    return S.generate(n, m, seed)


@lru_cache(maxsize=512)
def logistik_instance(n, m, seed, n_families, setup_time):
    return SL.generate(n, m, seed, n_families=n_families, setup_time=setup_time)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    mwkr: object                # Hauptregel: Most Work Remaining (die beste einfache Regel für Cmax hier)
    spt: object                 # falsche Regel hier - obwohl SPT die Wurzel dieser Linie ist!
    fifo: object                # naive Regel: keine Prioritätsinformation
    random_mean: float
    random_runs: int
    optimal: object             # None, wenn n > EXACT_MAX_N
    optimal_proven: bool

    @property
    def gap_spt(self):
        return _gap(self.spt.cmax, self.mwkr.cmax)

    @property
    def gap_fifo(self):
        return _gap(self.fifo.cmax, self.mwkr.cmax)

    @property
    def gap_random(self):
        return _gap(self.random_mean, self.mwkr.cmax)

    @property
    def mwkr_matches_optimum(self):
        return self.optimal is not None and abs(self.mwkr.cmax - self.optimal.cmax) < 1e-6

    @property
    def mwkr_ratio_to_optimum(self):
        return None if self.optimal is None or self.optimal.cmax <= 1e-9 else self.mwkr.cmax / self.optimal.cmax


def _gap(value, baseline):
    if baseline <= 1e-9:
        return 0.0 if value <= 1e-9 else float(value)
    return 100.0 * (value - baseline) / baseline


def analyse(settings, random_draws=20):
    """Wertet Giffler-Thompson (MWKR-Regel) auf dem gewählten Vehikel aus - Neutral oder Werkstatt/Logistik
    (Rüstzeit beim Familienwechsel je Maschine zählt mit). Von Anfang an vehikel-bewusst UND vorzeichen-
    ehrlich gebaut (Lehren aus Stück 1-7 dieser Linie): keine dieser Regeln ist bewiesen optimal (nur der
    SUCHRAUM aktiver Zeitpläne enthält bewiesen das Optimum) - ein negativer Abstand ist möglich, AUCH auf dem
    neutralen Vehikel."""
    if settings.vehicle == "logistik":
        inst = logistik_instance(settings.n, settings.m, settings.seed, settings.n_families, settings.setup_time)
        routing, proc, family, setup = inst.routing, inst.proc, inst.family, inst.setup

        def ev(priority):
            return A.giffler_thompson(routing, proc, priority, family, setup)

        optimal, proven = (A.solve_exact(routing, proc, family, setup, C.EXACT_TIME_LIMIT_SECONDS)
                            if settings.n <= C.EXACT_MAX_N else (None, False))
    else:
        inst = instance(settings.n, settings.m, settings.seed)
        routing, proc = inst.routing, inst.proc

        def ev(priority):
            return A.giffler_thompson(routing, proc, priority)

        optimal, proven = (A.solve_exact(routing, proc, time_limit_seconds=C.EXACT_TIME_LIMIT_SECONDS)
                            if settings.n <= C.EXACT_MAX_N else (None, False))

    mwkr = ev(A.mwkr_priority(proc))
    spt = ev(A.spt_priority(proc))
    fifo = ev(A.fifo_priority)
    rng = np.random.default_rng(settings.chain_seed)
    random_totals = [ev(A.random_priority(settings.n, rng)).cmax for _ in range(random_draws)]
    return Analysis(settings, inst, mwkr, spt, fifo, float(np.mean(random_totals)), random_draws, optimal, proven)


# --- Sweeps und Tabellen -----------------------------------------------------------------------------------------------------------------------


def _mean(rows, key):
    return float(np.mean([r[key] for r in rows]))


def run_config(base, seeds=C.SWEEP_SEEDS, chains=C.SWEEP_CHAINS, **changes):
    s0 = replace(base, **changes)
    rows = []
    for seed in seeds:
        for ch in range(chains):
            a = analyse(replace(s0, seed=seed, chain_seed=ch))
            rows.append({"gap_spt": a.gap_spt, "gap_fifo": a.gap_fifo, "gap_random": a.gap_random})
    out = {k: _mean(rows, k) for k in rows[0]}
    out["n_runs"] = len(rows)
    return out


SWEEP_VALUES = {"n": (2, 5, 10, 15, 20, 30), "m": (2, 3, 4, 5, 6)}
SWEEP_LABELS = {"n": "Aufträge", "m": "Maschinen"}


def sweep(param, base=Settings(), values=None):
    values = SWEEP_VALUES[param] if values is None else values
    return [{"value": v, **run_config(base, **{param: v})} for v in values]


def active_schedule_theorem_check(ns=C.ACTIVE_CHECK_NS, m=C.ACTIVE_CHECK_M, seeds=C.SWEEP_SEEDS):
    """Der zentrale Beweis-Check dieses Stücks: Giffler & Thompson (1960) zeigen, dass die Menge ALLER aktiven
    Zeitpläne mindestens einen optimalen enthält - hier für kleine Instanzen geprüft (volle Verzweigung über
    ALLE Konfliktauflösungen, nicht nur eine Regel), gegen CP-SAT als unabhängige Bestätigung. Zusätzlich, wie
    oft MWKR allein (die einfache Regel) das Optimum trifft - KEINE 100 %-Erwartung, anders als Stück 1-4/6."""
    rows = []
    for n in ns:
        theorem_matches, mwkr_matches = 0, 0
        for seed in seeds:
            inst = instance(n, m, seed)
            best_active = A.enumerate_active_schedules(inst.routing, inst.proc)
            opt, proven = A.solve_exact(inst.routing, inst.proc, time_limit_seconds=C.EXACT_TIME_LIMIT_SECONDS)
            if proven and best_active is not None and abs(best_active - opt.cmax) < 1e-6:
                theorem_matches += 1
            mwkr_cmax = A.giffler_thompson(inst.routing, inst.proc, A.mwkr_priority(inst.proc)).cmax
            if proven and abs(mwkr_cmax - opt.cmax) < 1e-6:
                mwkr_matches += 1
        rows.append({"value": n, "theorem_match_rate": theorem_matches / len(seeds), "mwkr_match_rate": mwkr_matches / len(seeds)})
    return rows


def timing_sweep(ns=(2, 3, 4, 5, 6, 7, 8), m=C.DEFAULT_M, seed=C.DEFAULT_SEED):
    """Gemessene Rechenzeit: CP-SAT (Zeitlimit, im schlimmsten Fall exponentiell) gegen Giffler-Thompson
    (polynomiell in n·m)."""
    rows = []
    for n in ns:
        inst = instance(n, m, seed)
        t0 = time.perf_counter()
        A.solve_exact(inst.routing, inst.proc, time_limit_seconds=C.EXACT_TIME_LIMIT_SECONDS)
        t_exact = time.perf_counter() - t0
        t0 = time.perf_counter()
        for _ in range(50):
            A.giffler_thompson(inst.routing, inst.proc, A.mwkr_priority(inst.proc))
        t_gt = (time.perf_counter() - t0) / 50
        rows.append({"value": n, "exact_seconds": t_exact, "gt_seconds": t_gt})
    return rows


def setup_gap(n=6, m=C.DEFAULT_M, seeds=C.SWEEP_SEEDS, n_families=C.DEFAULT_N_FAMILIES, setup_time=C.DEFAULT_SETUP_TIME):
    """Vehikel-B-Härtetest: Giffler-Thompson mit MWKR (kennt keine Rüstzeiten) gegen die echte Optimallösung MIT
    Rüstzeiten (CP-SAT, deshalb kleines n). Der Abstand ist eine echte Messfrage, kein behaupteter Befund."""
    gaps = []
    for seed in seeds:
        linst = SL.generate(n, m, seed, n_families=n_families, setup_time=setup_time)
        mwkr_cmax = A.giffler_thompson(linst.routing, linst.proc, A.mwkr_priority(linst.proc), linst.family, linst.setup).cmax
        opt, proven = A.solve_exact(linst.routing, linst.proc, linst.family, linst.setup, C.EXACT_TIME_LIMIT_SECONDS)
        if proven:
            gaps.append(_gap(mwkr_cmax, opt.cmax))
    return {"gap_mean": float(np.mean(gaps)), "gap_min": float(np.min(gaps)), "gap_max": float(np.max(gaps)), "n_runs": len(gaps)}


def setup_gap_sweep(setup_times=(0, 5, 15, 30, 60), n=6, m=C.DEFAULT_M, seeds=C.SWEEP_SEEDS, n_families=C.DEFAULT_N_FAMILIES):
    return [{"value": s, **setup_gap(n=n, m=m, seeds=seeds, n_families=n_families, setup_time=s)} for s in setup_times]
