"""Aussagen der README: jede Zahlengruppe wird unabhängig aus asw_frozen.json nachgerechnet (eigene Arithmetik hier im Test, nicht über
asw_frozen), dazu der Wortlaut: der Messblock der README ist der von tools/asw_readme.py erzeugte, die Annahmen sind die der App.

Mittelwerte und Zählungen sind exakt aus der Datei; Bootstrap-Intervalle werden mit einem eigenen Zufallsgenerator neu gezogen und als Band
verglichen (±0,03 Punkte)."""

import importlib.util
import json
import random
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

import asw_constants as C
import asw_frozen as F
import asw_saetze as SZ
import asw_texts as T

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
D = json.loads((ROOT / "asw_frozen.json").read_text(encoding="utf-8"))
DREI = ("cf", "laut", "q")


def _d(akz, key, j, block="voll", basis=None):
    """Mittlerer gepaarter Unterschied Zufall minus Regel, direkt aus der Datei."""
    a = D["gap"]["voll" if block in ("empf", "verd") else block][akz]["rand/r2"] if basis is None else basis
    b = D["gap"][block][akz][key]
    return [x[j] - y[j] for x, y in zip(a, b)]


def _mittel(x):
    return sum(x) / len(x)


def _ci(werte, seed=1, ziehungen=3000):
    z = random.Random(seed)
    m = len(werte)
    mittel = sorted(sum(werte[z.randrange(m)] for _ in range(m)) / m for _ in range(ziehungen))
    return mittel[int(0.025 * ziehungen)], mittel[int(0.975 * ziehungen)]


def _klasse(werte):
    d = _mittel(werte)
    lo, hi = _ci(werte)
    return "besser" if d >= 0.25 and lo > 0 else ("schlechter" if d <= -0.10 and hi < 0 else "gleich")


def _anteil(block, akz, key, h=7, feld="apps"):
    z = D["zaehler"][block][akz][key][feld][1]
    return 100.0 * z[h] / sum(z)


def _de(x, stellen=2):
    return f"{x:+.{stellen}f}".replace(".", ",").replace("-", "−")


def test_readme_block_ist_aus_der_messung_geschrieben():
    spec = importlib.util.spec_from_file_location("asw_readme", ROOT / "tools" / "asw_readme.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    assert modul.einsetzen(README) == README
    for satz in (SZ.satz_wirkung(), SZ.satz_anteile(), SZ.satz_gutschrift(), SZ.satz_kredit(), SZ.satz_verduennung(), SZ.satz_empfindlichkeit()):
        assert satz in README
    assert T.ASSUMPTIONS_MARKDOWN.strip() in README


def test_groesse_der_messung():
    assert D["meta"]["auswertungen_gesamt"] == 375_840_000 and "375 840 000 Auswertungen" in README
    assert D["meta"]["instanzen"] == 120 and D["meta"]["laeufe"] == 3 and D["unterboten"] == 30 and "in 30 von 120 Instanzen" in README
    assert 3 * (1 + 18 + 6) + 2 * 20 + 1 == 116 and "116 Varianten" in README
    assert "4000 Ziehungen" in README and C.BOOTSTRAP_ZIEHUNGEN == 4000


def test_gleichverteilung():
    assert Fraction(1, 8) == Fraction(125, 1000) and round(100 * Fraction(5, 12), 1) == Fraction(417, 10)
    assert F.gleichverteilung() == (12.5, pytest.approx(100 * 5 / 12))
    assert F.gleichverteilung(7, False) == (pytest.approx(100 / 7), pytest.approx(100 / 7))
    assert "12,5 % und 41,7 %" in README


def test_kernzahlen_standardbelohnung_kleines_budget():
    """Rekord-zu-Rekord +1,14 / +0,84 / +0,88; Late Acceptance −1,57 / −1,18 / −1,36; alle sechs mit Klasse; Q-Lernen unter „nur besser“ +0,50."""
    rr = [_d("rr", f"{r}/r2", 0) for r in DREI]
    la = [_d("la", f"{r}/r2", 0) for r in DREI]
    assert " / ".join(_de(_mittel(x)) for x in rr) == "+1,14 / +0,84 / +0,88" and "+1,14 / +0,84 / +0,88" in README
    assert " / ".join(_de(_mittel(x)) for x in la) == "−1,57 / −1,18 / −1,36" and "−1,57 / −1,18 / −1,36" in README
    assert [_klasse(x) for x in rr] == ["besser"] * 3 and [_klasse(x) for x in la] == ["schlechter"] * 3
    q = _d("ob", "q/r2", 0)
    lo, hi = _ci(q)
    assert _de(_mittel(q)) == "+0,50" and lo == pytest.approx(0.13, abs=0.03) and hi == pytest.approx(0.87, abs=0.03) and "(+0,50 [+0,13; +0,87])" in README
    assert [_klasse(_d("ob", f"{r}/r2", 0)) for r in ("rg", "cf", "ucb", "laut", "q")] == ["gleich"] * 4 + ["besser"]


def test_zaehlungen_ueber_die_zellen():
    """15 Zellen mit Standardbelohnung und 54 Zellen über alle 18 Paare, je Budget; je Akzeptanzregel."""
    def zaehle(paare, j, akzn=C.AKZEPTANZEN):
        k = [_klasse(_d(akz, f"{r}/{b}", j)) for akz in akzn for r, b in paare]
        return k.count("besser"), k.count("schlechter"), len(k)
    assert zaehle(C.PAARE_STANDARD, 0) == (5, 3, 15) and zaehle(C.PAARE_STANDARD, 1) == (0, 4, 15)
    assert zaehle(C.PAARE, 0) == (21, 14, 54) and zaehle(C.PAARE, 1) == (4, 13, 54)
    assert [zaehle(C.PAARE, 0, (a,))[:2] for a in C.AKZEPTANZEN] == [(5, 0), (16, 0), (0, 14)]
    assert [zaehle(C.PAARE, 1, (a,))[:2] for a in C.AKZEPTANZEN] == [(0, 2), (4, 0), (0, 11)]
    assert "keine der 15 Zellen" in README and "4 liegen hinter Zufall" in README
    assert "21 von 54 Zellen vor und 14 hinter Zufall, bei großem 4 vor und 13 dahinter" in README
    assert "Rekord-zu-Rekord 16 vor und 0 hinter Zufall bei kleinem, 4 und 0 bei großem Budget" in README
    assert "Late Acceptance 0 vor und 14 hinter Zufall bei kleinem, 0 und 11 bei großem Budget" in README
    assert "„nur besser“ 5 vor und 0 hinter Zufall bei kleinem, 0 und 2 bei großem Budget" in README
    # die vier Zellen bei großem Budget liegen alle unter Rekord-zu-Rekord und keine hat die Standardbelohnung
    vier = [(r, b) for r, b in C.PAARE if _klasse(_d("rr", f"{r}/{b}", 1)) == "besser"]
    assert len(vier) == 4 and all(b != "r2" for _, b in vier)
    assert all(_klasse(_d(akz, "rg/r2", j)) == "gleich" for akz in C.AKZEPTANZEN for j in (0, 1))        # Zufallsgradient: sechs Zellen
    groesster = max((_mittel(_d(akz, f"{r}/{b}", 1)), r, b, akz) for akz in C.AKZEPTANZEN for r, b in C.PAARE)
    assert _de(groesster[0]) == "+0,29" and groesster[1:] == ("cf", "r1", "rr") and "+0,29 [+0,02; +0,57]" in README


def test_anteile_auf_2opt_b5():
    erwartet = {("la", "cf"): ("59,9", "88,2"), ("la", "laut"): ("72,7", "93,0"), ("la", "q"): ("32,6", "70,8"),
                ("rr", "cf"): ("49,3", "82,9"), ("rr", "laut"): ("68,1", "91,4"), ("rr", "q"): ("32,9", "71,1")}
    for (akz, r), (a, w) in erwartet.items():
        assert f"{_anteil('voll', akz, r + '/r2'):.1f}".replace(".", ",") == a and f"{_anteil('voll', akz, r + '/r2', feld='evals'):.1f}".replace(".", ",") == w
        assert f"{a} % der Anwendungen ({w} % der Auswertungen)" in README
    assert [round(_anteil("voll", "ob", r + "/r2"), 1) for r in DREI] == [17.8, 40.5, 16.1] and "17,8 %, 40,5 % und 16,1 %" in README
    ucb = [round(_anteil("voll", akz, "ucb/r2"), 1) for akz in C.AKZEPTANZEN]
    assert (min(ucb), max(ucb)) == (12.7, 12.9) and "12,7 bis 12,9 %" in README
    assert _anteil("voll", "rr", "cf/r2") >= 49 and _anteil("voll", "rr", "laut/r2") >= 49      # „rund die Hälfte und mehr“
    # Auswertungsanteil folgt aus dem Anwendungsanteil a: 5a / (5a + 1 - a), bis auf die Kürzung der letzten Anwendung (unter 0,3 Punkte)
    for akz in C.AKZEPTANZEN:
        for r in C.REGELN:
            a = _anteil("voll", akz, r + "/r2") / 100
            assert 100 * 5 * a / (5 * a + 1 - a) == pytest.approx(_anteil("voll", akz, r + "/r2", feld="evals"), abs=0.3)


def test_gutschrift_ohne_neuen_bestwert():
    def g(akz, key):
        k = D["konto"]["voll"][akz][key]
        return round(100 * _mittel([z[1] for z in k["ohne"]]), 1), round(_mittel([z[1] for z in k["w"]]), 2)
    assert g("la", "rand/r2") == (46.7, 2.97) and g("la", "cf/r2") == (71.6, 8.36) and g("la", "laut/r2") == (67.6, 7.11)
    assert g("la", "q/r2") == (67.5, 6.77) and g("la", "ucb/r2") == (51.5, 3.39) and g("rr", "rand/r2") == (39.1, 2.80) and g("rr", "cf/r2") == (44.4, 3.29)
    for text in ("46,7 % (W = 2,97)", "71,6 % (W = 8,36)", "67,6 % (W = 7,11)", "67,5 % (W = 6,77)", "51,5 % (W = 3,39)", "39,1 % (W = 2,80)", "44,4 % (W = 3,29)"):
        assert text in README
    for key in D["konto"]["voll"]["ob"]:                                 # Kontrolle „nur besser“: 0 % und W = 1 in jeder Instanz
        k = D["konto"]["voll"]["ob"][key]
        assert all(z == [0.0, 0.0] for z in k["ohne"]) and all(z == [1.0, 1.0] for z in k["w"])
    k = D["konto"]["voll"]["la"]["cf/r2"]
    assert round(100 * k["gut_r2"][7] / sum(k["gut_r2"]), 1) == 73.5 and round(100 * k["gut_best"][7] / sum(k["gut_best"]), 1) == 51.6
    assert "73,5 % der Standard-Gutschrift und 51,6 %" in README and g("rr", "cf/r2")[0] > 40
    assert "bei der Choice Function bei 44,4 % (Zufall 39,1 %; unter Late Acceptance 71,6 % gegen 46,7 %)" in README


def test_ucb_unter_rekord_zu_rekord_und_vorab_regel_im_messblock():
    """Der Messblock nennt UCB unter Rekord-zu-Rekord (kleines Budget, Standardbelohnung) und sagt, wie viele Regeln die Vorab-Regel erfüllen."""
    zahlen = {r: _mittel(_d("rr", r + "/r2", 0)) for r in ("rg", "cf", "ucb", "laut", "q")}
    klassen = {r: _klasse(_d("rr", r + "/r2", 0)) for r in zahlen}
    assert _de(zahlen["ucb"]) == "+0,51" and klassen["ucb"] == "besser" and klassen["rg"] == "gleich"
    assert sum(k == "besser" for k in klassen.values()) == 4
    assert "auch UCB vor Zufall (+0,51 [" in README and "erreichen dort also 4 die Marke" in README
    assert "erfüllen 2 von 3 Regeln (Choice Function, Lernautomat); es fehlt: Q-Lernen (Senkung 12,6 statt mindestens 20 Punkte)" in README


def test_kreditregel():
    """Late Acceptance: Senkung des Anteils und Güte (Abstand Standard minus Abstand „nur Bestwert“) je Regel; 2 von 3 erfüllen beides."""
    erfuellt = []
    soll = {"cf": ("59,9", "21,5", "38,4", "+0,67", "+1,44"), "laut": ("72,7", "39,7", "33,0", "+0,93", "+1,20"), "q": ("32,6", "20,0", "12,6", "+0,81", "+0,71")}
    for r in DREI:
        a2, ab = _anteil("voll", "la", r + "/r2"), _anteil("voll", "la", r + "/best")
        guete = [[x[j] - y[j] for x, y in zip(D["gap"]["voll"]["la"][r + "/r2"], D["gap"]["voll"]["la"][r + "/best"])] for j in (0, 1)]
        assert (f"{a2:.1f}", f"{ab:.1f}", f"{a2 - ab:.1f}") == tuple(s.replace(",", ".") for s in soll[r][:3])
        assert (_de(_mittel(guete[0])), _de(_mittel(guete[1]))) == soll[r][3:]
        assert f"Anteil {soll[r][0]} → {soll[r][1]} % (Senkung {soll[r][2]} Punkte), Güte {soll[r][3]} [" in README
        erfuellt.append(a2 - ab >= 20 and all(_mittel(g) >= 0.5 and _ci(g)[0] > 0 for g in guete))
    assert erfuellt == [True, True, False]
    # gegen Zufall mit „nur Bestwert“: 3 von 6 Zellen dahinter, keine davor
    k = [_klasse(_d("la", r + "/best", j)) for r in DREI for j in (0, 1)]
    assert k.count("schlechter") == 3 and k.count("besser") == 0
    assert [_de(_mittel(_d("la", "cf/best", j))) for j in (0, 1)] == ["−0,90", "−0,08"] and "gegen Zufall dann −0,90 und −0,08" in README
    # Gegenprobe Rekord-zu-Rekord: Anteil sinkt, Güte in keiner der sechs Zellen mit Intervall ohne 0
    assert round(_anteil("voll", "rr", "cf/r2"), 1) == 49.3 and round(_anteil("voll", "rr", "cf/best"), 1) == 21.2 and "49,3 → 21,2 %" in README
    for r in DREI:
        for j in (0, 1):
            lo, hi = _ci([x[j] - y[j] for x, y in zip(D["gap"]["voll"]["rr"][r + "/r2"], D["gap"]["voll"]["rr"][r + "/best"])])
            assert lo < 0 < hi, (r, j)
    for r in DREI:                                                       # „nur besser“: beide Belohnungen sind dieselbe
        assert D["gap"]["voll"]["ob"][r + "/r2"] == D["gap"]["voll"]["ob"][r + "/best"]


def test_verduennung():
    v = D["verd"]
    assert v["p"] == 0.6 and "in 60 % der Anwendungen würfelt" in README
    ziel, ist = _anteil("voll", "la", "cf/best"), _anteil("verd", "la", "cfv/r2")
    assert (round(ziel, 1), round(ist, 1)) == (21.5, 22.0) and abs(ist - ziel) <= C.VERD_BAND and ziel == pytest.approx(100 * v["ziel"], abs=1e-3)
    d = [[x[j] - y[j] for x, y in zip(D["gap"]["verd"]["la"]["cfv/r2"], D["gap"]["voll"]["la"]["cf/best"])] for j in (0, 1)]
    assert [_de(_mittel(x)) for x in d] == ["−0,36", "−0,08"] and "−0,36 [−0,67; −0,06] bei kleinem und −0,08 [−0,31; +0,14] bei großem Budget" in README
    assert _mittel(d[1]) < C.VERD_MARKE                                  # unter der Marke: „weniger lernen“
    lo, hi = _ci(d[1])
    assert lo == pytest.approx(-0.31, abs=0.03) and hi == pytest.approx(0.14, abs=0.03)
    z = [_d("la", "cfv/r2", j, "verd") for j in (0, 1)]
    assert [_de(_mittel(x)) for x in z] == ["−0,54", "+0,00"] and "−0,54 [−0,86; −0,23] (klein) und +0,00 [−0,27; +0,27] (groß)" in README


def test_empfindlichkeit():
    def zaehle(akz, j):
        k = [_klasse(_d(akz, f"{r}/{e}/{b}", j, "empf")) for r, e, b in C.EMPF_VARIANTEN]
        return k.count("besser"), k.count("schlechter")
    assert (zaehle("la", 0), zaehle("la", 1), zaehle("rr", 0), zaehle("rr", 1)) == ((1, 16), (0, 16), (18, 0), (2, 0))
    assert "1 von 20 Varianten vor und 16 hinter Zufall, bei großem 0 und 16" in README and "18 von 20 vor Zufall und 0 dahinter, bei großem 2 und 0" in README
    beste = max((_mittel(_d("la", f"{r}/{e}/{b}", 0, "empf")), r, e, b) for r, e, b in C.EMPF_VARIANTEN)
    assert _de(beste[0]) == "+0,37" and beste[1:] == ("ucb", "hoch", "r2") and "UCB mit c = 1,0, Belohnung „Standard“ mit +0,37 [+0,06; +0,70]" in README
    # Vorzeichen: positive Mittel je Akzeptanzregel und Budget (README: 2 bzw. 20 bei kleinem, 13 bzw. 3 bei großem Budget)
    def positiv(akz, j):
        return sum(_mittel(_d(akz, f"{r}/{e}/{b}", j, "empf")) > 0 for r, e, b in C.EMPF_VARIANTEN)
    assert (positiv("la", 0), positiv("rr", 0), positiv("rr", 1), positiv("la", 1)) == (2, 20, 13, 3)
    assert ("das Vorzeichen folgt bei kleinem Budget der Akzeptanzregel (2 bzw. 20 von 20 Varianten positiv unter Late Acceptance bzw. "
            "Rekord-zu-Rekord), bei großem Budget ist es unter Rekord-zu-Rekord gemischt (13 von 20 positiv; unter Late Acceptance 3)") in README


def test_zahl_der_zellen_mit_vorsprung_wechselt_mit_der_bootstrap_ziehung():
    """README: bei großem Budget liegen vier Zellen knapp an der Marke; bei anderen Bootstrap-Ziehungen sind es drei oder vier (nie mit Standardbelohnung)."""
    kandidaten = [(akz, f"{r}/{b}") for akz in C.AKZEPTANZEN for r, b in C.PAARE if _mittel(_d(akz, f"{r}/{b}", 1)) >= 0.25]
    assert len(kandidaten) == 4
    zahlen = set()
    for seed in range(1, 21):
        vorn = [(a, k) for a, k in kandidaten if _ci(_d(a, k, 1), seed=seed)[0] > 0]
        zahlen.add(len(vorn))
        assert all(not k.endswith("/r2") for _, k in vorn)
    assert zahlen == {3, 4}
    assert "bei anderen Bootstrap-Ziehungen drei oder vier" in README and "bei anderen Bootstrap-Ziehungen sind es drei oder vier" in SZ.satz_wirkung()


def test_intervalle_der_lesefunktionen_gegen_eigenes_bootstrap():
    """Die Intervalle im Text stammen aus asw_stats (numpy, SplitMix64); hier mit Python-random neu gezogen: Band 0,03 Punkte."""
    for akz, key, j in (("rr", "cf/r2", 0), ("la", "cf/r2", 0), ("la", "laut/best", 1), ("ob", "q/rank", 0), ("rr", "ucb/ma", 1)):
        x = F.diff(akz, key, j)
        d = _d(akz, key, j)
        lo, hi = _ci(d, seed=7, ziehungen=6000)
        assert x["d"] == pytest.approx(_mittel(d), abs=1e-12) and x["lo"] == pytest.approx(lo, abs=0.03) and x["hi"] == pytest.approx(hi, abs=0.03)


def test_abgleich_mit_der_zugmengen_demo_im_text():
    """Die README nennt die Zahlen von zugmenge-demo (+1,15 / +0,84 / +0,88 und −1,57 / −1,18 / −1,36) und „höchstens 0,02 Punkte“ Abweichung."""
    hier = [_mittel(_d(akz, r + "/r2", 0)) for akz in ("rr", "la") for r in DREI]
    dort = [1.15, 0.84, 0.88, -1.57, -1.18, -1.36]
    assert all(abs(a - b) <= 0.02 for a, b in zip(hier, dort))
    assert "+1,15 / +0,84 / +0,88" in README and "höchstens 0,02 Punkte" in README


def test_handbeispiel_zahlen_im_text():
    import asw_hand as H
    z = H.schritte("la")
    k = H.kennzahlen(z)
    assert (k["arbeit"], k["netto"], k["w"]) == (6, 2, 3) and H.OPTIMUM == 24
    assert k["konto"]["r2"]["C"] == pytest.approx(4 / 5) and k["konto"]["r2"]["A"] == pytest.approx(2 / 5) and k["konto"]["rbest"]["C"] == 0
    assert H.zustaende(z, "r2")["laut"]["p"][2] == pytest.approx(9199 / 24000)
    for text in ("Starttour der Länge 30 (Optimum 24)", "also W = 3", "9199/24000", "die Gutschrift 4/5", "W = 1"):
        assert text in README
    # Verlauf der Züge und Herkunft von 2/5 (Verkürzung 2, mittlere Kantenlänge 30 / 6 = 5), wie die README sie nennt
    assert [(x["zugart"], x["kosten"]) for x in z] == [("A", 28), ("B", 30), ("C", 28), ("B", 30), ("C", 28)]
    assert z[0]["r2"] == pytest.approx(2 / 5) and 30 / 6 == 5
    assert [x["angenommen"] for x in H.schritte("ob")] == [True, False, False, False, False]
    for text in ("A kürzt die Tour von 30 auf 28, B verlängert sie auf 30, C kürzt auf 28, B verlängert wieder auf 30, C kürzt auf 28", "mittlerer Kantenlänge 30 / 6 = 5",
                 "also 2/5, je Verkürzung um 2", "die vier Züge nach dem ersten abgelehnt"):
        assert text in README


def test_methodik_gegen_die_konstanten():
    assert (C.CF_ALPHA, C.UCB_C, C.UCB_GAMMA, C.LAUT_A, C.LAUT_BODEN, C.Q_ALPHA, C.Q_GAMMA, C.Q_EPS) == (0.9, 0.2, 0.995, 0.05, 0.01, 0.1, 0.5, 0.1)
    assert (C.RHO, C.LA_LEN, C.RANK_FENSTER, C.MARKE_KLAR, C.MARKE_GLEICH, C.KREDIT_SENKUNG, C.KREDIT_GUETE, C.VERD_MARKE) == (0.01, 50, 30, 0.25, 0.10, 20.0, 0.5, 0.3)
    assert (C.TRAIN_START, C.TRAIN_INSTANZEN, len(C.FAMILIEN) * len(C.N_GEMESSEN) * C.TRAIN_INSTANZEN) == (1000, 5, 30)
    assert (C.VERD_RASTER[0], C.VERD_RASTER[-1], C.MINI_INSTANZEN_MIN, C.MINI_INSTANZEN_MAX) == (0.05, 0.95, 6, 30)
    for text in ("α = 0,9", "c = 0,2, γ = 0,995", "a = 0,05, Boden 0,01", "α = 0,1, γ = 0,5, ε = 0,1", "Toleranz 1 %", "Liste der Länge 50", "letzten 30",
                 "ab +0,25 Punkte", "ab −0,10 Punkte", "mindestens 20 Prozentpunkte", "mindestens 0,5 Punkte", "mindestens 0,3 Punkte", "1000 bis 1004",
                 "Raster 0,05 bis 0,95", "6 bis 30 Instanzen", "1000·n Auswertungen"):
        assert text in README, text
    refs = json.loads((ROOT / "asw_refs.json").read_text(encoding="utf-8"))
    assert refs["meta"]["budget_faktor"] == 1000


def test_testzahl_der_readme_stimmt_mit_der_suite():
    m = re.search(r"^(\d+) Tests \(`pytest --collect-only", README, re.M)
    assert m, "Testzahl fehlt in der README"
    aus = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", str(ROOT / "tests")], capture_output=True, text=True,
                         cwd=str(ROOT), stdin=subprocess.DEVNULL, timeout=240).stdout
    gezaehlt = re.search(r"(\d+) tests? collected", aus)
    assert gezaehlt and int(gezaehlt.group(1)) == int(m.group(1))
