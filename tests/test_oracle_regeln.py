"""Orakel der Auswahlregeln: Lernautomat, Q-Lernen, Choice Function und UCB gegen eine Referenz in exakten Brüchen.

Die Referenz ist aus der Formelbeschreibung neu geschrieben (nicht aus dem Code abgeleitet) und rechnet mit `fractions.Fraction`; verglichen
wird auf 50 Zufallsfolgen von Zugarten und Belohnungen mit Toleranz 1e-12. Anderer Rechenweg: keine Gleitkommazahl, direkte Summen statt
fortgeschriebener Zustände (UCB), neu aufgebaute Listen statt Änderung an Ort und Stelle."""

import math
import random
from fractions import Fraction as F

import pytest

import asw_regeln as R
import asw_select as SE

FOLGEN = 50
SCHRITTE = 60


def _folge(seed: int, m: int):
    z = random.Random(seed)
    return [(z.randrange(m), F(0) if z.random() < 0.5 else F(z.randrange(1, 1000), 1000)) for _ in range(SCHRITTE)]


@pytest.mark.parametrize("seed", range(FOLGEN))
def test_lernautomat_gegen_brueche(seed):
    m = 3 + seed % 6
    s = SE.new_laut(m)
    p = [F(1, m)] * m
    for arm, r in _folge(seed, m):
        SE.update_laut(s, arm, float(r))
        if r > 0:
            p = [x * F(19, 20) + (F(1, 20) if j == arm else 0) for j, x in enumerate(p)]
            p = [max(x, F(1, 100)) for x in p]
            p = [x / sum(p) for x in p]
    assert s["p"] == pytest.approx([float(x) for x in p], abs=1e-12)
    assert sum(p) == 1 and min(p) >= F(1, 100) / (1 + m * F(1, 100))     # Untergrenze vor dem Normieren 0,01, danach knapp darunter möglich


@pytest.mark.parametrize("seed", range(FOLGEN))
def test_q_lernen_gegen_brueche(seed):
    m = 3 + seed % 6
    s = SE.new_q(m)
    q = [F(0)] * m
    for arm, r in _folge(seed, m):
        SE.update_q(s, arm, float(r))
        ziel = r + F(1, 2) * max(q)
        q = [x + F(1, 10) * (ziel - x) if j == arm else x for j, x in enumerate(q)]
    assert s["q"] == pytest.approx([float(x) for x in q], abs=1e-12)


@pytest.mark.parametrize("seed", range(FOLGEN))
def test_choice_function_gegen_brueche(seed):
    """f1 und f2 als geometrisch abgewertete Summen direkt aus der Folge, phi als Zähler der Misserfolge seit dem letzten Erfolg."""
    m = 3 + seed % 6
    folge = _folge(seed, m)
    s = SE.new_cf(m)
    for arm, r in folge:
        SE.update_cf(s, arm, float(r))
    a = F(9, 10)
    f1 = [F(0)] * m
    for j in range(m):
        stellen = [k for k, (arm, _) in enumerate(folge) if arm == j]
        f1[j] = sum(folge[k][1] * a ** (len(stellen) - 1 - i) for i, k in enumerate(stellen))
    assert s["f1"] == pytest.approx([float(x) for x in f1], abs=1e-12)
    letzter = folge[-1][0]
    for j in range(m):                                                   # Paarterm: Belohnungen von j direkt nach `letzter`
        stellen = [k for k in range(1, len(folge)) if folge[k][0] == j and folge[k - 1][0] == letzter]
        erwartet = sum(folge[k][1] * a ** (len(stellen) - 1 - i) for i, k in enumerate(stellen))
        assert s["f2"][letzter][j] == pytest.approx(float(erwartet), abs=1e-12)
    erfolge = [k for k, (_, r) in enumerate(folge) if r > 0]
    phi = F(99, 100) - F(1, 100) * (len(folge) - 1 - erfolge[-1]) if erfolge else F(1, 2) - F(1, 100) * len(folge)
    phi = max(phi, F(1, 100))
    assert s["phi"] == pytest.approx(float(phi), abs=1e-12)
    # Wertung: phi * (f1 / max f1 + f2 / max f2) + (1 - phi) * min(Wartezeit, 50) / 50
    zeile = [F(s["f2"][letzter][j]) for j in range(m)]
    for j, w in enumerate(R.cf_scores(s)):
        warte = len(folge) - max((k + 1 for k, (arm, _) in enumerate(folge) if arm == j), default=0)
        teil1 = f1[j] / max(f1) if max(f1) > 0 else 0
        teil2 = zeile[j] / max(zeile) if max(zeile) > 0 else 0
        assert w == pytest.approx(float(phi * (teil1 + teil2) + (1 - phi) * F(min(warte, 50), 50)), abs=1e-9)


@pytest.mark.parametrize("seed", range(FOLGEN))
def test_ucb_gegen_direkte_summen_in_bruechen(seed):
    m = 3 + seed % 4
    z = random.Random(1000 + seed)
    folge = [(j, F(z.randrange(0, 1000), 1000)) for j in range(m)] + _folge(seed, m)     # jede Zugart mindestens einmal
    g = F(199, 200)
    s = R.new_ucb(m)
    for arm, r in folge:
        R.update_ucb(s, arm, float(r))
    t = len(folge)
    n = [sum(g ** (t - 1 - k) for k, (arm, _) in enumerate(folge) if arm == j) for j in range(m)]
    su = [sum(r * g ** (t - 1 - k) for k, (arm, r) in enumerate(folge) if arm == j) for j in range(m)]
    rmax = max(max(r for _, r in folge), F(1, 10 ** 12))
    gesamt = float(sum(n))
    erwartet = [float(su[j] / n[j] / rmax) + 0.2 * math.sqrt(2 * math.log(gesamt) / float(n[j])) for j in range(m)]
    assert R.ucb_index(s) == pytest.approx(erwartet, rel=1e-9, abs=1e-12)
    assert R.choose_ucb(s, None) == max(range(m), key=lambda j: (erwartet[j], -j)) or \
        sorted(erwartet)[-1] - sorted(erwartet)[-2] < 1e-9               # bei praktisch gleichem Index entscheidet die Rundung
