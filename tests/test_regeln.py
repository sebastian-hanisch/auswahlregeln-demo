"""Auswahlregeln dieser Demo je Einheit: Zufallsgradient, UCB, Fassungen mit Parameter, verdünnte Choice Function."""

import math
import random

import pytest

import asw_constants as C
import asw_regeln as R
import asw_select as SE
from asw_rng import SplitMix64
from conftest import Skript


def test_zufallsgradient_behaelt_nach_erfolg_und_wuerfelt_nach_misserfolg():
    s = R.new_rg(4)
    rng = Skript([0.6, 0.1])
    assert R.choose_rg(s, rng) == 2 and rng.gezogen == 1                 # am Anfang gleichverteilt: int(0,6 * 4)
    R.update_rg(s, 2, 0.3)
    assert R.choose_rg(s, rng) == 2 and rng.gezogen == 1                 # Erfolg: dieselbe Zugart, keine Zufallszahl
    R.update_rg(s, 2, 0.0)
    assert R.choose_rg(s, rng) == 0 and rng.gezogen == 2                 # Misserfolg: neu würfeln
    assert R.choose_rg(R.new_rg(1), Skript([])) == 0                     # eine einzige Zugart braucht keine Zufallszahl


def test_ucb_waehlt_erst_jeden_arm_einmal():
    s = R.new_ucb(3)
    gesehen = []
    for u in (0.9, 0.0, 0.5):
        a = R.choose_ucb(s, Skript([u]))
        gesehen.append(a)
        R.update_ucb(s, a, 0.0)
    assert sorted(gesehen) == [0, 1, 2] and gesehen[0] == 2


def test_ucb_index_ohne_vergessen_ist_die_ucb1_formel():
    """c = 1, gamma = 1, größte Belohnung 1: Index = Mittelwert + sqrt(2 ln t / n_j) (Grundform von UCB1)."""
    s = R.new_ucb(3, c=1.0, gamma=1.0)
    folge = [(0, 1.0), (1, 0.25), (2, 0.5), (0, 0.0), (1, 0.75), (0, 0.5)]
    for arm, r in folge:
        R.update_ucb(s, arm, r)
    mittel = [(1.0 + 0.0 + 0.5) / 3, (0.25 + 0.75) / 2, 0.5]
    zahl = [3, 2, 1]
    erwartet = [mittel[j] + math.sqrt(2 * math.log(6) / zahl[j]) for j in range(3)]
    assert R.ucb_index(s) == pytest.approx(erwartet, rel=1e-12)
    assert R.choose_ucb(s, Skript([])) == 2                              # der selten gewählte Arm hat den größten Bonus


def test_ucb_mit_vergessen_gegen_direkte_summen():
    """Unabhängige Rechnung: n_j = Summe gamma^Alter, s_j = Summe r * gamma^Alter, N = Summe aller gamma^Alter."""
    g, c = 0.9, 0.2
    s = R.new_ucb(2, c=c, gamma=g)
    folge = [(0, 0.2), (1, 0.6), (1, 0.0), (0, 0.4), (1, 0.1)]
    for arm, r in folge:
        R.update_ucb(s, arm, r)
    t = len(folge)
    n = [sum(g ** (t - 1 - k) for k, (a, _) in enumerate(folge) if a == j) for j in range(2)]
    su = [sum(r * g ** (t - 1 - k) for k, (a, r) in enumerate(folge) if a == j) for j in range(2)]
    gesamt = sum(g ** k for k in range(t))
    erwartet = [su[j] / n[j] / 0.6 + c * math.sqrt(2 * math.log(gesamt) / n[j]) for j in range(2)]
    assert R.ucb_index(s) == pytest.approx(erwartet, rel=1e-9)
    assert R.log_wirksame_anzahl(t, g) == pytest.approx(math.log(gesamt), rel=1e-12)
    assert R.log_wirksame_anzahl(1, g) == 0.0 and R.log_wirksame_anzahl(0, g) == 0.0


def test_ucb_bonus_bei_gleichverteilung():
    """Bonus c * sqrt(2 ln N / n) bei c = 0,2, N = 100 Anwendungen, n = 12,5 je Zugart: 0,1717."""
    assert round(C.UCB_C * math.sqrt(2 * math.log(100) / 12.5), 4) == 0.1717


@pytest.mark.parametrize("regel", ["cf", "laut", "q"])
def test_fassung_mit_parameter_ist_mit_dem_standardwert_bitgleich_zur_kopie(regel):
    _, standard, _, _ = C.PARAMETER[regel]
    neu_a, wahl_a, lern_a = SE.REGEL_FUNKTIONEN[regel]
    neu_b, wahl_b, lern_b = R.regel_funktionen(regel, standard)
    z = random.Random(5)
    a, b = neu_a(5), neu_b(5)
    ra, rb = SplitMix64(11), SplitMix64(11)
    for _ in range(400):
        x, y = wahl_a(a, ra), wahl_b(b, rb)
        assert x == y
        r = 0.0 if z.random() < 0.6 else z.random()
        lern_a(a, x, r)
        lern_b(b, y, r)
    assert a == b


@pytest.mark.parametrize("regel", ["cf", "laut", "q", "ucb"])
def test_anderer_parameterwert_aendert_das_lernen(regel):
    _, _, niedrig, hoch = C.PARAMETER[regel]
    folgen = []
    for wert in (niedrig, hoch):
        neu, wahl, lern = R.regel_funktionen(regel, wert)
        s = neu(4)
        rng = SplitMix64(3)
        z = random.Random(9)
        folge = []
        for _ in range(300):
            a = wahl(s, rng)
            folge.append(a)
            lern(s, a, 0.0 if z.random() < 0.85 else z.random())
        folgen.append((folge, repr(s)))                                 # die Choice Function kann sich früh festlegen: dann unterscheidet sich nur der Zustand
    assert folgen[0] != folgen[1]


def test_parameter_wert_je_einstellung():
    assert R.parameter_wert("cf", "standard") is None and R.parameter_wert("rand", "hoch") is None
    assert R.parameter_wert("ucb", "niedrig") == 0.05 and R.parameter_wert("ucb", "hoch") == 1.0
    assert R.parameter_wert("laut", "niedrig") == 0.02 and R.parameter_wert("q", "hoch") == 0.3 and R.parameter_wert("cf", "hoch") == 0.99


def test_verduennte_choice_function():
    neu, wahl, _ = R.regel_funktionen("cfv", 0.25)
    s = neu(4)
    rng = Skript([0.1, 0.8])
    assert wahl(s, rng) == 3 and rng.gezogen == 2                        # u < p: gleichverteilt, int(0,8 * 4)
    rng = Skript([0.9, 0.5, 0.5, 0.5, 0.5])
    a = wahl(s, rng)                                                     # u >= p: die Choice Function zieht je Arm eine Zahl
    assert rng.gezogen == 5 and a == SE.choose_cf(SE.new_cf(4), Skript([0.5] * 4))
    _, wahl0, lern0 = R.regel_funktionen("cfv", 0.0)                     # p = 0: immer die Wahl der Choice Function
    s0, s1 = SE.new_cf(4), SE.new_cf(4)
    z = random.Random(1)
    for _ in range(60):
        werte = [z.random() for _ in range(4)]
        x, y = wahl0(s0, Skript([0.5, *werte])), SE.choose_cf(s1, Skript(werte))
        assert x == y
        r = 0.0 if z.random() < 0.5 else z.random()
        lern0(s0, x, r)
        SE.update_cf(s1, y, r)
    assert s0 == s1


def test_cf_wertung_passt_zur_wahl_der_kopie():
    z = random.Random(2)
    s = SE.new_cf(6)
    rng = SplitMix64(4)
    for _ in range(300):
        werte = R.cf_scores(s)
        a = SE.choose_cf(s, rng)
        assert werte[a] >= max(werte) - 2e-9                             # das Rauschen entscheidet nur innerhalb von 1e-9
        SE.update_cf(s, a, 0.0 if z.random() < 0.7 else z.random())
