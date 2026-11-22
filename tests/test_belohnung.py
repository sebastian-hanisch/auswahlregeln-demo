"""Belohnungsformen je Einheit: Formeln an Handwerten, Kappung, Gedächtnis (Fenster, gleitendes Mittel, Bestwert)."""

import pytest

import asw_belohnung as B
import asw_constants as C
import asw_select as SE


def test_r2_r1_best_an_handwerten_und_kappung():
    assert B.reward_r2(-2.0, 1, 5.0) == 2 / 5 and B.reward_r2(-2.0, 5, 5.0) == 2 / 25
    assert B.reward_r2(-30.0, 1, 5.0) == 1.0 and B.reward_r2(0.0, 1, 5.0) == 0.0 and B.reward_r2(2.0, 1, 5.0) == 0.0
    assert B.reward_r2(-1e-10, 1, 5.0) == 0.0                           # unter der Toleranz 1e-9: keine Verbesserung
    assert B.reward_r1(-2.0, 5.0) == 2 / 5 and B.reward_r1(-7.0, 5.0) == 1.0 and B.reward_r1(1.0, 5.0) == 0.0
    assert B.reward_best(2.0, 1, 5.0) == 2 / 5 and B.reward_best(0.0, 1, 5.0) == 0.0 and B.reward_best(9.0, 1, 5.0) == 1.0


@pytest.mark.parametrize("delta,kosten", [(-3.0, 1), (-0.2, 5), (0.0, 1), (4.0, 2), (-99.0, 1)])
def test_r2_ist_die_standardbelohnung_der_kopie(delta, kosten):
    assert B.reward_r2(delta, kosten, 7.5) == SE.reward_standard(delta, kosten, 7.5)
    assert B.make_reward("r2", 7.5, 60.0)(delta, kosten, True) == SE.standard_reward(7.5)(delta, kosten, True)


def test_rang_zaehlt_kleinere_werte_im_fenster_der_letzten_30():
    assert B.reward_rank(0.3, [0.0, 0.1, 0.3, 0.5]) == 2 / 30            # zwei Werte kleiner, bezogen auf die Fensterlänge 30
    assert B.reward_rank(0.0, [0.0, 0.1]) == 0.0
    b = B.make_reward("rank", 5.0, 30.0)
    assert b(-2.0, 1, True) == 0.0                                       # leeres Fenster
    assert b(1.0, 1, False) == 0.0
    assert b(-2.5, 1, True) == 2 / 30                                    # 0,4 und 0 liegen darunter
    for _ in range(40):
        b(1.0, 1, False)
    assert len(b.fenster) == C.RANK_FENSTER and b(-0.5, 1, True) == 1.0  # 30 Nullen im Fenster


def test_gleitendes_mittel():
    b = B.make_reward("ma", 5.0, 30.0)
    assert b(-2.0, 1, True) == 1.0                                       # erstes Mittel = 0,4
    assert b(1.0, 1, True) == 0.0 and b.mittel == pytest.approx(0.4)
    r = b(-1.0, 1, True)                                                 # Mittel 0,4 + 0,05 * (0,2 - 0,4) = 0,39
    assert b.mittel == pytest.approx(0.39) and r == pytest.approx(0.2 / 0.39)


def test_nur_bestwert_fuehrt_laenge_und_bestwert_mit():
    b = B.make_reward("best", 5.0, 30.0)
    assert b(-2.0, 1, True) == 2 / 5                                     # 30 -> 28, neuer Bestwert
    assert b(2.0, 1, True) == 0.0                                        # 28 -> 30 angenommen
    assert b(-2.0, 1, True) == 0.0                                       # 30 -> 28: Reparatur, kein neuer Bestwert
    assert b(-3.0, 1, False) == 0.0                                      # nicht angenommen zählt nicht
    assert b(-3.0, 5, True) == pytest.approx(3 / 25)                     # 28 -> 25
    assert (b.tracker.cost, b.tracker.best) == (25.0, 25.0)


def test_unbekannte_form_wird_abgelehnt():
    with pytest.raises(ValueError):
        B.make_reward("xyz", 1.0, 1.0)
