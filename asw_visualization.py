"""Plotly-Abbildungen der Demo. Alle Achsen sind fest (`fixedrange`), damit das Scrollen auf Touch-Geräten nicht am Diagramm hängen bleibt."""

import plotly.graph_objects as go

import asw_constants as C

_LAYOUT = dict(margin=dict(l=10, r=10, t=40, b=10), height=340, legend=dict(orientation="h", yanchor="bottom", y=-0.35, x=0))


def _fest(fig: go.Figure, **layout) -> go.Figure:
    fig.update_layout(**{**_LAYOUT, **layout})
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _duenn(xs: list, punkte: int = 400) -> list[int]:
    """Indizes einer ausgedünnten Folge (höchstens `punkte`), immer mit dem letzten Element."""
    n = len(xs)
    if n <= punkte:
        return list(range(n))
    schritt = n / punkte
    idx = sorted({int(i * schritt) for i in range(punkte)} | {n - 1})
    return idx


def fig_verlauf(spur, start: float, k: int) -> go.Figure:
    """Länge der aktuellen und der besten Tour über die Auswertungen bis zur Anwendung k; angenommene Verschlechterungen als Punkte."""
    teil = spur[:k]
    used = 0
    xs, cur, best, vx, vy = [0], [start], [start], [], []
    for _, delta, kosten, ok, cost, b, _ in teil:
        used += kosten
        xs.append(used)
        cur.append(cost)
        best.append(b)
        if ok and delta > C.EPS:
            vx.append(used)
            vy.append(cost)
    idx = _duenn(xs)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[xs[i] for i in idx], y=[round(cur[i], 2) for i in idx], mode="lines", name="aktuelle Tour", line=dict(color=C.COLOR_ZUFALL, width=1)))
    fig.add_trace(go.Scatter(x=[xs[i] for i in idx], y=[round(best[i], 2) for i in idx], mode="lines", name="beste Tour", line=dict(color=C.COLOR_BEST, width=2)))
    if vx:
        j = _duenn(vx, 300)
        fig.add_trace(go.Scatter(x=[vx[i] for i in j], y=[round(vy[i], 2) for i in j], mode="markers", name="angenommene Verschlechterung",
                                 marker=dict(color=C.COLOR_SCHLECHT, size=4, opacity=0.6)))
    return _fest(fig, title="Länge der Tour über die Auswertungen", xaxis_title="Auswertungen", yaxis_title="Länge")


def fenster_anteile(spur, k: int, fenster: int = C.FENSTER, punkte: int = 120) -> tuple[list[int], list[list[float]]]:
    """Anteil je Zugart an den letzten `fenster` Anwendungen, an höchstens `punkte` Stellen bis zur Anwendung k. Rückgabe (Stellen, Anteile[h])."""
    teil = [z[0] for z in spur[:k]]
    if not teil:
        return [], [[] for _ in range(C.K)]
    stellen = sorted({max(1, int((i + 1) * len(teil) / punkte)) for i in range(punkte)})
    anteile = [[] for _ in range(C.K)]
    for s in stellen:
        ausschnitt = teil[max(0, s - fenster):s]
        for h in range(C.K):
            anteile[h].append(100.0 * ausschnitt.count(h) / len(ausschnitt))
    return stellen, anteile


def fig_fenster(spur, arms, k: int) -> go.Figure:
    stellen, anteile = fenster_anteile(spur, k)
    fig = go.Figure()
    for h in arms:
        fig.add_trace(go.Scatter(x=stellen, y=[round(a, 1) for a in anteile[h]], mode="lines", stackgroup="eins", name=C.HNAMEN[h],
                                 line=dict(width=0.5, color=C.FARBE_ZUGART[h])))
    return _fest(fig, title=f"Anteil je Zugart an den letzten {C.FENSTER} Anwendungen", xaxis_title="Anwendung", yaxis_title="Anteil in %",
                 yaxis_range=[0, 100])


def fig_anteile(anteil_apps, anteil_evals, arms, gleich_apps: float, key_titel: str = "Anteil je Zugart über den ganzen Lauf") -> go.Figure:
    """Balken: Anteil je Zugart an Anwendungen und Auswertungen (Prozent); gestrichelt die Gleichverteilung der Anwendungen."""
    namen = [C.HNAMEN[h] for h in arms]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=namen, y=[round(100 * anteil_apps[h], 1) for h in arms], name="Anwendungen", marker_color=C.COLOR_REGEL))
    fig.add_trace(go.Bar(x=namen, y=[round(100 * anteil_evals[h], 1) for h in arms], name="Auswertungen", marker_color=C.COLOR_BEST))
    fig.add_hline(y=gleich_apps, line_dash="dash", line_color=C.COLOR_ZUFALL)
    return _fest(fig, title=key_titel, yaxis_title="Anteil in %", barmode="group", yaxis_range=[0, 100])


def fig_konto(gut_r2, gut_best, arms) -> go.Figure:
    """Gutschriftkonto: Summe der Belohnung je Zugart nach der Standardform und nach „nur Bestwert“."""
    namen = [C.HNAMEN[h] for h in arms]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=namen, y=[round(gut_r2[h], 3) for h in arms], name="Standard (Verbesserung der aktuellen Tour)", marker_color=C.COLOR_REGEL))
    fig.add_trace(go.Bar(x=namen, y=[round(gut_best[h], 3) for h in arms], name="nur Verbesserung des Bestwerts", marker_color=C.COLOR_BEST))
    return _fest(fig, title="Gutschriftkonto dieses Laufs", yaxis_title="Summe der Belohnung", barmode="group")


def fig_wirkung(zeilen, titel: str) -> go.Figure:
    """Unterschied zu Zufall mit Intervall je Zeile; zeilen = [(Beschriftung, d, lo, hi, klasse)]."""
    farbe = {"besser": C.COLOR_GUT, "schlechter": C.COLOR_SCHLECHT, "gleich": C.COLOR_ZUFALL}
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[round(z[1], 3) for z in zeilen], y=[z[0] for z in zeilen], mode="markers",
        marker=dict(color=[farbe[z[4]] for z in zeilen], size=9),
        error_x=dict(type="data", symmetric=False, array=[round(z[3] - z[1], 3) for z in zeilen], arrayminus=[round(z[1] - z[2], 3) for z in zeilen],
                     color=C.COLOR_ZUFALL, thickness=1),
        showlegend=False))
    fig.add_vline(x=0, line_color=C.COLOR_ZUFALL)
    fig.add_vline(x=C.MARKE_KLAR, line_dash="dot", line_color=C.COLOR_GUT)
    return _fest(fig, title=titel, xaxis_title="Zufall minus Regel in Prozentpunkten (rechts: Regel besser)", height=max(260, 60 + 26 * len(zeilen)),
                 yaxis_autorange="reversed")


def fig_mini(je_instanz) -> go.Figure:
    """Mini-Reihe: Unterschied je Instanz, sortiert."""
    werte = sorted(je_instanz)
    fig = go.Figure(go.Bar(x=list(range(1, len(werte) + 1)), y=[round(v, 3) for v in werte],
                           marker_color=[C.COLOR_GUT if v > 0 else C.COLOR_SCHLECHT for v in werte], showlegend=False))
    fig.add_hline(y=0, line_color=C.COLOR_ZUFALL)
    return _fest(fig, title="Unterschied je Instanz (sortiert; über 0: Regel besser)", xaxis_title="Instanz (Rang)", yaxis_title="Prozentpunkte", height=300)
