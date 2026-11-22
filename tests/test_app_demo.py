"""AppTest-Läufe der Demo: jedes Preset, jede Regel, Permalink (Begrenzen und Einrasten), Mini-Messreihe, gesperrter Knopf über der Rechengrenze."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import asw_constants as C
import asw_presets as P

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _app(**query) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=300)
    for k, v in query.items():
        at.query_params[k] = str(v)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _meldungen(at) -> list[str]:
    return [m.value for art in ("success", "info", "warning", "error") for m in getattr(at, art)]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_laeuft_und_zeigt_alle_fuenf_kernfragen(name):
    at = _app()
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    assert len([s for s in at.subheader if s.value.startswith("🔬 Kernfrage")]) == 5
    assert not at.error
    for key, wert in C.PRESETS[name].items():
        assert at.session_state[P.PRESET_KEYS[key]] == wert, key
    assert len(_meldungen(at)) >= 6                                      # Anteil, Zelle, Gutschrift, Kredit, ohne 2opt_b5, zwei Einstellungen


@pytest.mark.parametrize("regel", C.REGELN)
@pytest.mark.parametrize("akz", C.AKZEPTANZEN)
def test_jede_regel_unter_jeder_akzeptanz(regel, akz):
    at = _app(regel=regel, akz=akz, n=60, budget=200, familie="cluster")
    assert at.session_state["regel_select"] == regel and at.session_state["akz_select"] == akz and at.session_state["n_select"] == 60
    assert at.metric[0].value == str(at.metric[0].value) and int(at.metric[0].value) > 2400     # Anwendungen bei 12 000 Auswertungen


def test_permalink_begrenzt_und_rastet_ein():
    at = _app(n=47, budget=120, instanz=5000, lauf=-3, regel="gibtsnicht", akz="la", belohnung="best", mini=999, laeufe=0)
    s = at.session_state
    assert s["n_select"] == 60 and s["budget_select"] == 50 and s["instanz_input"] == C.INSTANZ_MAX and s["lauf_input"] == 0
    assert s["regel_select"] == C.DEFAULT_REGEL and s["akz_select"] == "la" and s["belohnung_select"] == "best"
    assert s["mini_instanzen_slider"] == C.MINI_INSTANZEN_MAX and s["mini_laeufe_slider"] == C.MINI_LAEUFE_MIN


def test_permalink_mit_belohnung_die_die_regel_nicht_kennt():
    at = _app(regel="laut", belohnung="rank", einstellung="hoch")
    assert at.session_state["belohnung_select"] == "r2" and at.session_state["einstellung_select"] == "hoch"
    at = _app(regel="rand", belohnung="best", einstellung="hoch")
    assert at.session_state["belohnung_select"] == "r2" and at.session_state["einstellung_select"] == "standard"
    assert any("Maßstab" in m for m in _meldungen(at))                   # Zufall gegen sich selbst: kein Vergleich


def test_adresszeile_spiegelt_die_einstellung():
    at = _app()
    at.sidebar.selectbox(key="akz_select").set_value("ob").run()
    assert at.query_params["akz"] in ("ob", ["ob"]) and at.query_params["regel"] in (C.DEFAULT_REGEL, [C.DEFAULT_REGEL])


def test_mini_messreihe_rechnet_auf_klick_und_bleibt_bis_zur_naechsten_aenderung():
    at = _app(mini=6, laeufe=1, akz="la")
    knopf = next(b for b in at.main.button if b.label.startswith("Mini-Messreihe rechnen"))
    assert "18 000 Auswertungen" in knopf.label                         # 2 x 6 x 1 x 1500
    knopf.click().run()
    assert not at.exception
    assert any("In dieser Mini-Reihe (6 Instanzen × 1 Läufe" in m for m in _meldungen(at))
    at.run()
    assert any("In dieser Mini-Reihe (6 Instanzen × 1 Läufe" in m for m in _meldungen(at))
    at.sidebar.selectbox(key="akz_select").set_value("rr").run()
    assert not any("In dieser Mini-Reihe" in m for m in _meldungen(at))  # andere Einstellung: das alte Ergebnis wird nicht mehr gezeigt


def test_ueber_der_rechengrenze_ist_der_knopf_gesperrt():
    at = _app(n=60, budget=200, mini=30, laeufe=4)
    knopf = next(b for b in at.main.button if b.label.startswith("Mini-Messreihe rechnen"))
    assert knopf.disabled and any("2 880 000 Auswertungen, Obergrenze 600 000." in m for m in _meldungen(at))


def test_handbeispiel_schaltet_die_belohnung_um():
    at = _app()
    def wahl():
        return [t.value["zieht danach vor"].tolist() for t in at.dataframe if "zieht danach vor" in t.value.columns][0]
    assert wahl() == ["C", "C", "C"]
    at.radio(key="hand_form_radio").set_value("rbest").run()
    assert wahl() == ["A", "A", "A"]


def test_schritt_regler_und_zugmenge_ohne_2opt_b5():
    at = _app(menge="ohne_2opt_b5", akz="la")
    at.slider(key="schritt_slider").set_value(5).run()
    assert not at.exception
    assert any("ohne `2opt_b5`" in m for m in _meldungen(at))
