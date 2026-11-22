"""Wer belohnt wen? Kreditzuweisung bei der Wahl der Zugart - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Dritte Demo der Linie „Hyperheuristiken erklärt“: sechs Auswahlregeln, fünf Belohnungsformen und drei Akzeptanzregeln auf der Rundtour.
Aufbau nach DEMO-PLAYBOOK.md (§2): fester Kopf, Presets in der Seitenleiste, Kernfragen mit Live-Rechnung und Verdikt, Annahmen, Formeln.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import asw_algorithm as A
import asw_constants as C
import asw_evaluation as E
import asw_frozen as F
import asw_hand as H
import asw_presets as P
import asw_regeln as R
import asw_saetze as SZ
import asw_texts as T
import asw_visualization as V
import modul_frisch
from asw_layout import dunkles_design, kopf_css

modul_frisch.aktualisieren(__file__)

st.set_page_config(page_title=T.SEITENTITEL, layout="wide")
de, iv = E.de, E.intervall


@st.cache_data(show_spinner=False)
def _lauf(familie, n, idx, lauf, regel, akz, bel, menge, faktor, einstellung):
    """Ein Lauf mit Spur und Gutschriftkonto (alle Eingaben stehen im Schlüssel)."""
    r = A.run(familie, n, idx, lauf, regel, akz, bel, C.MENGEN[menge], faktor * n, spur=True, wert=R.parameter_wert(regel, einstellung))
    k = r["konto"]
    return dict(best=r["best"], start=r["start"], used=r["used"], steps=r["steps"], arms=r["arms"], spur=k.spur, apps=k.apps, evals=k.evals,
                gut_r2=k.gut_r2, gut_best=k.gut_best, w=r["w"], anteil_ohne=r["anteil_ohne"], verschlechterungen=k.verschlechterungen)


@st.cache_data(show_spinner=False)
def _wirkung_tabelle(j):
    return SZ.tabelle_wirkung(j)


@st.cache_data(show_spinner=False)
def _anteil_tabelle():
    return SZ.tabelle_anteile()


@st.cache_data(show_spinner=False)
def _kredit_tabelle(akz):
    return SZ.tabelle_belohnung(akz)


@st.cache_data(show_spinner=False)
def _empf_tabelle(akz, j):
    return SZ.tabelle_empfindlichkeit(akz, j)


def zeige(verdikt):
    art, text = verdikt
    getattr(st, art)(text)


# ---------------------------------------------------------------- Kopf und Einleitung
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title(T.TITEL)
st.markdown(T.INTRO)

# erklaerseite:einfach:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/auswahlregeln-erklaert.json, nicht von Hand ändern)
with st.expander("💬 In einfachen Worten"):
    st.markdown(
        """
Eine Suche verbessert eine Rundtour Schritt für Schritt mit kleinen Änderungen, den Zugarten. In jedem Schritt muss eine Zugart gewählt werden. Die einfachste Regel würfelt. Klüger klingt es, sich zu merken, welche Zugart zuletzt Erfolg hatte, und sie öfter zu nehmen.

Die Schwierigkeit: Manche Suchen lassen zwischendurch absichtlich eine längere Tour zu. Eine Zugart, die danach den Umweg wieder aufholt, sieht dann wie ein Held aus, obwohl die Tour nicht kürzer ist als vorher. Wer das Lob bekommt, bestimmt, was gelernt wird. Die Demo vergleicht sechs Regeln und fünf Formen des Lobs und zeigt, wann Lernen dem Würfeln etwas voraushat und wann nicht. Ob das Lob für das Aufholen der Grund dafür ist, bleibt offen.

[Ausführlich und verständlich erklärt, mit Fachteil](https://sebastianhanisch.net/auswahlregeln-erklaert.html)
        """
    )
# erklaerseite:einfach:end

P.load_permalink_settings()
P.init_session_state_defaults()
P.normalize_state()

with st.expander("So funktioniert die Wahl der Zugart", expanded=True):
    st.markdown(T.ABLAUF)
    st.markdown("**Die sechs Regeln**")
    st.markdown(T.REGEL_TABELLE)
    st.markdown("**Die fünf Belohnungsformen**")
    st.markdown(T.BELOHNUNG_TABELLE)
    st.markdown("**Die drei Akzeptanzregeln**")
    st.markdown(T.AKZEPTANZ_TABELLE)
    st.markdown("**Die acht Zugarten**")
    st.markdown(T.ZUGART_TABELLE)

# ---------------------------------------------------------------- Seitenleiste
with st.sidebar:
    P.sidebar_presets()
    st.header("🗺️ Rundtour und Budget")
    familie = st.selectbox("Familie der Städte", P.options("familie_select"), key="familie_select", format_func=C.FAMILIEN_ANZEIGE.get,
                           help="Wie die Städte erzeugt werden: gleichverteilt, in fünf Gruppen oder auf einem gestörten Gitter.")
    n = st.selectbox("Städte n", P.options("n_select"), key="n_select", help="Nur die zwei Größen der eingefrorenen Messung.")
    faktor = st.selectbox("Budget in Auswertungen", P.options("budget_select"), key="budget_select", format_func=C.STUFEN_ANZEIGE.get,
                          help="Eine Auswertung ist ein bewerteter Vorschlag; 2opt_b5 kostet bis zu fünf.")
    idx = st.number_input("Instanz", *P.bounds("instanz_input"), key="instanz_input", step=1,
                          help="Nummer der erzeugten Rundtour (Zufalls-Seed der Instanz). Die eingefrorene Messung nutzt 0 bis 19.")
    lauf = st.number_input("Zufalls-Seed des Laufs", *P.bounds("lauf_input"), key="lauf_input", step=1,
                           help="Bestimmt Starttour und Zufallsstrom. Alle Regeln lesen denselben Strom von vorn.")
    st.header("🎛️ Auswahl und Gutschrift")
    regel = st.selectbox("Auswahlregel", P.options("regel_select"), key="regel_select", format_func=C.REGEL_ANZEIGE.get)
    akz = st.selectbox("Akzeptanzregel", P.options("akz_select"), key="akz_select", format_func=C.AKZ_ANZEIGE.get)
    bel_optionen = C.BELOHNUNGEN_JE_REGEL[regel]
    bel = st.selectbox("Belohnung", bel_optionen, key="belohnung_select", format_func=C.BELOHNUNG_ANZEIGE.get, disabled=len(bel_optionen) == 1,
                       help="Was der Regel als Erfolg gutgeschrieben wird. Zufall liest keine Belohnung, der Zufallsgradient nur, ob die "
                            "aktuelle Tour kürzer wurde; der Lernautomat kennt nur die zwei Formen, die Erfolg anders abgrenzen.")
    menge = st.selectbox("Zugmenge", P.options("menge_select"), key="menge_select", format_func=C.MENGEN_ANZEIGE.get,
                         help="Alle acht Zugarten oder alle außer 2opt_b5. Weitere Mengen vergleicht die Demo „Die Zugmenge entscheidet“.")
    einst_optionen = C.EINSTELLUNGEN if regel in C.PARAMETER else (C.DEFAULT_EINSTELLUNG,)
    einstellung = st.selectbox("Einstellung der Regel", einst_optionen, key="einstellung_select", format_func=lambda e: SZ.einstellung_text(regel, e),
                               disabled=len(einst_optionen) == 1, help="Ein Parameter je Regel mit dem Standardwert und zwei weiteren gemessenen Werten (Kernfrage 5).")
    st.header("📏 Mini-Messreihe")
    mini_m = st.slider("Instanzen", *P.bounds("mini_instanzen_slider"), key="mini_instanzen_slider",
                       help="Die Reihe rechnet die gewählte Regel und Zufall auf so vielen aufeinanderfolgenden Instanzen ab der gewählten.")
    mini_l = st.slider("Läufe je Instanz", *P.bounds("mini_laeufe_slider"), key="mini_laeufe_slider")
    st.button("🎲 Neue Instanz", on_click=P.randomize_instance, width="stretch", key="zufall_button")

P.sync_query_params({"familie_select": familie, "n_select": n, "budget_select": faktor, "instanz_input": idx, "lauf_input": lauf, "regel_select": regel,
                     "akz_select": akz, "belohnung_select": bel, "menge_select": menge, "einstellung_select": einstellung,
                     "mini_instanzen_slider": mini_m, "mini_laeufe_slider": mini_l})

j = C.STUFEN.index(faktor)
regel_name, akz_name, stufe_name = C.REGEL_ANZEIGE[regel], C.AKZ_KURZ[akz], C.STUFEN_ANZEIGE[faktor]
meta = F.meta()
lauf_daten = _lauf(familie, n, int(idx), int(lauf), regel, akz, bel, menge, faktor, einstellung)
arms = lauf_daten["arms"]

# ---------------------------------------------------------------- Kernfrage 1
st.subheader("🔬 Kernfrage 1: Wohin geht die Auswahl?")
st.markdown(
    f"Ein Lauf mit **{regel_name}**, Akzeptanz **{akz_name}**, Belohnung „{C.BELOHNUNG_KURZ[bel]}“, {SZ.einstellung_text(regel, einstellung)}, "
    f"Zugmenge **{C.MENGEN_ANZEIGE[menge]}**, {faktor * n} Auswertungen auf der Instanz {int(idx)} ({C.FAMILIEN_ANZEIGE[familie]}, n = {n})."
)
anteil_k = st.slider("Lauf zeigen bis (Prozent der Anwendungen)", C.SCHRITT_MIN, 100, 100, step=C.SCHRITT_MIN, key="schritt_slider")
k_bis = max(1, lauf_daten["steps"] * anteil_k // 100)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Anwendungen", lauf_daten["steps"])
c2.metric("Verbesserung gegenüber der Starttour", f"{de(100 * (lauf_daten['start'] - lauf_daten['best']) / lauf_daten['start'], 1)} %")
c3.metric("angenommene Verschlechterungen", lauf_daten["verschlechterungen"])
c4.metric("beste Tour", de(lauf_daten["best"], 1))
links, rechts = st.columns(2)
links.plotly_chart(V.fig_verlauf(lauf_daten["spur"], lauf_daten["start"], k_bis), key="fig_verlauf", config={"displayModeBar": False})
rechts.plotly_chart(V.fig_fenster(lauf_daten["spur"], arms, k_bis), key="fig_fenster", config={"displayModeBar": False})
a_apps, a_evals = A.shares(lauf_daten["apps"], lauf_daten["evals"])
gleich = F.gleichverteilung(len(arms), C.H_2OPT_B5 in arms)
st.plotly_chart(V.fig_anteile(a_apps, a_evals, arms, 100.0 / len(arms)), key="fig_anteile", config={"displayModeBar": False})
h_top = max(arms, key=lambda h: a_apps[h])
gleich_top = F.gleichverteilung(len(arms), C.H_2OPT_B5 in arms and h_top == C.H_2OPT_B5)
zeige(E.verdict_anteil(regel_name, C.HNAMEN[h_top], 100 * a_apps[h_top], 100 * a_evals[h_top], gleich_top[0], gleich_top[1]))
st.markdown(SZ.satz_anteile())
st.dataframe(_anteil_tabelle(), hide_index=True, width="stretch")
st.caption(SZ.mess_caption() + " Anteile in Prozent, Summe über alle Läufe bis 200·n, Standardbelohnung.")

# ---------------------------------------------------------------- Kernfrage 2
st.subheader("🔬 Kernfrage 2: Schlägt eine Regel, die den Erfolg beachtet, den Zufall?")
if regel == "rand":
    st.info("Gewählt ist die Zufallswahl selbst: sie ist der Maßstab. Eine andere Regel wählen, um sie mit Zufall zu vergleichen.")
elif menge == "voll" and einstellung == "standard":
    zelle = F.diff(akz, F.key(regel, bel), j)
    zeige(E.verdict_zelle(regel_name, C.BELOHNUNG_KURZ[bel], akz_name, stufe_name, zelle["d"], zelle["lo"], zelle["hi"], meta["instanzen"], meta["laeufe"]))
elif menge == "ohne_2opt_b5" and einstellung == "standard" and bel == "r2":
    zelle = F.diff(akz, F.key(regel, bel), j, "ohne_2opt_b5")
    zeige(E.verdict_zelle(regel_name + " ohne `2opt_b5`", C.BELOHNUNG_KURZ[bel], akz_name, stufe_name, zelle["d"], zelle["lo"], zelle["hi"],
                          meta["instanzen"], meta["laeufe"]))
else:
    st.info("Für diese Kombination aus Zugmenge, Belohnung und Einstellung gibt es keine eingefrorene Zelle; die Mini-Messreihe unten rechnet sie live.")
st.markdown(SZ.satz_wirkung())
st.plotly_chart(V.fig_wirkung(SZ.zeilen_wirkung(j), f"Standardbelohnung, Budget {stufe_name}: fünf Regeln × drei Akzeptanzregeln"), key="fig_wirkung",
                config={"displayModeBar": False})
with st.expander("Alle 18 Paare aus Regel und Belohnung (eingefroren)"):
    st.dataframe(_wirkung_tabelle(j), hide_index=True, width="stretch")
    st.caption(SZ.mess_caption() + f" Unterschied „Zufall minus Regel“ in Prozentpunkten des Abstands bei Budget {stufe_name}, in Klammern das 95-%-Intervall "
               "(Bootstrap über die Instanzen). Klassen: besser ab +0,25 mit Intervall über 0, schlechter ab −0,10 mit Intervall unter 0.")

st.markdown("**Live: Mini-Messreihe** (die gewählte Regel gegen Zufall, gepaart: gleiche Instanzen, Starttouren und Zufallszahlen)")
kosten = E.mini_kosten(mini_m, mini_l, n, faktor)
mini_schluessel = (familie, n, int(idx), mini_m, mini_l, regel, akz, bel, menge, faktor, einstellung)
if regel == "rand":
    st.caption("Mit der Zufallswahl gegen sich selbst gibt es nichts zu rechnen.")
elif not E.mini_erlaubt(mini_m, mini_l, n, faktor):
    st.button("Mini-Messreihe rechnen", disabled=True, key="mini_button")
    st.warning(f"Zu groß für die Live-Rechnung: {E.tsd(kosten)} Auswertungen, Obergrenze {E.tsd(C.RECHENGRENZE)}. Weniger Instanzen, weniger Läufe "
               "oder das kleine Budget wählen.")
else:
    if st.button(f"Mini-Messreihe rechnen ({E.tsd(kosten)} Auswertungen)", key="mini_button"):
        with st.spinner(f"Rechne {E.tsd(kosten)} Auswertungen …"):
            st.session_state["mini_ergebnis"] = (mini_schluessel, E.mini_reihe(F.reference, familie, n, int(idx), mini_m, mini_l, regel, akz, bel,
                                                                              C.MENGEN[menge], faktor, R.parameter_wert(regel, einstellung)))
    gespeichert = st.session_state.get("mini_ergebnis")
    if gespeichert and gespeichert[0] == mini_schluessel:
        mr = gespeichert[1]
        zeige(E.verdict_vergleich(regel_name, akz_name, stufe_name, mr["d"], mr["lo"], mr["hi"], mr["m"], mr["laeufe"]))
        m1, m2, m3 = st.columns(3)
        m1.metric("Abstand Zufall", f"{de(mr['abstand_zufall'])} %")
        m2.metric(f"Abstand {regel_name}", f"{de(mr['abstand_regel'])} %", delta=f"{de(mr['abstand_regel'] - mr['abstand_zufall'], 2, True)} Punkte", delta_color="inverse")
        m3.metric("Halbbreite des Intervalls", f"{de(mr['halbbreite'])} Punkte")
        st.plotly_chart(V.fig_mini(mr["je_instanz"]), key="fig_mini", config={"displayModeBar": False})
    else:
        st.caption("Noch nicht gerechnet für diese Einstellung. " + SZ.satz_mini())

# ---------------------------------------------------------------- Kernfrage 3
st.subheader("🔬 Kernfrage 3: Wer bekommt das Lob für eine Reparatur?")
st.markdown(
    "**Handbeispiel ohne Zufall.** Sechs Städte, Starttour mit Länge 30, drei Zugarten mit je einer Auswertung (A = 2-opt, B = Tausch, "
    "C = Einfügen), Late Acceptance mit einer Liste der Länge 2. Die fünf Züge sind vorgegeben. Der Bestwert fällt nur in Schritt 0 (von 30 "
    "auf 28); danach nimmt die Suche zweimal eine Verlängerung an, und Zugart C repariert sie zweimal. Die Belohnung eines Zuges ist die Verkürzung "
    "geteilt durch die mittlere Kantenlänge der Starttour (30 / 6 = 5), hier also 2/5 = 0,4 je Verkürzung um 2; die Gutschrift einer Zugart ist "
    "die Summe ihrer Belohnungen."
)
hand_form = st.radio("Belohnung im Handbeispiel", ("r2", "rbest"), key="hand_form_radio", horizontal=True,
                     format_func={"r2": "Standard (Verbesserung der aktuellen Tour)", "rbest": "nur Verbesserung des Bestwerts"}.get)
hz = H.schritte("la")
hk = H.kennzahlen(hz)
st.dataframe([{"Schritt": z["schritt"], "Zug": z["text"], "Änderung": int(z["delta"]), "Länge danach": int(z["kosten"]),
               "angenommen": "ja" if z["angenommen"] else "nein", "Bestwert": int(z["best"]), "Belohnung": de(z[hand_form], 1)} for z in hz],
             hide_index=True, width="stretch")
hs = H.zustaende(hz, hand_form)
st.dataframe([
    {"Regel": "Lernautomat", "Zustand nach fünf Schritten (A, B, C)": "p = " + " / ".join(de(x, 4) for x in hs["laut"]["p"]), "zieht danach vor": hs["laut"]["wahl"]},
    {"Regel": "Q-Lernen", "Zustand nach fünf Schritten (A, B, C)": "Q = " + " / ".join(de(x, 4) for x in hs["q"]["q"]), "zieht danach vor": hs["q"]["wahl"]},
    {"Regel": "Choice Function", "Zustand nach fünf Schritten (A, B, C)": "Wertung = " + " / ".join(de(x, 4) for x in hs["cf"]["wertung"]), "zieht danach vor": hs["cf"]["wahl"]},
], hide_index=True, width="stretch")
st.info(
    f"Gutschrift im Handbeispiel: nach der Standardform bekommt A {de(hk['konto']['r2']['A'], 1)}, B {de(hk['konto']['r2']['B'], 1)} und C "
    f"{de(hk['konto']['r2']['C'], 1)}; nach „nur Bestwert“ bekommt A {de(hk['konto']['rbest']['A'], 1)} und C {de(hk['konto']['rbest']['C'], 1)}. "
    f"Die Summe der Verbesserungen ist {int(hk['arbeit'])}, der Nettogewinn {int(hk['netto'])}: W = {de(hk['w'], 0)}. Mit der Standardform ziehen alle "
    "drei Regeln danach die Reparatur C vor, mit „nur Bestwert“ die Zugart A. Die Zugfolge ist vorgegeben; sie stammt nicht von einer der Regeln."
)
st.markdown("**Live: Gutschriftkonto des Laufs aus Kernfrage 1** (beide Formen nebeneinander, unabhängig davon, welche die Regel liest)")
st.plotly_chart(V.fig_konto(lauf_daten["gut_r2"], lauf_daten["gut_best"], arms), key="fig_konto", config={"displayModeBar": False})
zeige(E.verdict_gutschrift(akz, lauf_daten["anteil_ohne"], lauf_daten["w"]))
st.markdown(SZ.satz_gutschrift())

# ---------------------------------------------------------------- Kernfrage 4
st.subheader("🔬 Kernfrage 4: Ändert eine andere Gutschrift etwas?")
kredit = F.kredit_rows("la")
verd = F.verduennung()
verd_urteil = E.urteil_verduennung(verd["d"][1]["d"], verd["d"][1]["lo"], verd["anteil"], verd["ziel"])
zeige(E.verdict_kredit(kredit, verd_urteil, verd["d"][1]["d"], verd["d"][1]["lo"], verd["d"][1]["hi"]))
st.markdown(SZ.satz_kredit())
st.dataframe(_kredit_tabelle(akz), hide_index=True, width="stretch")
st.caption(SZ.mess_caption() + f" Zeilen für die gewählte Akzeptanzregel ({akz_name}); Unterschied zu Zufall in Prozentpunkten mit 95-%-Intervall, "
           "Anteil von `2opt_b5` an Anwendungen und Auswertungen bis 200·n.")
st.markdown(SZ.satz_verduennung())
ohne_zeilen = [(C.REGEL_ANZEIGE[r], x["d"], x["lo"], x["hi"], x["klasse"]) for r in C.DREI_REGELN for x in [F.diff(akz, F.key(r), j, "ohne_2opt_b5")]]
zeige(E.verdict_ohne_b5(akz_name, stufe_name, ohne_zeilen))
if regel in C.LERNREGELN and len(C.BELOHNUNGEN_JE_REGEL[regel]) > 1:
    zwei = {form: _lauf(familie, n, int(idx), int(lauf), regel, akz, form, menge, faktor, einstellung) for form in ("r2", "best")}
    st.markdown(f"**Live: zwei Läufe von {regel_name}** auf derselben Instanz mit demselben Zufalls-Seed, einmal mit der Standardbelohnung, einmal mit „nur Bestwert“")
    z1, z2, z3, z4 = st.columns(4)
    z1.metric("beste Tour, Standard", de(zwei["r2"]["best"], 1))
    z2.metric("beste Tour, nur Bestwert", de(zwei["best"]["best"], 1), delta=de(zwei["best"]["best"] - zwei["r2"]["best"], 1, True), delta_color="inverse")
    b5 = [100.0 * zwei[f]["apps"][C.H_2OPT_B5] / max(1, sum(zwei[f]["apps"])) for f in ("r2", "best")]
    z3.metric("Anteil `2opt_b5`, Standard", f"{de(b5[0], 1)} %")
    z4.metric("Anteil `2opt_b5`, nur Bestwert", f"{de(b5[1], 1)} %")
    st.caption("Ein einzelner Lauf belegt nichts: die Zahlen oben schwanken von Instanz zu Instanz; die Aussage steht in der eingefrorenen Tabelle.")

# ---------------------------------------------------------------- Kernfrage 5
st.subheader("🔬 Kernfrage 5: Liegt es an der Einstellung der Regel?")
for akz_e in C.EMPF_AKZEPTANZEN:
    es = F.empf_summary(akz_e, j)
    b = es["beste"]
    zeige(E.verdict_einstellung(C.AKZ_KURZ[akz_e], stufe_name, es["varianten"], es["besser"], es["schlechter"], SZ.variante_text(b), b["d"], b["lo"], b["hi"]))
st.markdown(SZ.satz_empfindlichkeit())
with st.expander("Alle 20 Varianten je Akzeptanzregel (eingefroren)"):
    for akz_e in C.EMPF_AKZEPTANZEN:
        st.markdown(f"**{C.AKZ_KURZ[akz_e]}, Budget {stufe_name}**")
        st.dataframe(_empf_tabelle(akz_e, j), hide_index=True, width="stretch")
    st.caption(SZ.mess_caption() + " Je Regel ein Parameter mit zwei Werten neben dem Standard; bei Choice Function, UCB und Q-Lernen mit drei Belohnungsformen.")

# ---------------------------------------------------------------- Annahmen, Formeln, Footer
st.subheader("🚧 Wo die Annahmen enden")
st.markdown(T.ASSUMPTIONS_MARKDOWN)
st.markdown(T.NACHBARN)

with st.expander("📐 Mathematische Formulierung"):
    # erklaerseite:lesehilfe:start (erzeugt von tools/set_demo_explainer.py (Website-Repo) aus tools/content/explainers/auswahlregeln-erklaert.json, nicht von Hand ändern)
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind n Städte mit Abständen, eine Starttour, eine Menge von Zugarten und ein Budget an Auswertungen. Gesucht ist eine kurze Rundtour; die Demo fragt, welche Regel die Zugarten wählt und wie sie belohnt wird. Der Block ist ein vollständiges Modell der gemessenen Regeln (Suchrahmen, Akzeptanz, Belohnung, Auswahl, Gutschrift). Die Längenänderung steht nur für 2-opt ausgeschrieben; die übrigen Zugarten rechnen sie genauso aus den entfernten und den neuen Kanten.

| Symbol | Bedeutung |
|---|---|
| $t$, $d$, $L(t)$ | Tour (Reihenfolge der $n$ Städte), Abstand, Länge der Tour |
| $h$, $c_h$ | Zugart (eine von acht), Auswertungen je Anwendung (1; bei `2opt_b5` bis 5) |
| $B$ | Budget in Auswertungen (50·n oder 200·n) |
| $\Delta_k$ | Längenänderung des Vorschlags in Anwendung $k$ |
| $L^{*}_k$ | Bestwert: Länge der besten Tour nach $k$ Anwendungen |
| $\rho$, $\Lambda$, $\ell$ | Toleranz von Rekord-zu-Rekord (0,01); Länge (50) und Einträge der Liste von Late Acceptance (anfangs $L(t_0)$) |
| $\bar e$ | mittlere Kantenlänge der Starttour |
| $r_k$, $r_k^{\mathrm{best}}$ | Belohnung in der Standardform und in der Form „nur Bestwert“ |
| $G_h$, $W$ | Gutschrift der Zugart $h$; Verbesserungsarbeit je Nettogewinn |
| $p_j$, $Q_j$, $F_j$, $s_j$ | Wahrscheinlichkeit (Lernautomat), Wert (Q-Lernen), Wertung (Choice Function), Index (UCB) der Zugart $j$ |
| $a$, $\alpha$, $\gamma$, $\varepsilon$, $\varphi$, $c$ | Parameter der Regeln (Werte in den Formeln) |
| $f_{1,j}$, $f_{2,i,j}$, $\tau_j$ | Choice Function: Leistung der Zugart $j$, Leistung von $j$ direkt nach $i$, Schritte seit der letzten Anwendung von $j$ |
| $S_j$, $n_j$, $N$, $r_{\max}$ | UCB: abgewertete Belohnungssumme und Anwendungszahl von $j$, $N = \sum_j n_j$, größte bisherige Belohnung |

[Schritt für Schritt erklärt, mit Herleitung und Literatur](https://sebastianhanisch.net/auswahlregeln-erklaert.html#fachleute)
        """
    )
    # erklaerseite:lesehilfe:end
    for titel, formel in T.FORMELN:
        st.markdown(f"**{titel}**")
        st.markdown(f"$$\n{formel}\n$$")
    st.markdown(T.FORMEL_NACHSATZ)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Hyperheuristiken: Auswählen und Erzeugen](https://sebastianhanisch.net/konzepte-hyperheuristiken.html)."
)
