"""Orakel der Suche mit Gutschriftkonto: ein von `run` unabhängiger Nachrechner liest die Spur und baut alles neu auf.

Aus (Zugart, Änderung, Auswertungen) je Anwendung rekonstruiert er die Annahme nach der Akzeptanzregel, die Länge, den Bestwert, beide
Belohnungen, die Gutschrift je Zugart, W und den Anteil ohne neuen Bestwert. Anderer Rechenweg: eine einzige Schleife über die Spur mit
eigenen Formeln (Liste von Late Acceptance als Liste aller bisherigen Längen statt als Ring), ohne asw_accept und asw_belohnung."""

import pytest

import asw_algorithm as A
import asw_constants as C

FAELLE = [(f, n, i, regel, akz) for f, n, i in (("gleich", 30, 3), ("cluster", 60, 11), ("gitter", 30, 40))
          for regel in ("rand", "cf", "laut", "ucb") for akz in C.AKZEPTANZEN]


def nachrechnen(spur, start: float, n: int, akz: str) -> dict:
    kante = start / n
    cost = start
    best = start
    laengen = []                                                         # Länge nach jeder Anwendung
    gut_r2 = [0.0] * C.K
    gut_best = [0.0] * C.K
    arbeit = 0.0
    ohne = 0.0
    fehler = []
    for k, (h, delta, kosten, ok, cost_spur, best_spur, _) in enumerate(spur):
        neu = cost + delta
        if akz == "ob":
            soll = delta < -1e-9
        elif akz == "rr":
            soll = delta <= 1e-9 or neu <= 1.01 * best
        else:
            schwelle = laengen[k - 50] if k >= 50 else start             # Länge vor 50 Anwendungen, anfangs die Startlänge
            soll = delta <= 1e-9 or neu <= schwelle
        if soll != ok:
            fehler.append(("Annahme", k))
        vorher = best
        if soll:
            cost = neu
            if cost < best - 1e-9:                                       # dieselbe Tour mit Rundungsrest (unter 1e-9) ist kein neuer Bestwert
                best = cost
        laengen.append(cost)
        if abs(cost - cost_spur) > 1e-6 or abs(best - best_spur) > 1e-6:
            fehler.append(("Länge", k))
        if delta < -1e-9:
            r2 = min(1.0, -delta / (kosten * kante))
            arbeit += -delta
            gut_r2[h] += r2
            if best >= vorher:
                ohne += r2
        if best < vorher:
            gut_best[h] += min(1.0, (vorher - best) / (kosten * kante))
    return dict(best=best, final=cost, gut_r2=gut_r2, gut_best=gut_best, arbeit=arbeit, ohne=ohne, fehler=fehler)


@pytest.mark.parametrize("familie,n,idx,regel,akz", FAELLE)
def test_nachrechner_bestaetigt_spur_und_konto(familie, n, idx, regel, akz):
    r = A.run(familie, n, idx, 1, regel, akz, "r2", budget=60 * n, spur=True)
    k = r["konto"]
    x = nachrechnen(k.spur, r["start"], n, akz)
    assert not x["fehler"], x["fehler"][:3]
    assert x["best"] == pytest.approx(r["best"], rel=1e-12) and x["final"] == pytest.approx(r["final"], rel=1e-12)
    assert k.gut_r2 == pytest.approx(x["gut_r2"], rel=1e-9, abs=1e-12) and k.gut_best == pytest.approx(x["gut_best"], rel=1e-6, abs=1e-9)
    assert k.verbesserung == pytest.approx(x["arbeit"], rel=1e-9)
    assert r["w"] == pytest.approx(x["arbeit"] / (r["start"] - x["best"]), rel=1e-9)
    assert r["anteil_ohne"] == pytest.approx(x["ohne"] / sum(x["gut_r2"]), rel=1e-9, abs=1e-12)
    assert sum(z[2] for z in k.spur) == r["used"] == 60 * n and len(k.spur) == r["steps"]
    assert [sum(1 for z in k.spur if z[0] == h) for h in range(C.K)] == k.apps == r["apps"]


@pytest.mark.parametrize("form", ["best", "r1"])
def test_belohnung_in_der_spur_gegen_die_formel(form):
    """Die Belohnung, die die Regel liest (letzte Spalte der Spur), aus Änderung und Bestwert neu gerechnet."""
    r = A.run("gleich", 30, 5, 0, "q", "la", form, budget=3000, spur=True)
    kante = r["start"] / 30
    vorher = r["start"]
    for h, delta, kosten, ok, cost, best, bel in r["konto"].spur:
        if form == "best":
            assert bel == pytest.approx(min(1.0, max(0.0, vorher - best) / (kosten * kante)), abs=1e-9)
        else:
            assert bel == pytest.approx(min(1.0, -delta / kante) if delta < -1e-9 else 0.0, abs=1e-12)
        vorher = best
