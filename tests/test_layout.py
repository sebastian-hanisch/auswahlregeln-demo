"""Layout (DEMO-PLAYBOOK §2): fester Kopf, Schnellstart oben in der Seitenleiste, aktives Beispiel hervorgehoben.

Die Hervorhebung ist zustandslos (`aktives_preset` vergleicht jeden Regler aus SETTING_SPECS mit dem Beispiel). Der Test unten stellt
sicher, dass wirklich JEDER Regler der Seitenleiste dort steht: sonst bliebe das Beispiel trotz Änderung markiert."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import asw_constants as C
import asw_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")
REGLER_ARTEN = ("slider", "number_input", "select_slider", "selectbox", "radio", "toggle", "checkbox", "text_input")


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _typen(at) -> dict:
    """Button-Typ je Beispiel-Name (die Schnellstart-Buttons der Seitenleiste)."""
    return {b.label: b.proto.type for b in at.sidebar.button if b.label in C.PRESETS}


def _regler(at, key):
    for art in REGLER_ARTEN:
        try:
            return getattr(at.sidebar, art)(key=key)
        except KeyError:
            continue
    raise AssertionError(f"Regler {key} steht nicht in der Seitenleiste")


def _anderer_wert(spec, wert):
    if spec.options is not None:
        return next(o for o in spec.options if o != wert)
    return spec.hi if wert != spec.hi else spec.lo


def test_presets_stehen_in_der_seitenleiste_und_nicht_im_hauptbereich():
    at = _app()
    assert [b.label for b in at.sidebar.button][: len(C.PRESETS)] == list(C.PRESETS)  # die ersten Buttons der Seitenleiste
    assert not [b for b in at.main.button if b.label in C.PRESETS]
    assert at.sidebar.button[-1].label == "🎲 Neue Instanz"                # der Zufalls-Button ist das letzte Element


def test_titel_steht_im_festen_kopf():
    at = _app()
    assert "st-key-kopf" in " ".join(h.proto.body for h in at.get("html"))  # das Stylesheet setzt an der Klasse des Containers an
    assert at.title[0].value == "🎰 Wer belohnt wen? Kreditzuweisung bei der Wahl der Zugart"
    for wort in ("Konfiguration", "Parameterwahl", "Verfahrenswahl", "Wahlregeln"):
        assert wort not in at.title[0].value


def test_beim_start_ist_genau_das_standard_preset_hervorgehoben():
    typen = _typen(_app())
    assert [name for name, typ in typen.items() if typ == "primary"] == [next(iter(C.PRESETS))]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_angeklicktes_preset_ist_hervorgehoben_und_bleibt_es_im_naechsten_lauf(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]
    at.run()
    assert [n for n, typ in _typen(at).items() if typ == "primary"] == [name]


def test_jeder_regler_der_seitenleiste_steht_in_setting_specs():
    at = _app()
    schluessel = {w.key for art in REGLER_ARTEN for w in getattr(at.sidebar, art) if w.key}
    assert schluessel == set(P.SETTING_SPECS)


def test_jeder_regler_der_app_hat_einen_schluessel_und_die_grenzen_aus_dem_presets_modul():
    at = _app()
    bekannt = set(P.SETTING_SPECS) | {"schritt_slider", "hand_form_radio"}
    for art in REGLER_ARTEN:
        for w in getattr(at, art):
            assert w.key in bekannt, (art, w.label)
    for key in ("mini_instanzen_slider", "mini_laeufe_slider"):
        regler = at.sidebar.slider(key=key)
        assert (regler.min, regler.max, regler.value) == (*P.bounds(key), P.SETTING_SPECS[key].default)
    for key in ("instanz_input", "lauf_input"):
        feld = at.sidebar.number_input(key=key)
        assert (feld.min, feld.max) == P.bounds(key)
    for key in ("familie_select", "n_select", "akz_select", "budget_select", "regel_select", "menge_select", "belohnung_select", "einstellung_select"):
        assert len(at.sidebar.selectbox(key=key).options) == len(P.options(key))     # Standardregel Choice Function: alle Formen, alle Einstellungen


@pytest.mark.parametrize("state_key", list(P.SETTING_SPECS))
def test_jede_aenderung_eines_reglers_hebt_die_hervorhebung_auf(state_key):
    at = _app()
    spec = P.SETTING_SPECS[state_key]
    regler = _regler(at, state_key)
    regler.set_value(_anderer_wert(spec, regler.value)).run()
    assert not at.exception
    name = next(iter(C.PRESETS))
    typen = _typen(at)
    assert typen[name] != "primary"                                  # das Standard-Beispiel ist nicht mehr markiert
    assert list(typen.values()).count("primary") <= 1                # höchstens ein anderes, das genau diese Einstellung ist (z. B. andere Akzeptanz)
    at.sidebar.button(key=f"preset_{name}").click().run()            # erneutes Anklicken markiert wieder
    assert _typen(at)[name] == "primary"


@pytest.mark.parametrize("regel,formen,einstellungen", [("rand", 1, 1), ("rg", 1, 1), ("laut", 2, 3), ("ucb", 5, 3), ("q", 5, 3)])
def test_belohnung_und_einstellung_folgen_der_regel(regel, formen, einstellungen):
    """Abhängige Regler: nur die Formen und Einstellungen, die die Regel kennt; gibt es nur eine, ist der Regler gesperrt (nie ein wirkungsloser Regler)."""
    at = _app()
    at.sidebar.selectbox(key="belohnung_select").set_value("rank").run()
    at.sidebar.selectbox(key="einstellung_select").set_value("hoch").run()
    at.sidebar.selectbox(key="regel_select").set_value(regel).run()
    assert not at.exception, [str(e) for e in at.exception]
    bel = at.sidebar.selectbox(key="belohnung_select")
    einst = at.sidebar.selectbox(key="einstellung_select")
    assert len(bel.options) == formen and bel.disabled == (formen == 1)
    assert len(einst.options) == einstellungen and einst.disabled == (einstellungen == 1)
    assert bel.value == ("rank" if formen == 5 else "r2")              # eine Form, die die Regel nicht kennt, fällt auf den Standard zurück
    assert einst.value == ("hoch" if einstellungen == 3 else "standard")
    assert at.session_state["belohnung_select"] == bel.value and at.session_state["einstellung_select"] == einst.value


def test_expander_und_kernfragen_in_der_vorgesehenen_reihenfolge():
    at = _app()
    titel = [e.label for e in at.expander]
    for name in ("💬 In einfachen Worten", "So funktioniert die Wahl der Zugart", "📐 Mathematische Formulierung"):
        assert name in titel
    assert titel.index("💬 In einfachen Worten") == 0 and titel[-1] == "📐 Mathematische Formulierung"
    kopf = [s.value for s in at.subheader]
    assert [k[:15] for k in kopf[:5]] == [f"🔬 Kernfrage {i}: "[:15] for i in (1, 2, 3, 4, 5)] and kopf[-1] == "🚧 Wo die Annahmen enden"
