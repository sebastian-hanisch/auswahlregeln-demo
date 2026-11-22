"""Das Handbeispiel exakt: jede Zahl der Tabellen in App und README, mit Brüchen von Hand nachgerechnet (nicht aus dem Code abgeschrieben)."""

import itertools
from fractions import Fraction as F

import pytest

import asw_algorithm as A
import asw_hand as H
from asw_scenario import tour_cost
from conftest import Skript


def test_starttour_kanten_und_optimum(hand6):
    D, t0 = hand6
    assert [D[a][b] for a, b in zip(t0, t0[1:] + t0[:1])] == [7, 6, 4, 7, 3, 3]
    assert tour_cost(D, t0) == 30
    laengen = {p: tour_cost(D, [0, *p]) for p in itertools.permutations(range(1, 6))}      # alle 120 Rundtouren ab Stadt 0
    assert len(laengen) == 120 and min(laengen.values()) == H.OPTIMUM == 24
    assert tour_cost(D, [0, 3, 2, 1, 4, 5]) == 24
    assert F(30 - 24, 24) == F(1, 4)                                                       # die Starttour liegt 25 % über dem Optimum


def test_fuenf_schritte_unter_late_acceptance():
    z = H.schritte("la")
    assert [x["delta"] for x in z] == [-2, 2, -2, 2, -2]
    assert [x["kosten"] for x in z] == [28, 30, 28, 30, 28]
    assert all(x["angenommen"] for x in z)
    assert [x["best"] for x in z] == [28] * 5
    assert [x["ring"] for x in z] == [[28, 30]] * 5
    assert [x["tour"] for x in z] == [(3, 2, 1, 0, 4, 5), (3, 2, 5, 0, 4, 1), (2, 5, 3, 0, 4, 1), (0, 5, 3, 2, 4, 1), (0, 3, 2, 5, 4, 1)]
    k = H.kennzahlen(z)
    assert k["netto"] == 2 and k["arbeit"] == 6 and k["w"] == 6 / 2 == 3


def test_fuenf_schritte_unter_nur_besser():
    z = H.schritte("ob")
    assert [x["delta"] for x in z] == [-2, 2, 6, 10, 14]                 # ab Schritt 1 auf der unveränderten Tour 3-2-1-0-4-5
    assert [x["angenommen"] for x in z] == [True, False, False, False, False]
    assert [x["kosten"] for x in z] == [28] * 5
    k = H.kennzahlen(z)
    assert k["w"] == 1 and k["konto"]["r2"] == k["konto"]["rbest"] == {"A": pytest.approx(0.4), "B": 0, "C": 0}


def test_belohnungen_und_gutschrift_je_zugart():
    z = H.schritte("la")
    e = 30 / 6                                                          # mittlere Kantenlänge 5
    assert [x["r2"] for x in z] == pytest.approx([2 / e, 0, 2 / e, 0, 2 / e], abs=1e-15)
    assert [x["rbest"] for x in z] == pytest.approx([2 / e, 0, 0, 0, 0], abs=1e-15)
    k = H.kennzahlen(z)["konto"]
    assert k["r2"] == pytest.approx({"A": 2 / 5, "B": 0, "C": 4 / 5})
    assert k["rbest"] == pytest.approx({"A": 2 / 5, "B": 0, "C": 0})
    assert sum(k["rbest"].values()) == pytest.approx(2 / e)             # Teleskopsumme: Nettogewinn / mittlere Kante


def _laut(p, arm, r, a=F(1, 20), boden=F(1, 100)):
    if r <= 0:
        return p
    p = [x * (1 - a) for x in p]
    p[arm] += a
    p = [max(x, boden) for x in p]
    return [x / sum(p) for x in p]


def test_lernautomat_in_bruechen():
    arme = [H.ZUGARTEN.index(z) for z, _ in H.ZUEGE]
    for form, r, erwartet, wahl in (("r2", [F(2, 5), 0, F(2, 5), 0, F(2, 5)], [F(7942, 24000), F(6859, 24000), F(9199, 24000)], "C"),
                                    ("rbest", [F(2, 5), 0, 0, 0, 0], [F(11, 30), F(19, 60), F(19, 60)], "A")):
        p = [F(1, 3)] * 3
        zwischen = []
        for arm, rr in zip(arme, r):
            p = _laut(p, arm, rr)
            zwischen.append(p)
        assert p == erwartet
        if form == "r2":
            assert zwischen[0] == [F(11, 30), F(19, 60), F(19, 60)] and zwischen[2] == [F(418, 1200), F(361, 1200), F(421, 1200)]
        z = H.zustaende(H.schritte("la"), form)["laut"]
        assert z["p"] == pytest.approx([float(x) for x in erwartet], abs=1e-15) and z["wahl"] == wahl


def test_q_lernen_in_bruechen():
    arme = [H.ZUGARTEN.index(z) for z, _ in H.ZUEGE]
    for form, r, wahl in (("r2", [F(2, 5), 0, F(2, 5), 0, F(2, 5)], "C"), ("rbest", [F(2, 5), 0, 0, 0, 0], "A")):
        q = [F(0)] * 3
        for arm, rr in zip(arme, r):
            q[arm] += F(1, 10) * (rr + F(1, 2) * max(q) - q[arm])
        z = H.zustaende(H.schritte("la"), form)["q"]
        assert z["q"] == pytest.approx([float(x) for x in q], abs=1e-15) and z["wahl"] == wahl
        if form == "r2":
            assert [round(float(x), 4) for x in q] == [0.04, 0.0039, 0.0799]
            assert q[0] == F(1, 25)
        else:
            assert [round(float(x), 4) for x in q] == [0.04, 0.0038, 0.0038]


def test_choice_function_von_hand():
    z = H.zustaende(H.schritte("la"), "r2")["cf"]
    assert z["f1"] == pytest.approx([0.4, 0, 0.4 + 0.9 * 0.4]) and z["phi"] == 0.99
    # A: 0,99 * (0,4 / 0,76) + 0,01 * 4 / 50; B: 0,01 * 1 / 50; C: 0,99 * 1 (gerade angewandt, Wartezeit 0); der Paarterm nach C ist leer
    assert z["wertung"] == pytest.approx([0.99 * 0.4 / 0.76 + 0.01 * 4 / 50, 0.01 * 1 / 50, 0.99], abs=1e-9)
    assert [round(w, 5) for w in z["wertung"]] == [0.52185, 0.0002, 0.99] and z["wahl"] == "C"
    b = H.zustaende(H.schritte("la"), "rbest")["cf"]
    assert b["f1"] == pytest.approx([0.4, 0, 0]) and b["phi"] == pytest.approx(0.99 - 4 * 0.01)
    assert b["wertung"] == pytest.approx([0.95 + 0.05 * 4 / 50, 0.05 * 1 / 50, 0.0], abs=1e-9) and b["wahl"] == "A"
    assert [round(w, 4) for w in b["wertung"]] == [0.954, 0.001, 0.0]


def test_dieselben_fuenf_schritte_ueber_die_suche(hand6):
    """`run_on` mit vorgegebener Zugfolge und vorgegebenem Zufallsstrom: die Suche macht genau die fünf Schritte der Tabelle.

    Zufallswerte je Vorschlag (asw_moves): 2-opt (0, 3): i = int(u * 5) = 0, j = 1 + int(u * 3) = 3; Tausch (2, 5): i = int(u * 6) = 2,
    j = (2 + 2 + int(u * 3)) % 6 = 5; Einfügen (0, 2): i = 0, j = (0 + 1 + int(u * 4)) % 6 = 2; Tausch (0, 3); Einfügen (1, 3)."""
    D, t0 = hand6
    folge = [2, 0, 1, 0, 1]                                             # Positionen in arms = (0, 1, 2): Tausch, Einfügen, 2-opt
    fest = (lambda m: {"k": 0}, lambda s, rng: folge[s["k"]], lambda s, arm, r: s.__setitem__("k", s["k"] + 1))
    rng = Skript([0.0, 0.7, 0.4, 0.4, 0.0, 0.3, 0.0, 0.4, 0.2, 0.3])
    r = A.run_on(D, t0, rng, akz="la", belohnung="r2", menge=(0, 1, 2), budget=5, spur=True, funktionen=fest, check=True)
    k = r["konto"]
    assert rng.gezogen == 10 and r["used"] == 5 and r["best"] == 28 and r["final"] == 28
    assert [(h, d, ok, c, b) for h, d, _, ok, c, b, _ in k.spur] == [(2, -2, True, 28, 28), (0, 2, True, 30, 28), (1, -2, True, 28, 28),
                                                                    (0, 2, True, 30, 28), (1, -2, True, 28, 28)]
    assert k.apps[:3] == [2, 2, 1] and r["tour"] == [0, 3, 2, 5, 4, 1]
    assert k.gut_r2[:3] == pytest.approx([0, 0.8, 0.4]) and k.gut_best[:3] == pytest.approx([0, 0, 0.4])
    assert r["w"] == 3 and r["anteil_ohne"] == pytest.approx(2 / 3)     # 0,8 von 1,2 Gutschrift ohne neuen Bestwert
    assert k.verschlechterungen == 2
