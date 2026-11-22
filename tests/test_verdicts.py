"""Verdikte als reine Funktionen: Schwellen auf der Grenze, jede Zahl im Text an handgesetzten Zeilen, Zweige mit Nenner 0."""

import pytest

import asw_constants as C
import asw_evaluation as E


def test_zahlformat():
    assert E.de(1.5) == "1,50" and E.de(-0.126, 2, True) == "−0,13" and E.de(0.48, 2, True) == "+0,48" and E.de(63.64, 1) == "63,6"
    assert E.tsd(600000) == "600 000" and E.tsd(1152000) == "1 152 000" and E.tsd(999) == "999"
    assert E.intervall(0.04, 0.92) == "[+0,04; +0,92]" and E.intervall(-2.39, -1.5) == "[−2,39; −1,50]"


@pytest.mark.parametrize("d,lo,hi,erwartet", [
    (0.25, 0.01, 0.5, "besser"), (0.249, 0.01, 0.5, "gleich"), (0.25, 0.0, 0.5, "gleich"), (0.9, -0.1, 1.9, "gleich"),
    (-0.10, -0.3, -0.01, "schlechter"), (-0.099, -0.3, -0.01, "gleich"), (-0.10, -0.3, 0.0, "gleich"), (0.0, -0.1, 0.1, "gleich"),
])
def test_urteil_unterschied_auf_den_marken(d, lo, hi, erwartet):
    assert E.urteil_unterschied(d, lo, hi) == erwartet


def test_verdict_anteil_schwellen_und_zahlen():
    art, text = E.verdict_anteil("Choice Function", "2opt_b5", 50.0, 83.3, 12.5, 41.7)
    assert art == "warning" and "legt sich in diesem Lauf fest" in text and "50,0 %" in text and "83,3 %" in text and "12,5 %" in text and "41,7 %" in text
    art, text = E.verdict_anteil("Q-Lernen", "2opt_b5", 49.9, 80.0, 12.5, 41.7)
    assert art == "info" and "bevorzugt" in text and "49,9 %" in text
    assert "bevorzugt" in E.verdict_anteil("Q-Lernen", "2opt", 25.0, 20.0, 12.5, 12.5)[1]
    art, text = E.verdict_anteil("UCB", "insert", 24.9, 10.0, 12.5, 12.5)
    assert art == "info" and "fast gleichmäßig" in text and "24,9 %" in text and "`insert`" in text
    assert 100 * C.ANTEIL_FEST == 4 * 12.5 and 100 * C.ANTEIL_BEVORZUGT == 2 * 12.5      # 4- und 2-fache Gleichverteilung bei acht Zugarten


def test_verdict_zelle_drei_klassen():
    art, text = E.verdict_zelle("Choice Function", "Standard", "Rekord-zu-Rekord", "klein (50·n)", 1.15, 0.79, 1.51, 120, 3)
    assert art == "success" and "1,15 Prozentpunkte vor Zufall [+0,79; +1,51]" in text and "120 Instanzen × 3 Läufe" in text and "Auswertungen" in text
    art, text = E.verdict_zelle("Choice Function", "Standard", "Late Acceptance", "klein (50·n)", -1.57, -1.93, -1.23, 120, 3)
    assert art == "warning" and "1,57 Prozentpunkte hinter Zufall [−1,93; −1,23]" in text
    art, text = E.verdict_zelle("UCB", "Standard", "Late Acceptance", "groß (200·n)", 0.05, -0.2, 0.3, 120, 3)
    assert art == "info" and "nicht zu unterscheiden" in text and "+0,05 [−0,20; +0,30]" in text


def test_verdict_vergleich_mini_reihe():
    art, text = E.verdict_vergleich("Lernautomat", "Late Acceptance", "klein (50·n)", -1.4, -2.2, -0.6, 24, 2)
    assert art == "warning" and "24 Instanzen × 2 Läufe" in text and "1,40 Prozentpunkte hinter Zufall [−2,20; −0,60]" in text
    art, text = E.verdict_vergleich("Choice Function", "Rekord-zu-Rekord", "klein (50·n)", 1.2, 0.2, 2.2, 24, 2)
    assert art == "success" and "1,20 Prozentpunkte vor Zufall" in text
    art, text = E.verdict_vergleich("UCB", "Late Acceptance", "groß (200·n)", 0.3, -0.5, 1.1, 24, 2)
    assert art == "info" and "nicht von Zufall zu unterscheiden" in text and "unter etwa 0,80 Prozentpunkten" in text and "Marke 0,25" in text
    art, text = E.verdict_vergleich("UCB", "Late Acceptance", "groß (200·n)", 5.0, 1.0, 9.0, 3, 1)
    assert art == "info" and "kein Urteil" in text                       # unter vier Instanzen meldet auch ein großer Unterschied nichts


def test_verdict_gutschrift_schwellen_und_nenner_null():
    assert E.verdict_gutschrift("la", None, None)[0] == "info" and "keine einzige Verbesserung" in E.verdict_gutschrift("la", None, None)[1]
    art, text = E.verdict_gutschrift("ob", 0.0, 1.0)
    assert art == "info" and "Kontrolle" in text and "0,0 %" in text and "W = 1,00" in text
    art, text = E.verdict_gutschrift("la", 0.5, 3.0)
    assert art == "warning" and "Mehr als die Hälfte" in text and "50,0 %" in text and "3,00-Fache" in text
    assert E.verdict_gutschrift("la", 0.499, 3.0)[0] == "info" and "Ein Teil" in E.verdict_gutschrift("rr", 0.10, 1.2)[1]
    art, text = E.verdict_gutschrift("rr", 0.099, 1.05)
    assert art == "success" and "Kaum" in text and "9,9 %" in text


def _zeile(a, b, klassen=("schlechter", "gleich")):
    return dict(bed_a=a, bed_b=b, zufall_best=[dict(klasse=k) for k in klassen])


def test_urteil_kredit_und_verdict_kredit():
    assert E.urteil_kredit([_zeile(True, True), _zeile(True, True), _zeile(False, True)]) == "gestützt"
    assert E.urteil_kredit([_zeile(True, True), _zeile(True, False), _zeile(False, True)]) == "teilweise"
    assert E.urteil_kredit([_zeile(True, False), _zeile(False, True), _zeile(False, False)]) == "nicht gestützt"
    art, text = E.verdict_kredit([_zeile(True, True), _zeile(True, True), _zeile(False, True)], "nicht getrennt", 0.31, -0.02, 0.64)
    assert art == "success" and "2 von 3 Regeln" in text and "20 Prozentpunkte: 2 von 3" in text and "0,5 Punkte" in text and "mit Intervall über 0: 3 von 3" in text
    assert "in 3 von 6 Zellen" in text and "in 0 ein Vorsprung" in text and "nicht getrennt" in text and "+0,31 [−0,02; +0,64]" in text
    art, text = E.verdict_kredit([_zeile(True, False), _zeile(False, False), _zeile(False, False)], "weniger lernen", 0.1, -0.2, 0.4)
    assert art == "info" and "0 von 3 Regeln" in text and "weniger lernen" in text
    assert E.verdict_kredit([_zeile(True, True), _zeile(False, False), _zeile(False, False)], "gutschrift", 0.5, 0.2, 0.8)[1].startswith("Die Gutschrift ist nur teilweise")


@pytest.mark.parametrize("d,lo,anteil,ziel,erwartet", [
    (0.30, 0.01, 21.0, 22.0, "gutschrift"), (0.30, 0.0, 21.0, 22.0, "nicht getrennt"), (0.29, 0.1, 21.0, 22.0, "weniger lernen"),
    (-0.5, -0.9, 21.0, 22.0, "weniger lernen"), (0.9, 0.5, 19.9, 22.0, "nicht vergleichbar"), (0.9, 0.5, 20.0, 22.0, "gutschrift"),
])
def test_urteil_verduennung(d, lo, anteil, ziel, erwartet):
    assert E.urteil_verduennung(d, lo, anteil, ziel) == erwartet


def test_verdict_einstellung_und_ohne_b5():
    art, text = E.verdict_einstellung("Late Acceptance", "groß (200·n)", 20, 0, 14, "UCB mit c = 1,0", 0.08, -0.1, 0.26)
    assert art == "warning" and "0 von 20 Varianten" in text and "14 dahinter" in text and "UCB mit c = 1,0 mit +0,08 [−0,10; +0,26]" in text and "optimistisch" in text
    assert E.verdict_einstellung("Rekord-zu-Rekord", "klein (50·n)", 20, 9, 1, "x", 1.0, 0.5, 1.5)[0] == "info"
    art, text = E.verdict_ohne_b5("Late Acceptance", "klein (50·n)", [("Choice Function", 0.3, -0.1, 0.7, "gleich"), ("Lernautomat", 1.08, 0.74, 1.4, "besser"),
                                                                     ("Q-Lernen", -0.4, -0.7, -0.1, "schlechter")])
    assert art == "info" and "Lernautomat +1,08 [+0,74; +1,40]" in text and "1 von 3 Regeln vor und 1 hinter Zufall" in text


def test_mini_kosten_und_grenze():
    assert E.mini_kosten(24, 2, 30, 50) == 2 * 24 * 2 * 1500 == 144_000
    assert E.mini_erlaubt(24, 2, 30, 50) and E.mini_erlaubt(25, 1, 60, 200) and not E.mini_erlaubt(26, 1, 60, 200)   # 600 000 ist erlaubt
    assert not E.mini_erlaubt(C.MINI_INSTANZEN_MAX, C.MINI_LAEUFE_MAX, 60, 200)
    assert E.mini_indices(198, 4) == [198, 199, 0, 1]
