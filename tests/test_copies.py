"""Kopier-Tests: die Rundtour-Module sind wörtliche Kopien aus der Wurzel-Demo der Linie (hyperheuristik-demo), die vier Auswahlregeln und die
Referenzwerte aus zugmenge-demo, die Zufallsvorlage aus dem Website-Repo; jeweils bis auf das Präfix.

Fehlt der Nachbarordner (CI), werden die Tests übersprungen. Eine Korrektur gehört in die Quelle und wird neu kopiert, nicht in die Kopie."""

from pathlib import Path

import pytest

import asw_constants as C

ROOT = Path(__file__).resolve().parent.parent
QUELLE = ROOT.parent / "hyperheuristik-demo"
QUELLE_REGELN = ROOT.parent / "zugmenge-demo"
VORLAGE = ROOT.parent / "sebastianhanisch-website" / "tools" / "templates" / "rng_splitmix64_exact.py"
KOPIEN = ("rng", "rngblock", "scenario", "moves", "accept", "search", "stats")
GLEICHE_KONSTANTEN = (
    "HNAMEN", "K", "KOSTEN", "H_2OPT", "H_2OPT_B5", "ALLE_ZUGARTEN", "B5_STICHPROBEN", "LOKAL_LMAX", "FAMILIEN", "FAMILIE_HAND", "SEITE",
    "CLUSTER_ZAHL", "CLUSTER_SIGMA", "GITTER_FAKTOR", "GITTER_RAUSCHEN", "ZWECK_INSTANZ", "ZWECK_START", "ZWECK_LAUF", "ZWECK_BOOT", "EPS",
    "RHO", "LA_LEN", "LA_LEN_KURZ", "GD_END", "SA_T0", "SA_T1", "MARKE_KLAR", "MARKE_GLEICH", "BOOTSTRAP_ZIEHUNGEN",
)
REGEL_KONSTANTEN = ("EPS", "CF_ALPHA", "CF_PHI0", "CF_PHI_ERFOLG", "CF_PHI_SCHRITT", "CF_PHI_MIN", "CF_ZEITFENSTER", "CF_RAUSCHEN", "LAUT_A",
                    "LAUT_BODEN", "Q_EPS", "Q_ALPHA", "Q_GAMMA")


def _text(pfad: Path) -> str:
    return pfad.read_text(encoding="utf-8").replace("\r\n", "\n")


def _konstanten(pfad: Path) -> dict:
    namen: dict = {}
    exec(compile(_text(pfad), str(pfad), "exec"), namen)   # nur Zuweisungen von Konstanten
    return namen


@pytest.mark.parametrize("suffix", KOPIEN)
def test_kopie_stimmt_mit_der_quelle_ueberein_falls_vorhanden(suffix):
    quelle = QUELLE / f"hhw_{suffix}.py"
    if not quelle.exists():
        pytest.skip("Quelle nicht vorhanden (CI ohne den Nachbarordner)")
    assert _text(ROOT / f"asw_{suffix}.py") == _text(quelle).replace("hhw_", "asw_")


def test_zufallsvorlage_ist_bytegleich_falls_vorhanden():
    if not VORLAGE.exists():
        pytest.skip("Vorlage nicht vorhanden (CI ohne das Website-Repo)")
    assert _text(ROOT / "asw_rng.py") == _text(VORLAGE)


def test_auswahlregeln_sind_die_kopie_aus_der_zugmengen_demo_falls_vorhanden():
    quelle = QUELLE_REGELN / "zgm_select.py"
    if not quelle.exists():
        pytest.skip("Quelle nicht vorhanden (CI ohne den Nachbarordner)")
    assert _text(ROOT / "asw_select.py") == _text(quelle).replace("zgm_", "asw_")


def test_referenzwerte_sind_die_der_zugmengen_demo_falls_vorhanden():
    quelle = QUELLE_REGELN / "zgm_refs.json"
    if not quelle.exists():
        pytest.skip("Quelle nicht vorhanden (CI ohne den Nachbarordner)")
    assert _text(ROOT / "asw_refs.json") == _text(quelle)


def test_konstanten_der_kopien_haben_die_werte_der_quelle_falls_vorhanden():
    quelle = QUELLE / "hhw_constants.py"
    if not quelle.exists():
        pytest.skip("Quelle nicht vorhanden (CI ohne den Nachbarordner)")
    namen = _konstanten(quelle)
    for name in GLEICHE_KONSTANTEN:
        assert getattr(C, name) == namen[name], name


def test_parameter_der_kopierten_regeln_haben_die_werte_der_quelle_falls_vorhanden():
    quelle = QUELLE_REGELN / "zgm_constants.py"
    if not quelle.exists():
        pytest.skip("Quelle nicht vorhanden (CI ohne den Nachbarordner)")
    namen = _konstanten(quelle)
    for name in REGEL_KONSTANTEN:
        assert getattr(C, name) == namen[name], name
    assert C.MENGEN["ohne_2opt_b5"] == namen["MENGEN"]["ohne_2opt_b5"] and C.MENGEN["voll"] == namen["MENGEN"]["voll"]


def test_paare_und_varianten_der_messung():
    assert len(C.PAARE) == 18 and len(set(C.PAARE)) == 18                # 3 Regeln x 5 Formen + Lernautomat x 2 + Zufallsgradient
    assert len(C.EMPF_VARIANTEN) == 20 and len(set(C.EMPF_VARIANTEN)) == 20   # 3 Regeln x 2 Werte x 3 Formen + Lernautomat x 2 Werte
    assert all(b in C.BELOHNUNGEN_JE_REGEL[r] for r, b in C.PAARE)
    assert 3 * 18 == 54 and 3 * 5 == 15                                  # Zellen je Budget: alle Paare bzw. nur Standardbelohnung
    assert set(C.PARAMETER) == set(C.LERNREGELN)
