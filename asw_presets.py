"""Permalink (Begrenzen, Einrasten), Presets und Zufalls-Button (Standardmuster aus dem Demo-Portfolio).

SETTING_SPECS: alle Regler der Seitenleiste; sie stehen im Permalink und entscheiden, welches Beispiel hervorgehoben ist."""

import random
from dataclasses import dataclass

import streamlit as st

import asw_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None       # Auswahlregler: erlaubte Werte


SETTING_SPECS = {
    "familie_select": SettingSpec("familie", str, C.DEFAULT_FAMILIE, options=C.FAMILIEN),
    "n_select": SettingSpec("n", int, C.DEFAULT_N, options=C.N_GEMESSEN),
    "budget_select": SettingSpec("budget", int, C.DEFAULT_BUDGET, options=C.STUFEN),
    "instanz_input": SettingSpec("instanz", int, C.DEFAULT_INSTANZ, 0, C.INSTANZ_MAX),
    "lauf_input": SettingSpec("lauf", int, C.DEFAULT_LAUF, 0, C.LAUF_MAX),
    "regel_select": SettingSpec("regel", str, C.DEFAULT_REGEL, options=C.REGELN),
    "akz_select": SettingSpec("akz", str, C.DEFAULT_AKZ, options=C.AKZEPTANZEN),
    "belohnung_select": SettingSpec("belohnung", str, C.DEFAULT_BELOHNUNG, options=C.BELOHNUNGEN),
    "menge_select": SettingSpec("menge", str, C.DEFAULT_MENGE, options=tuple(C.MENGEN)),
    "einstellung_select": SettingSpec("einstellung", str, C.DEFAULT_EINSTELLUNG, options=C.EINSTELLUNGEN),
    "mini_instanzen_slider": SettingSpec("mini", int, C.DEFAULT_MINI_INSTANZEN, C.MINI_INSTANZEN_MIN, C.MINI_INSTANZEN_MAX),
    "mini_laeufe_slider": SettingSpec("laeufe", int, C.DEFAULT_MINI_LAEUFE, C.MINI_LAEUFE_MIN, C.MINI_LAEUFE_MAX),
}
PRESET_KEYS = {"familie": "familie_select", "n": "n_select", "budget": "budget_select", "instanz": "instanz_input", "lauf": "lauf_input",
               "regel": "regel_select", "akz": "akz_select", "belohnung": "belohnung_select", "menge": "menge_select",
               "einstellung": "einstellung_select", "mini_instanzen": "mini_instanzen_slider", "mini_laeufe": "mini_laeufe_slider"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def options(state_key) -> tuple:
    """Erlaubte Werte eines Auswahlreglers."""
    return SETTING_SPECS[state_key].options


def clamp(spec: SettingSpec, value):
    """Wert aus der Adresszeile auf den Regler abbilden: Zahlen begrenzen, Auswahlwerte einrasten (Zahl: nächster Wert; Text: nur gültige)."""
    if spec.options is not None:
        if value in spec.options:
            return value
        if spec.caster is int:
            return min(spec.options, key=lambda o: (abs(o - value), o))
        return None
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    return value


def belohnung_gueltig(regel: str, belohnung: str) -> str:
    """Die Belohnungsform, mit der die Regel rechnet: die gewählte, wenn die Regel sie kennt, sonst die Standardform."""
    return belohnung if belohnung in C.BELOHNUNGEN_JE_REGEL[regel] else C.DEFAULT_BELOHNUNG


def normalize_state():
    """Hält abhängige Regler gültig, bevor sie gezeichnet werden: eine Belohnungsform, die die gewählte Regel nicht kennt, und eine
    Einstellung für eine Regel ohne Parameter fallen auf den Standard zurück (so bleibt jeder gezeigte Wert der, mit dem gerechnet wird)."""
    regel = st.session_state.get("regel_select", C.DEFAULT_REGEL)
    bel = st.session_state.get("belohnung_select", C.DEFAULT_BELOHNUNG)
    if belohnung_gueltig(regel, bel) != bel:
        st.session_state["belohnung_select"] = C.DEFAULT_BELOHNUNG
    if regel not in C.PARAMETER and st.session_state.get("einstellung_select", C.DEFAULT_EINSTELLUNG) != C.DEFAULT_EINSTELLUNG:
        st.session_state["einstellung_select"] = C.DEFAULT_EINSTELLUNG


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, begrenzt bzw. eingerastet."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            value = clamp(spec, value)
            if value is not None:
                st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Einstellung."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen
    Standardwert) mit dem Session State. Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS,
    dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )


def randomize_instance():
    st.session_state["instanz_input"] = random.randint(0, C.INSTANZ_MAX)
