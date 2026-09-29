"""Job Shop - der Konvergenzpunkt dieser Linie - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Achtes Stück der neuen Konzepte-Linie "Klassische Scheduling-Theorie": n Aufträge, m Maschinen, JEDER Auftrag
besucht jede Maschine genau einmal, aber in AUFTRAGSEIGENER Reihenfolge - Reihenfolge (Stück 1-5), serielle
Maschinen (Stück 6) und parallele Maschinen (Stück 7) kommen hier zusammen. Stark NP-schwer. Giffler-Thompson
(1960) konstruiert AKTIVE Zeitpläne per Prioritätsregel; MWKR (Most Work Remaining) ist die beste einfache Regel
für Cmax hier - SPT (die Wurzel dieser Linie!) schneidet überraschend SCHLECHTER ab als sogar FIFO. Siehe README
für die Einordnung in die Linie.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import jsp_algorithm as A
import jsp_constants as C
from jsp_evaluation import Settings, SWEEP_LABELS, active_schedule_theorem_check, analyse, instance, run_config, setup_gap, setup_gap_sweep, sweep, timing_sweep
from jsp_presets import KEPT, apply_preset, bounds, init_session_state_defaults, load_permalink_settings, randomize_chain_seed, randomize_seed, seed_widget, sync_query_params
from jsp_visualization import build_jobs_chart, build_machine_finish_comparison, build_machine_gantt, build_setup_gap, build_sweep, build_theorem_chart, build_timing

st.set_page_config(page_title="Job Shop – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(param, base):
    return sweep(param, base)


@st.cache_data(show_spinner=False)
def _theorem_check():
    return active_schedule_theorem_check()


@st.cache_data(show_spinner=False)
def _timing(m):
    return timing_sweep(m=m)


@st.cache_data(show_spinner=False)
def _setup_gap_sweep(n, m, n_families):
    return setup_gap_sweep(n=n, m=m, n_families=n_families)


def _fmt_int(x):
    return f"{int(round(x)):,}".replace(",", ".")


def _fmt_pct(x):
    """Vorzeichen-korrekt: `+9.2 %` (Vergleichsregel schlechter als MWKR) oder `-x %` (MWKR ist keine bewiesen
    optimale Regel - eine Vergleichsregel kann hier auch mal besser abschneiden, AUCH ohne Rüstzeiten)."""
    return f"{x:+.1f} %"


st.title("🏭 Job Shop – der Konvergenzpunkt dieser Linie")
st.markdown(
    r"""
**n Aufträge, m Maschinen, JEDER Auftrag besucht jede Maschine genau einmal, aber in AUFTRAGSEIGENER
Reihenfolge** - hier laufen Reihenfolge (Stück 1-5), serielle Maschinen (Stück 6) und parallele Maschinen
(Stück 7) zusammen, stark NP-schwer. **Giffler-Thompson** (1960) konstruiert einen AKTIVEN Zeitplan (keine
Operation lässt sich vorziehen, ohne eine andere zu verzögern) mittels einer Prioritätsregel bei jedem Konflikt.
Mit **MWKR** (Most Work Remaining - der Auftrag mit der meisten verbleibenden Arbeit zuerst) ist das eine gute
Heuristik für die Gesamtdurchlaufzeit. **Der Beweis, der hier zählt, ist über den Suchraum**: Giffler & Thompson
zeigen, dass die Menge ALLER aktiven Zeitpläne mindestens einen optimalen enthält - eine vierte Art von Ergebnis
in dieser Linie.
"""
)
st.caption(
    "Achtes Stück der Konzepte-Linie „Klassische Scheduling-Theorie“ - der Konvergenzpunkt. Zwei Vehikel: "
    "**Neutral** (Aufträge mit eigener Maschinenreihenfolge) und **Werkstatt/Logistik** (dieselben Aufträge, "
    "aber in Familien mit Rüstzeit beim Wechsel je Maschine) - der Umschalter ist in der Seitenleiste."
)

with st.expander("So funktioniert Giffler-Thompson", expanded=True):
    st.markdown(
        r"""
1. **Nächste Operationen bestimmen.** Für jeden Auftrag die nächste noch offene Operation - das sind die Kandidaten.
2. **Frühesten Konflikt finden.** Unter allen Kandidaten die kleinste mögliche Fertigstellungszeit $C^*$ auf ihrer Maschine $M^*$ - alle Kandidaten für $M^*$, die vor $C^*$ starten könnten, bilden den "Konfliktsatz".
3. **Per Priorität entscheiden.** Aus dem Konfliktsatz den Auftrag mit der höchsten Priorität wählen - MWKR: die meiste verbleibende Arbeit zuerst.
4. **Warum das einen SICHEREN Suchraum ergibt.** Jede so konstruierte Lösung ist ein "aktiver" Zeitplan; Giffler & Thompson (1960) beweisen: unter ALLEN aktiven Zeitplänen ist mindestens einer optimal - kein Optimum geht verloren, egal welche Prioritätsregel man verwendet.
5. **Die Grenze der Annahme.** Keine Prioritätsregel kennt Rüstzeiten. Das Vehikel „Werkstatt/Logistik“ prüft, was passiert, wenn ein Familienwechsel auf einer Maschine zusätzlich Zeit kostet.
        """
    )

st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
preset_names = list(C.PRESETS.keys())
cols = st.columns(len(preset_names))
for col, name in zip(cols, preset_names):
    with col:
        st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP[name], key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    st.header("⚙️ Einstellungen")
    n_jobs = st.slider("Aufträge", *bounds("n_slider"), key="n_slider", step=C.N_STEP,
                        help=f"Anzahl der Aufträge. Bis {C.EXACT_MAX_N} löst CP-SAT das Problem exakt mit.")
    m_machines = st.slider("Maschinen", *bounds("m_slider"), key="m_slider",
                            help="Jeder Auftrag besucht jede Maschine genau einmal, aber in eigener Reihenfolge.")
    vehicle = st.radio("Vehikel", list(C.VEHICLE_LABELS), key="vehicle_radio", format_func=lambda k: C.VEHICLE_LABELS[k],
                        help="Neutral: nur Bearbeitungszeiten. Werkstatt/Logistik: dieselben Aufträge, zusätzlich in Familien mit Rüstzeit beim Wechsel je Maschine.")
    if vehicle == "logistik":
        seed_widget("setup_time_slider")
        setup_time = st.slider("Rüstzeit je Familienwechsel (Minuten)", *bounds("setup_time_slider"), key="setup_time_slider",
                                help="0 Minuten kollabiert strukturell exakt zum neutralen Vehikel (siehe Test/Messreihe).")
        st.session_state[KEPT["setup_time_slider"]] = setup_time
        seed_widget("n_families_slider")
        n_families = st.slider("Auftragsfamilien", *bounds("n_families_slider"), key="n_families_slider",
                                help="Weniger Familien bei gleicher Auftragszahl bedeutet mehr Wechsel und damit mehr Rüstzeit insgesamt.")
        st.session_state[KEPT["n_families_slider"]] = n_families
    else:
        setup_time = int(st.session_state.get(KEPT["setup_time_slider"], C.DEFAULT_SETUP_TIME))
        n_families = int(st.session_state.get(KEPT["n_families_slider"], C.DEFAULT_N_FAMILIES))
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed, help="Würfelt einen neuen Seed für Routing und Bearbeitungszeiten.")
    chain_seed = st.number_input("Zufalls-Seed der Kette", *bounds("chain_seed_input"), key="chain_seed_input", step=1,
                                  help="Steuert nur die zufällige Vergleichs-Priorität - MWKR/SPT/FIFO selbst sind deterministisch.")
    st.button("🎲 Neue Kette würfeln", width="stretch", on_click=randomize_chain_seed, help="Würfelt einen neuen Seed für die Zufalls-Vergleichspriorität.")

sync_query_params({"n_slider": int(n_jobs), "m_slider": int(m_machines), "seed_input": int(seed), "chain_seed_input": int(chain_seed),
                    "vehicle_radio": vehicle, "setup_time_slider": int(setup_time), "n_families_slider": int(n_families)})

settings = Settings(int(n_jobs), int(m_machines), int(seed), int(chain_seed), vehicle=vehicle, setup_time=int(setup_time), n_families=int(n_families))
with st.spinner("Rechne..."):
    a = _analysis(settings)
inst = a.inst
routing, proc = inst.routing, inst.proc
data_key = settings

# --- Job Shop in Aktion ---------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Job Shop in Aktion")
STEP_LABELS = {1: "1 · Aufträge", 2: "2 · Einplanen", 3: "3 · Ergebnis"}
if "jsp_step" not in st.session_state or st.session_state.get("jsp_step_owner") != data_key:
    st.session_state["jsp_step"] = 1
    st.session_state["jsp_step_owner"] = data_key
step = st.select_slider("Schritt", options=list(STEP_LABELS), key="jsp_step", format_func=lambda s: STEP_LABELS[s])

total_ops = int(n_jobs) * int(m_machines)
if step == 2:
    it_col, itplay_col = st.columns([5, 2])
    with it_col:
        upto = st.slider("Eingeplante Operationen", 1, total_ops, value=total_ops, key="jsp_upto")
else:
    upto = total_ops

view_slot = st.empty()
with view_slot.container():
    if step == 1:
        st.markdown(f"**{n_jobs} Aufträge, unsortiert** (gestapelt in eigener Maschinenreihenfolge, Farbe nach Maschine)")
        st.plotly_chart(build_jobs_chart(routing, proc), width="stretch", key="s1_jobs")
    elif step == 2:
        st.markdown(f"**MWKR-Zeitplan nach {upto} von {total_ops} eingeplanten Operationen** (Farbe nach Auftrag)")
        st.plotly_chart(build_machine_gantt(routing, proc, a.mwkr.start, a.mwkr.end, int(m_machines), upto_ops=upto), width="stretch", key=f"s2_sched_{upto}")
    else:
        st.markdown("**Fertigstellung je Maschine: MWKR gegen FIFO**")
        st.plotly_chart(build_machine_finish_comparison(a.mwkr.machine_finish, a.fifo.machine_finish), width="stretch", key="s3_finish")

if step == 1:
    st.caption(f"Bearbeitungszeiten zwischen {int(proc.min())} und {int(proc.max())} Minuten (Seed {seed}). Jeder Auftrag besucht jede Maschine genau einmal, aber in eigener Reihenfolge.")
elif step == 2:
    gap_note = " Lücken sind Wartezeit auf eine andere Maschine oder (Werkstatt-Vehikel) Rüstzeit bei einem Familienwechsel." if vehicle == "logistik" else " Lücken sind Wartezeit, bis die vorherige Operation desselben Auftrags fertig ist."
    st.caption(f"Jede Zeile ist eine Maschine, jeder Balken eine Operation, Farbe = Auftrag.{gap_note}")
else:
    st.caption(f"MWKR: Cmax {_fmt_int(a.mwkr.cmax)}. FIFO: {_fmt_int(a.fifo.cmax)} (Differenz {_fmt_pct(a.gap_fifo)}). Die gestrichelten Linien markieren jeweils die höchste Last (= Cmax).")

st.markdown("---")

# --- Ergebnis -------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Was die Prioritätsregel bringt")
vehicle_note = " Auf dem Werkstatt/Logistik-Vehikel zählt die Rüstzeit je Maschine mit - keine Regel kennt sie, alle Zahlen hier berücksichtigen sie trotzdem." if vehicle == "logistik" else ""
st.caption(f"**Abstand:** Cmax einer Regel gegenüber MWKR in Prozent - kann negativ werden, MWKR ist keine bewiesen optimale Regel, nur eine bewiesen GUTE innerhalb eines Suchraums, der bewiesen das Optimum enthält.{vehicle_note}")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("MWKR (Cmax)", _fmt_int(a.mwkr.cmax), help="Die Zielgröße: Gesamtdurchlaufzeit mit der Most-Work-Remaining-Regel, auf dem gewählten Vehikel.")
m2.metric("SPT (Wurzel dieser Linie!)", _fmt_pct(a.gap_spt), delta_color="off", help="SPT war für Stück 1 dieser Linie beweisbar optimal - hier, im Job Shop mit Cmax-Ziel, schneidet es überraschend schlecht ab.")
m3.metric("FIFO (naiv)", _fmt_pct(a.gap_fifo), delta_color="off", help="Keine Prioritätsinformation - Aufträge in Ankunftsreihenfolge.")
m4.metric(f"Zufällige Priorität (Mittel über {a.random_runs})", _fmt_pct(a.gap_random), delta_color="off", help="Mittel über mehrere zufällige Prioritätsreihenfolgen derselben Instanz.")
if a.optimal is not None and a.optimal_proven:
    m5.metric("CP-SAT (exakte Gegenprobe)", "trifft MWKR exakt" if a.mwkr_matches_optimum else f"{a.mwkr_ratio_to_optimum:.3f}× Optimum", delta_color="off",
              help="OR-Tools CP-SAT hat diese Instanz bewiesen exakt gelöst.")
elif a.optimal is not None:
    m5.metric("CP-SAT", "Zeitlimit erreicht", delta_color="off", help="CP-SAT hat innerhalb des Zeitlimits keine bewiesen optimale Lösung gefunden.")
else:
    m5.metric("CP-SAT", f"erst ab n ≤ {C.EXACT_MAX_N}", delta_color="off", help="Bei dieser Größe wäre eine exakte Lösung aussichtslos.")

if a.gap_spt < 0 or a.gap_fifo < 0 or a.gap_random < 0:
    candidates = [("SPT", a.gap_spt), ("FIFO", a.gap_fifo), ("eine zufällige Priorität", a.gap_random)]
    worse_than, worst_gap = min(candidates, key=lambda c: c[1])
    vehicle_hint = " (hier zusätzlich durch Rüstzeiten, die keine Regel kennt)" if vehicle == "logistik" else ""
    st.warning(f"⚠️ MWKR schneidet hier sogar schlechter ab als {worse_than}: {abs(worst_gap):.1f} % mehr{vehicle_hint}. Kein Fehler - der Beweis gilt für den SUCHRAUM aktiver Zeitpläne (siehe CP-SAT-Feld und 🔬 unten), nicht für MWKR als Regel gegenüber einer bestimmten anderen Regel auf genau dieser Instanz. Das kann auch OHNE Rüstzeiten vorkommen.")
else:
    tail = " (auch mit Rüstzeiten - bei dieser Instanz trifft MWKR trotzdem das Optimum, das ist nicht garantiert)" if vehicle == "logistik" and a.optimal is not None and a.mwkr_matches_optimum else ""
    st.success(f"✅ MWKR ist {a.gap_spt:.1f} % besser als SPT, {a.gap_fifo:.1f} % besser als FIFO und {a.gap_random:.1f} % besser als eine zufällige Priorität{tail}.")

st.markdown("---")

# --- Sweeps -----------------------------------------------------------------------------------------------------------------------------

st.subheader("📐 Wie stark hängt der Vorsprung von der Instanz ab?")
sweep_param = st.selectbox("Welcher Regler soll durchgefahren werden?", list(SWEEP_LABELS), format_func=lambda k: SWEEP_LABELS[k], key="sweep_select")
if st.button("Sweep über 5 feste Instanzen berechnen (dauert wenige Sekunden)", key="sweep_start"):
    st.session_state["sweep_done"] = st.session_state.get("sweep_done", set()) | {sweep_param}
if sweep_param in st.session_state.get("sweep_done", set()):
    rows_sweep = _sweep(sweep_param, Settings())
    st.plotly_chart(build_sweep(rows_sweep, SWEEP_LABELS[sweep_param]), width="stretch", key="sweep_chart")
    st.caption("Mittel über 5 feste Instanzen (Seeds 100000–100004) mit je drei Zufalls-Ketten für die Vergleichspriorität.")

st.markdown("---")

# --- Experimente ------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Enthalten aktive Zeitpläne wirklich das Optimum?")
if st.button(f"Alle aktiven Zeitpläne für n = 2 bis 6 durchprobieren (feste {C.ACTIVE_CHECK_M} Maschinen, dauert etwa 10 Sekunden)", key="theorem_start"):
    st.session_state["theorem_on"] = True
if st.session_state.get("theorem_on"):
    rows_th = _theorem_check()
    st.plotly_chart(build_theorem_chart(rows_th), width="stretch", key="theorem_chart")
    st.caption("Grün: das BESTE unter ALLEN aktiven Zeitplänen (volle Verzweigung über jede Konfliktauflösung) trifft IMMER das CP-SAT-Optimum - Giffler & Thompsons Beweis über den Suchraum, nicht über eine Regel. Blau gestrichelt: MWKR allein trifft das Optimum NICHT immer - der Unterschied ist der Punkt dieses Experiments.")

st.markdown("---")

st.subheader("🔬 Wie teuer ist eine exakte Lösung wirklich?")
if st.button("Rechenzeit für n = 2 bis 8 messen (dauert etwa 1 Sekunde)", key="timing_start"):
    st.session_state["timing_on"] = True
if st.session_state.get("timing_on"):
    rows_t = _timing(int(m_machines))
    st.plotly_chart(build_timing(rows_t), width="stretch", key="timing_chart")
    last = rows_t[-1]
    st.caption(f"Bei {last['value']} Aufträgen braucht CP-SAT bereits {last['exact_seconds']*1000:.0f} ms, Giffler-Thompson {last['gt_seconds']*1000:.3f} ms.")

st.markdown("---")

st.subheader("🔬 Werkstatt/Logistik: bleibt MWKR gut, wenn Rüstzeiten dazukommen?")
if st.button("Rüstzeit von 0 bis 60 Minuten durchfahren (dauert wenige Sekunden)", key="setup_start"):
    st.session_state["setup_on"] = True
if st.session_state.get("setup_on"):
    rows_s = _setup_gap_sweep(min(int(n_jobs), C.EXACT_MAX_N), int(m_machines), int(n_families))
    st.plotly_chart(build_setup_gap(rows_s), width="stretch", key="setup_chart")
    st.caption("MWKR ignoriert weiterhin die Rüstzeit beim Familienwechsel; verglichen mit der echten Optimallösung MIT Rüstzeiten (CP-SAT, deshalb kleine Instanz). Anders als bei Stück 1-4/6: der Abstand bei Rüstzeit 0 ist NICHT automatisch null.")

st.markdown("---")

# --- Grenzen ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Rüstzeiten sind nicht sequenzabhängig** | Sobald ein Familienwechsel auf einer Maschine zusätzlich Zeit kostet (Vehikel „Werkstatt/Logistik“), wächst der Abstand zum echten Optimum mit der Rüstzeit (siehe Experiment oben). | Kein direkter Nachfolger in dieser Linie |
| **Jeder Auftrag besucht jede Maschine genau einmal** | Manche Aufträge brauchen manche Maschinen mehrfach oder gar nicht, manche Operationen können auf MEHREREN Maschinen laufen (Flexible Job Shop) - eine noch größere Zuordnungsfrage. | Kreuzverweis: Exakte-Suche-Linie (RCPSP) |
| **Eine einzelne gute Regel reicht** | Für harte Instanzen brauchen professionelle Löser lokale Suche über ganze Zeitpläne - nicht nur eine Konstruktionsregel. | **Shifting-Bottleneck, Job-Shop-Tabu-Search** (SOTA-Folgestücke) |
"""
)
st.caption(
    "Achtes Stück der Linie „Klassische Scheduling-Theorie“: der Konvergenzpunkt. Verwandt: die Trajektorien-"
    "Metaheuristiken-Linie (Tabu Search, lokale Suche über ganze Zeitpläne)."
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem** (Job Shop, $C_{\max}$): $n$ Aufträge, $m$ Maschinen. Auftrag $j$ hat eine EIGENE Permutation der
Maschinen als Reihenfolge seiner $m$ Operationen; jede Operation braucht eine feste Bearbeitungszeit. Gesucht:
ein Zeitplan (Reihenfolge je Maschine), der $C_{\max}$ minimiert - stark NP-schwer bereits ab 3 Maschinen.

**Giffler-Thompson (1960).** Konstruktion eines AKTIVEN Zeitplans: solange nicht alle Operationen eingeplant
sind, unter den als Nächstes fälligen Operationen jedes Auftrags die mit der kleinstmöglichen Fertigstellung
$C^*$ auf ihrer Maschine $M^*$ finden; alle Operationen, die $M^*$ ebenfalls brauchen und vor $C^*$ beginnen
könnten, bilden den Konfliktsatz; eine Prioritätsregel wählt daraus.

**Satz (Giffler & Thompson 1960).** Die Menge aller so konstruierbaren aktiven Zeitpläne enthält mindestens
einen optimalen Zeitplan - ein Beweis über den SUCHRAUM, nicht über eine bestimmte Regel.

**MWKR** (Most Work Remaining): Priorität nach der Summe der noch ausstehenden Bearbeitungszeiten des Auftrags
(die aktuelle Operation und alle folgenden) - empirisch eine der besten einfachen Regeln für $C_{\max}$ im Job
Shop (Pinedo, "Scheduling"). **SPT** (Stück 1 dieser Linie) ist dafür NICHT geeignet: es lässt lange Aufträge
systematisch bis zuletzt liegen, was bei $C_{\max}$ bestraft wird.

**CP-SAT-Modell** (`solve_exact`): ein Kreis-Modell JE MASCHINE (die Operationen je Maschine sind durch das
Routing fest vorgegeben) plus Vorrang-Bedingungen zwischen den Operationen jedes Auftrags; bei Rüstzeit 0
kollabiert es exakt zum rüstzeitfreien Fall.

Implementiert in `jsp_algorithm.py` (Giffler-Thompson, Prioritätsregeln, volle Verzweigung über aktive
Zeitpläne, CP-SAT), `jsp_scenario.py`/`jsp_scenario_logistik.py` (die zwei Vehikel), `jsp_evaluation.py`
(Kennzahlen, Sweep, Beweis-Check über den Suchraum, Timing-Messreihe, Rüstzeit-Härtetest).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning. Interesse an einer maßgeschneiderten Lösung für "
    "Ihr Unternehmen? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html)"
)
