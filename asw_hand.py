"""Das Handbeispiel der Demo: sechs Städte, fünf vorgegebene Züge, Late Acceptance mit einem Ring der Länge 2.

Städte 0 bis 5 bei (1,4), (6,6), (6,0), (2,0), (3,6), (3,3), Abstände nach der Manhattan-Metrik (ganzzahlig, damit sich alles von Hand
nachrechnen lässt; die Demo selbst rechnet euklidisch, die Formeln sind dieselben). Starttour 0-1-2-3-4-5 mit Länge 30, mittlere Kante 5.
Drei Zugarten mit je einer Auswertung: A = 2-opt (Stück umdrehen), B = Tausch, C = Einfügen. Die Zugfolge ist vorgegeben (sie stammt nicht
von einer der Regeln): es geht um die Gutschrift. Die Funktionen benutzen dieselben Bausteine wie die Suche (asw_moves, asw_accept,
asw_belohnung, asw_select); tests/test_handbeispiel.py rechnet alles mit Brüchen nach."""

import asw_accept as AC
import asw_belohnung as B
import asw_regeln as R
import asw_select as SE
from asw_moves import apply_move
from asw_scenario import tour_cost

PUNKTE = ((1, 4), (6, 6), (6, 0), (2, 0), (3, 6), (3, 3))
START = (0, 1, 2, 3, 4, 5)
OPTIMUM = 24                                   # Tour 0-3-2-1-4-5 (Aufzählung aller 120 Rundtouren im Test)
ZUGARTEN = ("A", "B", "C")                     # Arme 0, 1, 2 der Regeln
ZUGART_NAME = {"A": "2-opt", "B": "Tausch", "C": "Einfügen"}
_H = {"A": 2, "B": 0, "C": 1}                  # Index der Zugart in asw_moves.apply_move
# (Zugart, Zug): Positionen in der Tour
ZUEGE = (("A", (0, 3)), ("B", (2, 5)), ("C", (0, 2)), ("B", (0, 3)), ("C", (1, 3)))
ZUG_TEXT = ("A: Positionen 0 bis 3 umkehren", "B: Positionen 2 und 5 tauschen", "C: Stadt an Position 0 hinter Position 2",
            "B: Positionen 0 und 3 tauschen", "C: Stadt an Position 1 hinter Position 3")
RING = 2


def distance_matrix() -> list[list[float]]:
    return [[float(abs(ax - bx) + abs(ay - by)) for bx, by in PUNKTE] for ax, ay in PUNKTE]


def schritte(akzeptanz: str = "la") -> list[dict]:
    """Die fünf Schritte unter Late Acceptance (Ring der Länge 2) oder unter „nur besser“ ('ob').

    Je Schritt: zugart, delta (volle Neubewertung), angenommen, kosten (Länge danach), best, ring (danach), tour (danach), r2, rbest."""
    D = distance_matrix()
    t = list(START)
    cost = tour_cost(D, t)
    cost0 = cost
    kante = cost0 / len(t)
    hist = AC.new_hist(cost0, RING)
    tracker = B.BestTracker(cost0)
    zeilen = []
    for step, (z, zug) in enumerate(ZUEGE):
        neu_t = list(t)
        apply_move(neu_t, _H[z], zug)
        neu = tour_cost(D, neu_t)
        delta = neu - cost
        ok = AC.accept_ob(delta) if akzeptanz == "ob" else AC.accept_la(delta, neu, hist, step)
        if ok:
            t, cost = neu_t, neu
        AC.update_hist(hist, step, cost)
        senkung = tracker.senkung(delta, ok)
        zeilen.append(dict(schritt=step, zugart=z, text=ZUG_TEXT[step], delta=delta, angenommen=ok, kosten=cost, best=tracker.best, ring=list(hist),
                           tour=tuple(t), r2=B.reward_r2(delta, 1, kante) if ok else 0.0, rbest=B.reward_best(senkung, 1, kante)))
    return zeilen


def kennzahlen(zeilen: list[dict]) -> dict:
    """Nettogewinn des Bestwerts, Summe der strengen Verbesserungen, W, Gutschrift je Zugart nach beiden Belohnungsformen."""
    netto = tour_cost(distance_matrix(), list(START)) - zeilen[-1]["best"]
    arbeit = sum(-z["delta"] for z in zeilen if z["angenommen"] and z["delta"] < 0)
    konto = {form: {a: sum(z[form] for z in zeilen if z["zugart"] == a) for a in ZUGARTEN} for form in ("r2", "rbest")}
    return dict(netto=netto, arbeit=arbeit, w=(arbeit / netto if netto > 0 else None), konto=konto)


def zustaende(zeilen: list[dict], form: str = "r2") -> dict:
    """Was Lernautomat, Q-Lernen und Choice Function aus den fünf Belohnungen lernen (Standardparameter) und welche Zugart sie danach vorziehen.

    form: 'r2' oder 'rbest'. Rückgabe je Regel: der Zustand und `wahl` (Zugart mit der größten Wahrscheinlichkeit, dem größten Q-Wert,
    der größten Wertung); bei der Choice Function zusätzlich `wertung` je Zugart (ohne das Rauschen zum Auflösen von Gleichständen)."""
    m = len(ZUGARTEN)
    laut, q, cf = SE.new_laut(m), SE.new_q(m), SE.new_cf(m)
    for z in zeilen:
        arm = ZUGARTEN.index(z["zugart"])
        r = z[form]
        SE.update_laut(laut, arm, r)
        SE.update_q(q, arm, r)
        SE.update_cf(cf, arm, r)
    wertung = R.cf_scores(cf)

    def beste(werte):
        return ZUGARTEN[max(range(m), key=lambda j: werte[j])]
    return dict(laut=dict(p=list(laut["p"]), wahl=beste(laut["p"])), q=dict(q=list(q["q"]), wahl=beste(q["q"])),
                cf=dict(f1=list(cf["f1"]), phi=cf["phi"], wertung=wertung, wahl=beste(wertung)))
