"""Plotly-Abbildungen der Job-Shop-Demo: Auftragsübersicht (gestapelt nach Maschinenreihenfolge), Mehrzeilen-
Gantt (eine Zeile je Maschine, Farbe nach AUFTRAG), Maschinen-Endzeit-Vergleich, Sweep, Timing. Achsen sind
gesperrt (fixedrange). Das Gantt baut EIN Trace JE MASCHINE (siehe [[feedback_plotly_many_traces_per_category_shrinks_bars]] -
gefunden in `johnson-rule-demo`, hier von Anfang an richtig gebaut), Farbe wird PRO AUFTRAG über customdata
gesetzt (ein Trace kann nicht mehrere Farben zugleich einfärben, deshalb ein eigener Marker-Farbvektor)."""

import numpy as np
import plotly.graph_objects as go

MACHINE_COLORS = ["#4c78a8", "#54a24b", "#e45756", "#f58518", "#b279a2", "#9c755f"]
JOB_COLORS = ["#4c78a8", "#54a24b", "#e45756", "#f58518", "#b279a2", "#9c755f", "#ff9da6", "#9d755d", "#bab0ac", "#eeca3b"]
FIFO_COLOR = "#e45756"
RANDOM_COLOR = "#7f7f7f"
SETUP_COLOR = "#f58518"
BOUND_COLOR = "#54a24b"


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.15), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _job_color(j):
    return JOB_COLORS[j % len(JOB_COLORS)]


def build_jobs_chart(routing, proc):
    """Ein gestapelter Balken je Auftrag - jedes Segment ist eine Operation in der AUFTRAGSEIGENEN
    Maschinenreihenfolge, eingefärbt nach der Maschine - zeigt vor jeder Einplanung, dass jeder Auftrag seinen
    eigenen Weg durch die Maschinen hat."""
    n, m = routing.shape
    fig = go.Figure()
    shown = set()
    for pos in range(m):
        xs, ys, colors, hover = [], [], [], []
        for j in range(n):
            k = int(routing[j, pos])
            xs.append(j)
            ys.append(int(proc[j, pos]))
            colors.append(MACHINE_COLORS[k % len(MACHINE_COLORS)])
            hover.append(f"Auftrag {j}, Schritt {pos + 1}: Maschine {k + 1}, Dauer {proc[j, pos]}")
        fig.add_trace(go.Bar(x=xs, y=ys, marker_color=colors, hovertext=hover, hoverinfo="text", showlegend=False))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title_text="Auftrag")
    fig.update_yaxes(title_text="Bearbeitungszeit (gestapelt über alle Operationen)")
    return _base(fig, 280)


def build_machine_gantt(routing, proc, start, end, m, upto_ops=None):
    """EIN Trace JE MASCHINE, Farbe nach AUFTRAG (customdata für Hover) - siehe Moduldocstring."""
    n = routing.shape[0]
    all_ops = [(j, pos) for j in range(n) for pos in range(routing.shape[1])]
    all_ops.sort(key=lambda jp: end[jp[0], jp[1]])
    upto_ops = len(all_ops) if upto_ops is None else upto_ops
    included = set(all_ops[:upto_ops])
    fig = go.Figure()
    rows = [f"Maschine {k + 1}" for k in range(m)]
    for k in range(m):
        ops_k = [(j, pos) for (j, pos) in included if routing[j, pos] == k]
        ops_k.sort(key=lambda jp: start[jp[0], jp[1]])
        if not ops_k:
            continue
        xs = [float(proc[j, pos]) for (j, pos) in ops_k]
        bases = [float(start[j, pos]) for (j, pos) in ops_k]
        colors = [_job_color(j) for (j, pos) in ops_k]
        customdata = [j for (j, pos) in ops_k]
        fig.add_trace(go.Bar(x=xs, y=[rows[k]] * len(ops_k), base=bases, orientation="h", width=0.6,
                              marker=dict(color=colors, line=dict(width=1, color="white")),
                              customdata=customdata, showlegend=False, hovertemplate="Auftrag %{customdata}<br>Dauer %{x}<extra></extra>"))
    fig.update_xaxes(title_text="Zeit")
    fig.update_yaxes(categoryorder="array", categoryarray=rows, autorange="reversed")
    return _base(fig, max(160, 40 * m))


def build_machine_finish_comparison(mwkr_finish, fifo_finish):
    m = len(mwkr_finish)
    machines = [f"M{k + 1}" for k in range(m)]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=machines, y=mwkr_finish.tolist(), name="MWKR", marker_color=MACHINE_COLORS[0]))
    fig.add_trace(go.Bar(x=machines, y=fifo_finish.tolist(), name="FIFO", marker_color=FIFO_COLOR))
    fig.add_hline(y=float(mwkr_finish.max()), line=dict(color=MACHINE_COLORS[0], width=1.5, dash="dot"))
    fig.add_hline(y=float(fifo_finish.max()), line=dict(color=FIFO_COLOR, width=1.5, dash="dot"))
    fig.update_xaxes(title_text="Maschine")
    fig.update_yaxes(title_text="Fertigstellung der letzten Operation")
    fig.update_layout(barmode="group")
    return _base(fig, 320)


def build_sweep(rows, param_label, value_key="value",
                 y_keys=(("gap_spt", "MWKR gegen SPT", "#f2cf5b"), ("gap_fifo", "MWKR gegen FIFO", FIFO_COLOR), ("gap_random", "MWKR gegen Zufall", RANDOM_COLOR))):
    xs = [r[value_key] for r in rows]
    fig = go.Figure()
    for key, name, color in y_keys:
        fig.add_trace(go.Scatter(x=xs, y=[r[key] for r in rows], mode="lines+markers", line=dict(color=color, width=2.5), name=name))
    fig.update_xaxes(title_text=param_label)
    fig.update_yaxes(title_text="Abstand zu MWKR (%)")
    fig.update_layout(legend=dict(orientation="h", y=-0.3))
    return _base(fig, 360)


def build_timing(rows):
    xs = [r["value"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["exact_seconds"] * 1000 for r in rows], mode="lines+markers", line=dict(color=FIFO_COLOR, width=2.5), name="CP-SAT (Zeitlimit, im schlimmsten Fall exponentiell)"))
    fig.add_trace(go.Scatter(x=xs, y=[r["gt_seconds"] * 1000 for r in rows], mode="lines+markers", line=dict(color=MACHINE_COLORS[0], width=2.5), name="Giffler-Thompson (polynomiell in n·m)"))
    fig.update_xaxes(title_text="Aufträge")
    fig.update_yaxes(title_text="Rechenzeit (ms)", type="log")
    fig.update_layout(legend=dict(orientation="h", y=-0.3))
    return _base(fig, 340)


def build_setup_gap(rows):
    xs = [r["value"] for r in rows]
    upper = [r["gap_max"] for r in rows]
    lower = [r["gap_min"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs + xs[::-1], y=upper + lower[::-1], fill="toself", fillcolor="rgba(245,133,24,0.15)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xs, y=[r["gap_mean"] for r in rows], mode="lines+markers", line=dict(color=SETUP_COLOR, width=2.5), name="MWKR über dem echten Optimum (CP-SAT)"))
    fig.update_xaxes(title_text="Rüstzeit je Familienwechsel (Minuten)")
    fig.update_yaxes(title_text="Abstand zum Optimum (%)")
    return _base(fig, 340)


def build_theorem_chart(rows):
    """Trefferquote des Beweis-Checks: der Suchraum aktiver Zeitpläne enthält IMMER das Optimum (theorem_match_rate
    = 100 %), MWKR allein trifft es NICHT immer (mwkr_match_rate schwankt) - der Unterschied macht den Punkt."""
    xs = [r["value"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["theorem_match_rate"] * 100 for r in rows], mode="lines+markers", line=dict(color=BOUND_COLOR, width=2.5), name="Bestes aktives Schema trifft CP-SAT-Optimum"))
    fig.add_trace(go.Scatter(x=xs, y=[r["mwkr_match_rate"] * 100 for r in rows], mode="lines+markers", line=dict(color=MACHINE_COLORS[0], width=2, dash="dash"), name="MWKR allein trifft das Optimum"))
    fig.update_xaxes(title_text="Aufträge")
    fig.update_yaxes(title_text="Trefferquote (%)", range=[-5, 105])
    fig.update_layout(legend=dict(orientation="h", y=-0.3))
    return _base(fig, 340)
