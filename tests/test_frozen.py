"""Die eingefrorene Messung: Aufbau der Datei und Neurechnung eines Ausschnitts als Band (nicht bytegleich: Linux rechnet im letzten Bit anders)."""

import importlib.util
import json
from pathlib import Path

import pytest

import asw_constants as C
import asw_frozen as F

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "asw_frozen.json").read_text(encoding="utf-8"))


def _werkzeug():
    spec = importlib.util.spec_from_file_location("asw_make_frozen", ROOT / "tools" / "asw_make_frozen.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_aufbau_der_datei():
    m = D["meta"]
    assert m["instanzen"] == 120 == len(D["instanzen"]) == len(D["ref"]) and m["laeufe"] == 3 and m["stufen"] == [50, 200]
    assert D["instanzen"] == [[f, n, i] for f in C.FAMILIEN for n in C.N_GEMESSEN for i in range(20)]
    assert set(D["gap"]) == {"voll", "ohne_2opt_b5", "empf", "verd"} and set(D["gap"]["voll"]) == set(C.AKZEPTANZEN)
    for akz in C.AKZEPTANZEN:
        assert set(D["gap"]["voll"][akz]) == {"rand/r2"} | {f"{r}/{b}" for r, b in C.PAARE}
        assert set(D["gap"]["ohne_2opt_b5"][akz]) == {f"{r}/r2" for r in C.REGELN}
    for akz in C.EMPF_AKZEPTANZEN:
        assert set(D["gap"]["empf"][akz]) == {f"{r}/{e}/{b}" for r, e, b in C.EMPF_VARIANTEN}
    assert set(D["gap"]["verd"]) == {"la"} and set(D["gap"]["verd"]["la"]) == {"cfv/r2"}
    for block in D["gap"].values():
        for zellen in block.values():
            for zeilen in zellen.values():
                assert len(zeilen) == 120 and all(len(z) == 2 and z[0] >= z[1] >= 0 for z in zeilen)   # Abstand fällt mit dem Budget, nie unter der Referenz


def test_zaehler_summieren_sich_zum_budget():
    """Je Variante: Summe der Auswertungen über alle Läufe = 3 Läufe x Summe der Budgets der 120 Instanzen (am Kontrollpunkt bis zu 4 mehr je Lauf)."""
    soll_hi = 3 * sum(200 * n for _, n, _ in D["instanzen"])
    soll_lo = 3 * sum(50 * n for _, n, _ in D["instanzen"])
    for block in D["zaehler"].values():
        for zellen in block.values():
            for z in zellen.values():
                assert sum(z["evals"][1]) == soll_hi
                assert soll_lo <= sum(z["evals"][0]) <= soll_lo + 4 * 360
                assert all(a <= e <= 5 * a for a, e in zip(z["apps"][1], z["evals"][1]))
    assert sum(D["zaehler"]["ohne_2opt_b5"]["la"]["cf/r2"]["apps"][1][7:]) == 0
    assert soll_hi == 3 * 60 * 200 * (30 + 60) == 3_240_000


def test_gesamtzahl_der_auswertungen():
    varianten = 3 * (19 + 6) + 2 * 20 + 1
    assert varianten == 116
    assert D["meta"]["auswertungen_gesamt"] == varianten * 3_240_000 == 375_840_000


def test_referenz_ist_das_minimum_und_die_verduennung_stammt_aus_dem_raster():
    refs = json.loads((ROOT / "asw_refs.json").read_text(encoding="utf-8"))["refs"]
    for (f, n, i), r in zip(D["instanzen"], D["ref"]):
        assert r <= refs[f][str(n)][i] + 1e-6
    assert 0 <= D["unterboten"] <= 120
    v = D["verd"]
    assert v["p"] in C.VERD_RASTER and [p for p, _ in v["raster"]] == list(C.VERD_RASTER)
    assert v["p"] == min(v["raster"], key=lambda z: (abs(z[1] - v["ziel"]), z[0]))[0]
    anteile = [a for _, a in v["raster"]]
    assert anteile[0] > anteile[-1]                                       # mehr Verdünnung, weniger Anwendungen auf 2opt_b5
    assert v["training"] == [1000, 1004]


def test_ausschnitt_neu_gerechnet_stimmt_als_band():
    """Drei Instanzen x acht Varianten (alle Blöcke, alle Akzeptanzregeln): Abstände auf 0,002 Prozentpunkte."""
    w = _werkzeug()
    assert len(w.CHECK_INSTANZEN) * len(w.CHECK_VARIANTEN) == 24
    assert w.check(D) == []


def test_standardlaeufe_sind_dieselben_wie_in_der_zugmengen_demo_falls_vorhanden():
    """Gleiche Instanzen, Starttouren, Ströme und Regeln wie zugmenge-demo (dort 50·n als Kontrollpunkt eines Laufs bis 400·n): die mittleren
    Abstände bei 50·n liegen dicht beieinander (andere Referenz: Minimum über andere Läufe), die Unterschiede zu Zufall ebenso."""
    pfad = ROOT.parent / "zugmenge-demo" / "zgm_band.json"
    if not pfad.exists():
        pytest.skip("Nachbarordner nicht vorhanden (CI)")
    z = json.loads(pfad.read_text(encoding="utf-8"))
    assert z["instanzen"] == D["instanzen"]
    for akz in C.AKZEPTANZEN:
        for regel in ("cf", "laut", "q"):
            dort = sum(a[0] - b[0] for a, b in zip(z["gap"][akz]["voll"]["rand"], z["gap"][akz]["voll"][regel])) / 120
            assert F.diff(akz, F.key(regel), 0)["d"] == pytest.approx(dort, abs=0.02), (akz, regel)
