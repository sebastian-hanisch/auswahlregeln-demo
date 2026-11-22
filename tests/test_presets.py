"""Presets: vollständig, in den Reglergrenzen, mit Hilfetext; je Preset die erwartete Verdikt-Zeile der eingefrorenen Zelle (DEMO-PLAYBOOK §11a Punkt 7)."""

import pytest

import asw_constants as C
import asw_evaluation as E
import asw_frozen as F
import asw_presets as P
import asw_saetze as SZ  # noqa: F401  (füllt C.PRESET_HELP)


def test_presets_legen_jeden_regler_fest_und_haben_einen_hilfetext():
    assert set(C.PRESETS) == set(C.PRESET_HELP) and len(C.PRESETS) == 7
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    assert len({tuple(sorted(p.items())) for p in C.PRESETS.values()}) == 7      # keine zwei Presets mit derselben Einstellung


def test_presetwerte_liegen_in_den_reglergrenzen_und_passen_zur_regel():
    for name, preset in C.PRESETS.items():
        for key, wert in preset.items():
            spec = P.SETTING_SPECS[P.PRESET_KEYS[key]]
            assert P.clamp(spec, wert) == wert, (name, key)
        assert preset["belohnung"] in C.BELOHNUNGEN_JE_REGEL[preset["regel"]], name
        assert preset["einstellung"] == "standard" or preset["regel"] in C.PARAMETER
        assert E.mini_erlaubt(preset["mini_instanzen"], preset["mini_laeufe"], preset["n"], preset["budget"]), name   # die Mini-Reihe des Presets ist rechenbar


def test_erstes_preset_ist_die_voreinstellung():
    erstes = next(iter(C.PRESETS.values()))
    assert all(erstes[key] == P.SETTING_SPECS[state].default for key, state in P.PRESET_KEYS.items())
    assert erstes["akz"] == "rr"                                           # Standard-Akzeptanz der Demo: Rekord-zu-Rekord


def test_belohnung_gueltig_faellt_auf_den_standard_zurueck():
    assert P.belohnung_gueltig("laut", "rank") == "r2" and P.belohnung_gueltig("laut", "best") == "best"
    assert P.belohnung_gueltig("rand", "best") == "r2" and P.belohnung_gueltig("cf", "ma") == "ma"


# Erwartete Klasse der eingefrorenen Zelle je Preset (Regel mit ihrer Belohnung gegen Zufall, auf der Zugmenge des Presets)
ERWARTET = {
    "Rekord-zu-Rekord, kleines Budget": "besser",
    "Late Acceptance: hier verliert Lernen": "schlechter",
    "Nur Verbesserungen des Bestwerts belohnen": "gleich",
    "Großes Budget, „nur besser“": "gleich",
    "Der Lernautomat legt sich fest": "schlechter",
    "UCB wählt fast wie Zufall": "gleich",
    "Ohne die Zugart 2opt_b5": "gleich",
}


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_verdikt_zeile_je_preset(name):
    p = C.PRESETS[name]
    j = C.STUFEN.index(p["budget"])
    x = F.diff(p["akz"], F.key(p["regel"], p["belohnung"]), j, p["menge"])
    art, text = E.verdict_zelle(C.REGEL_ANZEIGE[p["regel"]], C.BELOHNUNG_KURZ[p["belohnung"]], C.AKZ_KURZ[p["akz"]], C.STUFEN_ANZEIGE[p["budget"]],
                                x["d"], x["lo"], x["hi"], 120, 3)
    assert art == {"besser": "success", "schlechter": "warning", "gleich": "info"}[x["klasse"]]
    assert E.de(abs(x["d"])) in text
    if ERWARTET[name] is not None:
        assert x["klasse"] == ERWARTET[name], (name, x)
    if name == "Großes Budget, „nur besser“":
        assert art != "success"                                          # ein Preset ohne Vorteil meldet keinen Vorteil
    assert SZ.preset_erwartung(name) in C.PRESET_HELP[name]
