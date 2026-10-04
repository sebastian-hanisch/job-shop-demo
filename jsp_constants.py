"""Konstanten der Job-Shop-Demo: beide Vehikel (Neutral, Werkstatt/Logistik), Regler, Messreihen-Seeds."""

N_MIN, N_MAX, DEFAULT_N, N_STEP = 2, 30, 10, 1
M_MIN, M_MAX, DEFAULT_M = 2, 6, 4
SEED_MAX = 999999
DEFAULT_SEED = 60
SWEEP_SEEDS = tuple(range(100000, 100005))
SWEEP_CHAINS = 3

# Bearbeitungszeiten
P_MIN, P_MAX = 1, 100

# CP-SAT exakte Gegenprobe: praktisches Limit für eine live nutzbare Demo (gemessen, siehe README) - das
# Kreis-Modell je Maschine ist hier einfacher als bei Stück 7 (keine Zuordnungsentscheidung, nur Reihenfolge je
# Maschine), deshalb deutlich schneller: n bis 9 UND m bis 6 bleiben komfortabel unter dem Zeitlimit.
EXACT_MAX_N = 8
EXACT_TIME_LIMIT_SECONDS = 15.0

# Beweis-Check (volle Verzweigung über ALLE aktiven Zeitpläne, siehe jsp_algorithm.enumerate_active_schedules):
# EIGENER, kleinerer Größenbereich - die Zahl aktiver Zeitpläne explodiert unvorhersehbar (n=7,m=4 kann über
# 100 Sekunden brauchen), deshalb fest auf m=3 begrenzt, unabhängig vom Maschinen-Regler der App.
ACTIVE_CHECK_NS = (2, 3, 4, 5, 6)
ACTIVE_CHECK_M = 3

# --- Vehikel B "Werkstatt/Logistik" ---------------------------------------------------------------------------
N_FAMILIES_MIN, N_FAMILIES_MAX, DEFAULT_N_FAMILIES = 2, 6, 3
SETUP_TIME_MIN, SETUP_TIME_MAX, DEFAULT_SETUP_TIME = 0, 60, 15

VEHICLE_LABELS = {"neutral": "Neutral", "logistik": "Werkstatt/Logistik"}
DEFAULT_VEHICLE = "neutral"


def _preset(n=DEFAULT_N, m=DEFAULT_M, vehicle=DEFAULT_VEHICLE, setup_time=DEFAULT_SETUP_TIME, n_families=DEFAULT_N_FAMILIES):
    return {"n": n, "m": m, "seed": DEFAULT_SEED, "chain_seed": 0, "vehicle": vehicle, "setup_time": setup_time, "n_families": n_families}


PRESETS = {
    "Standardfall (Voreinstellung)": _preset(),
    "Kleine Instanz (CP-SAT sichtbar)": _preset(n=EXACT_MAX_N),
    "Große Instanz (Skalierung)": _preset(n=N_MAX),
    "Werkstatt/Logistik-Vehikel": _preset(vehicle="logistik"),
    "Hohe Rüstlast (Werkstatt)": _preset(vehicle="logistik", setup_time=SETUP_TIME_MAX),
}
# Werte in PRESET_HELP nach der Messreihe (jsp_evaluation.run_config) final eingetragen.
PRESET_HELP = {
    "Standardfall (Voreinstellung)": f"{DEFAULT_N} Aufträge auf {DEFAULT_M} Maschinen, jeder mit eigener Reihenfolge: Giffler-Thompson mit MWKR misst sich gegen SPT, gegen dieselbe Konstruktion mit FIFO und gegen Zufall.",
    "Kleine Instanz (CP-SAT sichtbar)": f"{EXACT_MAX_N} Aufträge: hier löst CP-SAT (OR-Tools) das Problem exakt mit.",
    "Große Instanz (Skalierung)": f"{N_MAX} Aufträge: Giffler-Thompson bleibt schnell, eine exakte Lösung wäre bei dieser Größe aussichtslos.",
    "Werkstatt/Logistik-Vehikel": "Dieselben Aufträge, aber in Familien mit Rüstzeit beim Wechsel je Maschine - die Prioritätsregeln kennen diese Rüstzeiten nicht.",
    "Hohe Rüstlast (Werkstatt)": f"Rüstzeit {SETUP_TIME_MAX} Minuten je Familienwechsel: der Abstand zum echten Optimum wächst.",
}
