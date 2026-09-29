# Job Shop – der Konvergenzpunkt dieser Linie – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-job-shop-demo.streamlit.app/)**

Achtes Stück der **Klassische-Scheduling-Theorie-Linie** der "Konzepte"-Reihe für die Website "Sebastian Hanisch
– Operations Research und Machine Learning": $n$ Aufträge, $m$ Maschinen, JEDER Auftrag besucht jede Maschine
genau einmal, aber in AUFTRAGSEIGENER Reihenfolge, Ziel ist die Gesamtdurchlaufzeit $C_{\max}$ zu minimieren -
stark NP-schwer bereits ab drei Maschinen.

**Einordnung in die Linie:** Der Konvergenzpunkt - Reihenfolge (Stück 1-5), serielle Maschinen (Johnson, Stück 6)
und parallele Maschinen (LPT, Stück 7) kommen hier zusammen. **Giffler-Thompson** (1960) konstruiert einen
AKTIVEN Zeitplan per Prioritätsregel; der eigentliche Beweis in diesem Stück ist über den SUCHRAUM, nicht über
eine Regel: die Menge aller aktiven Zeitpläne enthält garantiert mindestens einen optimalen - eine vierte Art
von Ergebnis in dieser Linie (nach "exakter Beweis", "nur Heuristik ohne Garantie" und "bewiesene Worst-Case-
Garantie").
```
SPT (1||ΣCⱼ, Vertauschungsargument)                                              [Stück 1]
EDD (1||Lmax, dasselbe Beweismuster, andere Zielfunktion)                        [Stück 2]
Moore-Hodgson (1||ΣUⱼ, EDD + gezieltes Streichen)                                [Stück 3]
WSPT / Smith's Rule (1||ΣwⱼCⱼ, verallgemeinert SPT mit Gewichten)                [Stück 4]
ATC (1||ΣwⱼTⱼ, stark NP-schwer - erstes Stück ohne Beweis)                       [Stück 5]
Johnson-Regel (F2||Cmax, erste Erweiterung auf zwei Maschinen)                   [Stück 6]
LPT (Pm||Cmax, parallele Maschinen, bewiesene Worst-Case-Garantie)               [Stück 7]
 └─ Job Shop (Konvergenzpunkt: Reihenfolge UND serielle UND parallele Maschinen) [dieses Stück]
       Shifting-Bottleneck, Job-Shop-Tabu-Search (SOTA-Folgestücke)
```

Ergebnis in Kürze: bei 10 Aufträgen auf 4 Maschinen liegt **MWKR** (Most Work Remaining) im Mittel **44 %** unter
SPT, **20 %** unter FIFO und **25 %** unter einer zufälligen Priorität. **Der überraschendste Befund dieses
Stücks**: SPT - die WURZEL dieser ganzen Linie, für $1||\sum C_j$ beweisbar optimal - schneidet hier, im Job
Shop mit $C_{\max}$-Ziel, systematisch SCHLECHTER ab als sogar die naive FIFO-Regel. SPT lässt lange Aufträge
konsequent bis zuletzt liegen, was bei der Gesamtdurchlaufzeit hart bestraft wird - ein ehrlicher Rückblick auf
die ganze Linie: eine Regel, die an der Wurzel beweisbar optimal war, ist hier eine der schlechtesten Wahlen.
**Der eigentliche, unverrückbare Beweis (Giffler & Thompson 1960)**: die Menge ALLER aktiven Zeitpläne enthält
IMMER das Optimum (100 % über n=2..6, CP-SAT-geprüft) - MWKR als einzelne Regel trifft es dagegen NICHT
zuverlässig (Trefferquote fällt bis auf 0 % bei n=4). Auf dem Werkstatt/Logistik-Vehikel bleibt der Abstand zum
Optimum zwischen 13 % und 20 % über den gesamten Rüstzeit-Bereich - nicht sauber monoton (wie schon bei
`edd-scheduling-demo` beobachtet, jedes Stück misst neu, statt eine Kurvenform anzunehmen).

| Frage | Ergebnis (Mittel über 5 feste Instanzen, Seeds 100000–100004, mit je 3 Ketten-Seeds) |
|---|---|
| Standardfall (10 Aufträge, 4 Maschinen) | ✅ MWKR liegt **44 %** unter SPT, **20 %** unter FIFO, **25 %** unter Zufall |
| **SPT (Wurzel dieser Linie) im Job Shop** | ❌ Systematisch SCHLECHTER als FIFO - eine echte, ernüchternde Umkehr |
| **Beweis über den Suchraum (n=2..6)** | ✅ **100 %** - aktive Zeitpläne enthalten IMMER das Optimum |
| **MWKR allein trifft das Optimum** | ❌ Fällt bis auf **0 %** bei n=4 - eine Regel ist etwas anderes als der volle Suchraum |
| **Vehikel Werkstatt/Logistik** | ❌ 13–20 % über dem Optimum, nicht sauber monoton über die Rüstzeit |

## Was die Demo zeigt

1. **Job Shop in Aktion** (Schritt-Slider): **Aufträge** (gestapelter Balken je Auftrag in eigener Maschinen-
   reihenfolge) → **Einplanen** (Regler "eingeplante Operationen", Gantt mit einer Zeile JE MASCHINE, Farbe nach
   AUFTRAG) → **Ergebnis** (Fertigstellung je Maschine, MWKR gegen FIFO).
2. **Was die Prioritätsregel bringt:** MWKR, SPT (die Wurzel dieser Linie - hier falsch!), FIFO (naiv),
   zufällige Priorität, CP-SAT-Gegenprobe (n ≤ 8, mit Beweis-Status).
3. **📐 Sweep** über die Anzahl der Aufträge ODER Maschinen.
4. **🔬 Experimente auf Abruf:** enthalten aktive Zeitpläne wirklich das Optimum (der Beweis-Check dieses
   Stücks - volle Verzweigung über alle Konfliktauflösungen, nicht nur eine Regel); Rechenzeit CP-SAT gegen
   Giffler-Thompson; Rüstzeit-Härtetest.
5. **🚧 Grenzen:** Tabelle mit Verweis auf die SOTA-Folgestücke (Shifting-Bottleneck, Job-Shop-Tabu-Search).

Regler: Aufträge (2–30), **Maschinen** (2–6), **Vehikel** (Neutral/Werkstatt-Logistik – bei Werkstatt zusätzlich
Rüstzeit und Anzahl Familien), Seed der Instanz (+ 🎲), Seed der Kette (+ 🎲).

## Die zwei Vehikel (gelten für die ganze Linie)

- **Neutral** (`jsp_scenario.py`): $n$ Aufträge, jeder mit einer ZUFÄLLIGEN Permutation der $m$ Maschinen als
  eigener Reihenfolge, Bearbeitungszeiten $\sim U(1, 100)$ je Operation - der klassische, in der Literatur
  übliche Job-Shop-Instanztyp (z. B. Taillard-Benchmarks).
- **Werkstatt/Logistik** (`jsp_scenario_logistik.py`): dieselbe Instanz, aber jeder Auftrag gehört zu einer
  Familie; ein Familienwechsel kostet eine feste Rüstzeit JE MASCHINE (dieselbe Idee wie in
  `spt-scheduling-demo` usw.). Rüstzeit 0 kollabiert strukturell exakt zum neutralen Vehikel (per Test belegt).

## Modell und Verfahren

- **Instanz** (`jsp_scenario.py`, `jsp_scenario_logistik.py`): Routing (Maschinenreihenfolge je Auftrag),
  Bearbeitungszeiten, Familien und Rüstzeit-Matrix.
- **Giffler-Thompson** (`jsp_algorithm.py`): konstruiert EINEN aktiven Zeitplan per Prioritätsregel (MWKR, SPT,
  FIFO, Zufall). Dazu die volle Verzweigung über ALLE Konfliktauflösungen (`enumerate_active_schedules`, nur für
  kleine Instanzen, siehe README-Grenzen) als unabhängiger Beweis-Check.
- **CP-SAT** (`jsp_algorithm.solve_exact`): ein Kreis-Modell JE MASCHINE (die Operationen je Maschine sind durch
  das Routing fest vorgegeben, anders als bei `lpt-scheduling-demo` keine Zuordnungsentscheidung mehr) plus
  Vorrang-Bedingungen zwischen den Operationen jedes Auftrags. Gegen unabhängige Brute-Force-Vollaufzählung
  verifiziert.
- **Auswertung** (`jsp_evaluation.py`): Kennzahlen, Sweep, Beweis-Check über den Suchraum, Timing-Messreihe,
  Rüstzeit-Härtetest.

## Was nicht funktioniert hat / Grenzen

- **Vorab-Annahme: "SPT, die Wurzel dieser Linie, bleibt zumindest eine brauchbare Regel"** - **klar widerlegt**:
  SPT schneidet im Standardfall 44 % schlechter ab als MWKR und sogar systematisch schlechter als die naive
  FIFO-Regel. Grund: SPT optimiert für $\sum C_j$ (viele kurze Aufträge schnell durchschleusen), aber $C_{\max}$
  bestraft genau das Gegenteil - ein langer Auftrag, der bis zuletzt liegen bleibt, verlängert die gesamte
  Durchlaufzeit. Ein Modellwechsel kann eine einst beweisbar optimale Regel zu einer der schlechtesten machen.
- **Vorab-Vermutung: "MWKR ist auf dem neutralen Vehikel immer mindestens so gut wie SPT/FIFO/Zufall" (wie bei
  Stück 1-4/6)** - **widerlegt** (wie schon bei `lpt-scheduling-demo`): MWKR kann sogar OHNE Rüstzeiten
  schlechter abschneiden als FIFO (n=6, m=3, Seed 2: -20,4 %). Der Giffler-Thompson-Beweis gilt für den
  SUCHRAUM aktiver Zeitpläne, nicht für MWKR als Regel gegenüber einer bestimmten anderen Regel.
- **Die volle Verzweigung über aktive Zeitpläne explodiert unvorhersehbar** - n=6/m=4 dauert unter 3 Sekunden,
  n=7/m=4 kann über 100 Sekunden brauchen. Der Beweis-Check ist deshalb FEST auf n≤6 bei 3 Maschinen begrenzt,
  unabhängig vom Maschinen-Regler der App (mit einem Sicherheitsnetz `max_leaves` im Code).
- **CP-SAT ist überraschend schnell**: bis n=9, m=6 (54 Operationen) unter 4 Sekunden selbst mit Rüstzeiten -
  deutlich komfortabler als das ATC-Modell aus Stück 5, weil hier keine Zuordnungsentscheidung mehr nötig ist.
- **Der Rüstzeit-0-Fall ist KEIN Nulltest mehr** (wie bei ATC/LPT): die korrekte Konsistenzprüfung ist
  strukturell (identischer Zeitplan bei Rüstzeit 0), nicht "trifft MWKR das Optimum".
- **Synthetische Instanzen:** Bearbeitungszeiten gleichverteilt, jeder Auftrag besucht jede Maschine genau
  einmal (kein Flexible Job Shop, keine wiederholten Maschinenbesuche).

## Verifikation

- **CP-SAT gegen unabhängige Brute-Force-Vollaufzählung** (mit und ohne Rüstzeiten): für n ≤ 4, m ≤ 3 über
  mehrere Seeds stimmt das Kreis-Modell exakt mit einer unabhängigen Vollaufzählung (alle zulässigen
  Permutations-Kombinationen je Maschine) überein.
- **Beweis-Check gegen CP-SAT**: für n = 2 bis 6 (feste 3 Maschinen) trifft das BESTE unter allen aktiven
  Zeitplänen (volle Verzweigung) exakt das CP-SAT-Optimum - Giffler & Thompsons Satz empirisch bestätigt.
- **Struktureller Konsistenz-Test**: MWKRs Zeitplan bei Rüstzeit 0 ist identisch mit dem neutralen Vehikel.
- **Handrechnung:** eine kleine Instanz (2 Aufträge, 2 Maschinen, ein Auftrag mit viel Arbeit, einer mit wenig)
  bestätigt, dass MWKR den arbeitsintensiven Auftrag zuerst einplant und SPT schlägt.
- **Alle Zahlen der App-Texte sind als Tests hinterlegt** (Standardfall, Beweis-Check, Rüstzeit-Härtetest;
  positive **und** negative Aussagen inklusive des Falls, in dem MWKR schlechter als FIFO abschneidet - auch
  ohne Rüstzeiten); alle 5 Presets geprüft; AppTest-Rauchtests (Voreinstellung, jedes Preset, jeder Schritt auf
  beiden Vehikeln, Würfel-Knöpfe, Permalink-Grenzen inkl. ungültigem Vehikel, Extremwerte, Experimente auf
  Abruf, Footer, korrekt formatierte negative Prozent-Abstände); eigener Test für die ausblendbaren Regler
  (kein verwaister Widget-Zustand nach Permalink/Preset - von Anfang an eingebaut).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `app.py` | Streamlit-App: Schritte, Ergebnis, 📐 Sweep, 🔬 Experimente, 🚧 Grenzen, Mathe |
| `jsp_algorithm.py` | Giffler-Thompson, Prioritätsregeln, volle Verzweigung über aktive Zeitpläne, CP-SAT |
| `jsp_scenario.py` | Vehikel Neutral |
| `jsp_scenario_logistik.py` | Vehikel Werkstatt/Logistik (Familien, Rüstzeit-Matrix) |
| `jsp_constants.py` | Konstanten, Presets |
| `jsp_evaluation.py` | Kennzahlen, Sweep, Beweis-Check über den Suchraum, Timing-Messreihe, Rüstzeit-Härtetest |
| `jsp_presets.py`, `jsp_visualization.py` | Permalink/Presets (inkl. `seed_widget`/`KEPT` für ausblendbare Regler), Plotly-Figuren (ein Trace je Maschine, achsengesperrt) |
| `tests/` | CP-SAT gegen Vollaufzählung, Beweis-Check gegen CP-SAT, Szenario und Auswertung, Aussagen der App, Presets, versteckter Widget-Zustand, AppTest |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

Teil des [Operations-Research-Demo-Portfolios](https://sebastianhanisch.net/demos.html) von
[Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning.
Interesse an einer maßgeschneiderten Lösung? [Kontakt aufnehmen](https://sebastianhanisch.net/kontakt.html).
