"""Sätze und Tabellen mit Messzahlen: alles wird aus der eingefrorenen Messung gerechnet (asw_frozen), nichts steht von Hand im Text.

Die README führt dieselben Sätze wörtlich (tests/test_claims.py vergleicht), und test_claims rechnet die Zahlen unabhängig aus der Datei nach."""

import asw_constants as C
import asw_frozen as F
from asw_evaluation import de, intervall


def zahl(x: dict) -> str:
    """Unterschied mit Intervall: '+1,15 [+0,79; +1,51]'."""
    return f"{de(x['d'], 2, True)} {intervall(x['lo'], x['hi'])}"


def mess_caption() -> str:
    m = F.meta()
    return (f"Eingefrorene Messung: {m['instanzen']} Instanzen (3 Familien × n = 30 und 60 × 20 Instanzen) × {m['laeufe']} Läufe, "
            "Zähleinheit Auswertungen.")


def einstellung_text(regel: str, einstellung: str) -> str:
    """Anzeige der Einstellung: 'Standardwert (α = 0,9)' usw.; Regeln ohne Parameter: 'keine Einstellung'."""
    if regel not in C.PARAMETER:
        return "keine Einstellung"
    name, standard, niedrig, hoch = C.PARAMETER[regel]
    wert = {"standard": standard, "niedrig": niedrig, "hoch": hoch}[einstellung]
    symbol = {"alpha": "α", "c": "c", "a": "a"}[name]
    return f"{C.EINSTELLUNG_ANZEIGE[einstellung]} ({symbol} = {str(wert).replace('.', ',')})"


def variante_text(zeile: dict) -> str:
    """Name einer Variante der Empfindlichkeit: 'UCB mit c = 1,0, Belohnung „Standard“'."""
    name = {"alpha": "α", "c": "c", "a": "a"}[C.PARAMETER[zeile["regel"]][0]]
    return f"{C.REGEL_ANZEIGE[zeile['regel']]} mit {name} = {str(zeile['wert']).replace('.', ',')}, Belohnung „{C.BELOHNUNG_KURZ[zeile['belohnung']]}“"


_KLASSE = {"besser": "besser", "schlechter": "schlechter", "gleich": "gleich"}


# ---------------------------------------------------------------- Tabellen (Listen von Zeilen für st.dataframe; Zahlen als Text mit Dezimalkomma)
def tabelle_wirkung(j: int) -> list[dict]:
    rows = []
    for regel, bel in C.PAARE:
        zeile = {"Regel": C.REGEL_ANZEIGE[regel], "Belohnung": C.BELOHNUNG_KURZ[bel]}
        for akz in C.AKZEPTANZEN:
            x = F.diff(akz, F.key(regel, bel), j)
            zeile[C.AKZ_KURZ[akz]] = zahl(x)
            zeile["Klasse " + C.AKZ_KURZ[akz]] = _KLASSE[x["klasse"]]
        rows.append(zeile)
    return rows


def zeilen_wirkung(j: int) -> list[tuple]:
    """Zeilen des Diagramms: fünf Regeln mit Standardbelohnung × drei Akzeptanzregeln."""
    return [(f"{C.REGEL_ANZEIGE[regel]} · {C.AKZ_KURZ[akz]}", x["d"], x["lo"], x["hi"], x["klasse"])
            for akz in C.AKZEPTANZEN for regel, bel in C.PAARE_STANDARD for x in [F.diff(akz, F.key(regel, bel), j)]]


def tabelle_anteile() -> list[dict]:
    """Anteil auf 2opt_b5 (Anwendungen / Auswertungen) je Regel und Akzeptanzregel, Standardbelohnung, bis 200·n; dazu die häufigste Zugart."""
    rows = []
    for regel in C.REGELN:
        zeile = {"Regel": C.REGEL_ANZEIGE[regel]}
        for akz in C.AKZEPTANZEN:
            a, w = F.share("voll", akz, F.key(regel))
            zeile[C.AKZ_KURZ[akz] + ": 2opt_b5"] = f"{de(a, 1)} / {de(w, 1)}"
            h, top = F.top_share("voll", akz, F.key(regel))
            zeile[C.AKZ_KURZ[akz] + ": häufigste"] = f"{C.HNAMEN[h]} {de(top, 1)}"
        rows.append(zeile)
    return rows


def tabelle_belohnung(akz: str) -> list[dict]:
    """Belohnung × Regel für eine Akzeptanzregel: Unterschied zu Zufall bei beiden Budgets, Anteil von 2opt_b5, W und Gutschrift ohne Bestwert."""
    rows = []
    for regel, bel in C.PAARE:
        if regel == "rg":
            continue
        s = F.key(regel, bel)
        a, w = F.share("voll", akz, s)
        g = F.gutschrift(akz, s)
        rows.append({"Regel": C.REGEL_ANZEIGE[regel], "Belohnung": C.BELOHNUNG_KURZ[bel], "klein (50·n)": zahl(F.diff(akz, s, 0)),
                     "groß (200·n)": zahl(F.diff(akz, s, 1)), "2opt_b5: Anwendungen / Auswertungen in %": f"{de(a, 1)} / {de(w, 1)}",
                     "Gutschrift ohne neuen Bestwert in %": de(g["ohne"], 1), "W": de(g["w"])})
    return rows


def tabelle_empfindlichkeit(akz: str, j: int) -> list[dict]:
    rows = []
    for regel in C.LERNREGELN:
        x = F.diff(akz, F.key(regel), j)
        rows.append({"Regel": C.REGEL_ANZEIGE[regel], "Parameter": einstellung_text(regel, "standard"), "Belohnung": C.BELOHNUNG_KURZ["r2"],
                     "Zufall minus Regel": zahl(x), "Klasse": _KLASSE[x["klasse"]]})
    for z in F.empf_rows(akz, j):
        rows.append({"Regel": C.REGEL_ANZEIGE[z["regel"]], "Parameter": einstellung_text(z["regel"], z["einstellung"]),
                     "Belohnung": C.BELOHNUNG_KURZ[z["belohnung"]], "Zufall minus Regel": zahl(z), "Klasse": _KLASSE[z["klasse"]]})
    return rows


# ---------------------------------------------------------------- Sätze (jede Zahl aus der Datei gerechnet)
def _z(akz: str, regel: str, j: int, bel: str = "r2", block: str = "voll") -> dict:
    return F.diff(akz, F.key(regel, bel), j, block)


def _drei(akz: str, j: int, bel: str = "r2", block: str = "voll") -> str:
    """Choice Function, Lernautomat, Q-Lernen in dieser Reihenfolge: '+1,14 / +0,84 / +0,88'."""
    return " / ".join(de(_z(akz, r, j, bel, block)["d"], 2, True) for r in C.DREI_REGELN)


def _vor_zufall(akz: str, j: int) -> int:
    """Zahl der fünf Regeln mit Standardbelohnung (ohne Zufall), die unter dieser Akzeptanzregel die Marke erreichen."""
    return sum(1 for r in ("rg", "cf", "ucb", "laut", "q") if _z(akz, r, j)["klasse"] == "besser")


def kernbotschaft() -> str:
    z = F.zaehlung(C.PAARE_STANDARD)
    alle = F.zaehlung()
    return (
        f"Ob eine Regel, die den Erfolg der Zugarten beachtet, die Zufallswahl schlägt, hängt in dieser Messung an der Akzeptanzregel und am Budget. "
        f"Bei kleinem Budget (50·n Auswertungen) liegen Choice Function, Lernautomat und Q-Lernen mit der Standardbelohnung unter Rekord-zu-Rekord "
        f"{_drei('rr', 0)} Prozentpunkte vor Zufall (alle drei über der gesetzten Marke 0,25, siehe Methodik, mit Intervall über 0) und unter "
        f"Late Acceptance {_drei('la', 0)} Punkte dahinter (alle drei mit Intervall unter 0). "
        f"Unter Rekord-zu-Rekord liegt bei kleinem Budget auch UCB vor Zufall ({zahl(_z('rr', 'ucb', 0))}), der Zufallsgradient nicht "
        f"({zahl(_z('rr', 'rg', 0))}); von den fünf Regeln ohne Zufall (sechs mit Zufall) erreichen dort also {_vor_zufall('rr', 0)} die Marke. "
        f"Unter „nur besser“ erreicht von den fünf Regeln nur Q-Lernen die Marke "
        f"({zahl(_z('ob', 'q', 0))}). Bei großem Budget (200·n) erreicht mit der Standardbelohnung keine der {z[('alle', 1)]['zellen']} Zellen "
        f"(fünf Regeln × drei Akzeptanzregeln) die Marke, {z[('alle', 1)]['schlechter']} liegen hinter Zufall. "
        f"Über alle 18 Paare aus Regel und Belohnung sind es bei kleinem Budget {alle[('alle', 0)]['besser']} von 54 Zellen vor und "
        f"{alle[('alle', 0)]['schlechter']} hinter Zufall, bei großem {alle[('alle', 1)]['besser']} vor und {alle[('alle', 1)]['schlechter']} dahinter."
    )


def satz_wirkung() -> str:
    alle = F.zaehlung()
    teile = []
    for akz in C.AKZEPTANZEN:
        teile.append(f"{C.AKZ_KURZ[akz]} {alle[(akz, 0)]['besser']} vor und {alle[(akz, 0)]['schlechter']} hinter Zufall bei kleinem, "
                     f"{alle[(akz, 1)]['besser']} und {alle[(akz, 1)]['schlechter']} bei großem Budget")
    g = F.groesster(j=1)
    return (kernbotschaft() + " Je Akzeptanzregel (18 Paare): " + "; ".join(teile) + ". "
            "Die Zellen mit Vorsprung bei großem Budget liegen knapp an der Marke; bei anderen Bootstrap-Ziehungen sind es drei oder vier. "
            f"Der größte gemessene Vorsprung bei großem Budget (nachträglich unter 54 Zellen gewählt) ist {zahl(g)} "
            f"({C.REGEL_ANZEIGE[g['regel']]}, Belohnung „{C.BELOHNUNG_KURZ[g['belohnung']]}“, "
            f"{C.AKZ_KURZ[g['akz']]}). Der Zufallsgradient ist in allen sechs Zellen nicht von Zufall zu unterscheiden. "
            "Die Zählungen stehen ohne Korrektur für Mehrfachvergleiche, und die Paare sind nicht unabhängig.")


def satz_anteile() -> str:
    def a(akz, regel):
        x, w = F.share("voll", akz, F.key(regel))
        return f"{de(x, 1)} % der Anwendungen ({de(w, 1)} % der Auswertungen)"
    g = F.gleichverteilung()
    ucb = [F.share("voll", akz, "ucb/r2")[0] for akz in C.AKZEPTANZEN]
    return (
        f"**Eingefrorene Messung, Anteil der Zugart `2opt_b5` bis 200·n, Standardbelohnung:** Unter Late Acceptance setzt die Choice Function "
        f"{a('la', 'cf')} auf `2opt_b5`, der Lernautomat {a('la', 'laut')}, Q-Lernen {a('la', 'q')}; bei Gleichverteilung wären es {de(g[0], 1)} % und "
        f"{de(g[1], 1)} %. Unter Rekord-zu-Rekord sind es {a('rr', 'cf')}, {a('rr', 'laut')} und {a('rr', 'q')}, unter „nur besser“ "
        f"{de(F.share('voll', 'ob', 'cf/r2')[0], 1)} %, {de(F.share('voll', 'ob', 'laut/r2')[0], 1)} % und {de(F.share('voll', 'ob', 'q/r2')[0], 1)} % der Anwendungen. "
        f"UCB verteilt unter allen drei Akzeptanzregeln fast gleichmäßig ({de(min(ucb), 1)} bis {de(max(ucb), 1)} % auf `2opt_b5`). "
        "Ein hoher Anteil sagt allein nichts über die Güte: unter Rekord-zu-Rekord setzen Choice Function und Lernautomat ebenfalls rund die Hälfte "
        "und mehr ihrer Anwendungen auf `2opt_b5` und liegen bei kleinem Budget trotzdem vor Zufall (Kernfrage 2)."
    )


def satz_mini() -> str:
    return ("Die Mini-Reihe ist klein: sie trennt nur große Unterschiede, und nicht jeder Ausschnitt von Instanzen zeigt das Vorzeichen der "
            "eingefrorenen Messung. Die Marke 0,25 gehört der eingefrorenen Messung.")


def satz_gutschrift() -> str:
    def g(akz, regel):
        x = F.gutschrift(akz, F.key(regel))
        return f"{de(x['ohne'], 1)} % (W = {de(x['w'])})"

    def anteil(akz, regel):
        return f"{de(F.gutschrift(akz, F.key(regel))['ohne'], 1)} %"
    k2, kb = F.gutschrift_konto("la", "cf/r2")
    return (
        f"**Eingefrorene Messung, bis 200·n, Mittel über 120 Instanzen:** Unter Late Acceptance gehen bei der Zufallswahl {g('la', 'rand')} der "
        f"Standard-Gutschrift an Anwendungen, nach denen der Bestwert nicht fiel, bei der Choice Function {g('la', 'cf')}, beim Lernautomaten "
        f"{g('la', 'laut')}, bei Q-Lernen {g('la', 'q')}, bei UCB {g('la', 'ucb')}. Unter Rekord-zu-Rekord sind es {g('rr', 'rand')} (Zufall) und "
        f"{g('rr', 'cf')} (Choice Function), unter „nur besser“ 0 % mit W = 1 (Kontrolle, als Eigenschaft getestet). "
        f"Bei der Choice Function unter Late Acceptance bekommt `2opt_b5` {de(k2[C.H_2OPT_B5], 1)} % der Standard-Gutschrift und "
        f"{de(kb[C.H_2OPT_B5], 1)} % der Gutschrift nach „nur Bestwert“. Dass die Gutschrift ohne neuen Bestwert den Rückstand verursacht, zeigt diese "
        f"Zählung nicht: auch unter Rekord-zu-Rekord liegt ihr Anteil bei der Choice Function bei {anteil('rr', 'cf')} (Zufall "
        f"{anteil('rr', 'rand')}; unter Late Acceptance {anteil('la', 'cf')} gegen {anteil('la', 'rand')}), "
        "und dort liegt die Regel bei kleinem Budget vorn."
    )


def _kredit_erfuellt(z: dict) -> bool:
    """Vorab-Regel der Kreditzuweisung: Senkung des Anteils und Güte bei beiden Budgets (Intervall über 0)."""
    return z["senkung"] >= C.KREDIT_SENKUNG and all(g["d"] >= C.KREDIT_GUETE and g["lo"] > 0 for g in z["guete"])


def satz_kredit() -> str:
    rows = F.kredit_rows("la")
    teile = []
    for z in rows:
        teile.append(f"{C.REGEL_ANZEIGE[z['regel']]}: Anteil {de(z['anteil_r2'], 1)} → {de(z['anteil_best'], 1)} % (Senkung {de(z['senkung'], 1)} Punkte), "
                     f"Güte {zahl(z['guete'][0])} bei kleinem und {zahl(z['guete'][1])} bei großem Budget, gegen Zufall dann "
                     f"{de(z['zufall_best'][0]['d'], 2, True)} und {de(z['zufall_best'][1]['d'], 2, True)}")
    erfuellt = [z for z in rows if _kredit_erfuellt(z)]
    fehlt = [f"{C.REGEL_ANZEIGE[z['regel']]} (Senkung {de(z['senkung'], 1)} statt mindestens {de(C.KREDIT_SENKUNG, 0)} Punkte)"
             for z in rows if z["senkung"] < C.KREDIT_SENKUNG]
    regel_satz = (
        f"Die Vorab-Regel (Senkung des Anteils um mindestens {de(C.KREDIT_SENKUNG, 0)} Punkte und Güte um mindestens {de(C.KREDIT_GUETE, 1)} Punkte mit "
        f"Intervall über 0 bei beiden Budgets) erfüllen {len(erfuellt)} von {len(rows)} Regeln ({', '.join(C.REGEL_ANZEIGE[z['regel']] for z in erfuellt)})"
        + (f"; es fehlt: {', '.join(fehlt)}. " if fehlt else ". ")
    )
    rr = F.kredit_rows("rr")
    rr_text = "; ".join(f"{C.REGEL_ANZEIGE[z['regel']]} {zahl(z['guete'][0])} und {zahl(z['guete'][1])}" for z in rr)
    return (
        "**Vorab-Regel unter Late Acceptance** (Belohnung „nur Bestwert“ statt Standard; Anteil von `2opt_b5` an den Anwendungen bis 200·n): "
        + ". ".join(teile) + ". "
        + regel_satz +
        f"**Gegenprobe unter Rekord-zu-Rekord:** Dort senkt „nur Bestwert“ den Anteil ebenfalls ({de(rr[0]['anteil_r2'], 1)} → {de(rr[0]['anteil_best'], 1)} % "
        f"bei der Choice Function), die Güte ändert sich aber in keiner der sechs Zellen mit Intervall ohne 0 ({rr_text}). Unter „nur besser“ sind "
        "beide Belohnungen dieselbe (Kontrolle)."
    )


def satz_verduennung() -> str:
    v = F.verduennung()
    return (
        f"**Kontrolle „weniger lernen“ (nur Choice Function, Late Acceptance):** Eine Choice Function mit Standardbelohnung, die in {de(100 * v['p'], 0)} % "
        f"der Anwendungen würfelt statt ihrer Wertung zu folgen, setzt {de(v['anteil'], 1)} % der Anwendungen auf `2opt_b5` (Ziel: die {de(v['ziel'], 1)} % "
        f"der Choice Function mit „nur Bestwert“; die Stärke wurde auf 30 anderen Instanzen gesucht). Ihr Abstand minus der Abstand mit „nur Bestwert“: "
        f"{zahl(v['d'][0])} bei kleinem und {zahl(v['d'][1])} bei großem Budget (negativ: die verdünnte Regel ist besser). Nach der vorab gesetzten "
        f"Marke von {de(C.VERD_MARKE, 1)} Punkten bei großem Budget ist bloßes Verdünnen hier nicht um die Marke schlechter als die andere Belohnung "
        "(Gleichwertigkeit ist damit nicht gezeigt); dass die bessere Gutschrift der Grund der Besserung ist, belegt diese Messung für die Choice Function "
        "nicht. Gegen Zufall liegt die verdünnte Regel bei "
        f"{zahl(v['zufall'][0])} (klein) und {zahl(v['zufall'][1])} (groß)."
    )


def satz_empfindlichkeit() -> str:
    s = {(akz, j): F.empf_summary(akz, j) for akz in C.EMPF_AKZEPTANZEN for j in (0, 1)}
    b = s[("la", 0)]["beste"]
    return (
        f"**Eingefrorene Messung, 20 Varianten je Akzeptanzregel** (je Regel ein Parameter mit zwei Werten neben dem Standard): Unter Late Acceptance "
        f"liegen bei kleinem Budget {s[('la', 0)]['besser']} von 20 Varianten vor und {s[('la', 0)]['schlechter']} hinter Zufall, bei großem "
        f"{s[('la', 1)]['besser']} und {s[('la', 1)]['schlechter']}. Die beste Variante bei kleinem Budget ist {variante_text(b)} mit {zahl(b)}; sie ist "
        f"nachträglich unter 20 gewählt. Unter Rekord-zu-Rekord liegen bei kleinem Budget {s[('rr', 0)]['besser']} von 20 vor Zufall und "
        f"{s[('rr', 0)]['schlechter']} dahinter, bei großem {s[('rr', 1)]['besser']} und {s[('rr', 1)]['schlechter']}. Die Einstellung verschiebt die Zahlen; "
        f"das Vorzeichen folgt bei kleinem Budget der Akzeptanzregel ({s[('la', 0)]['positiv']} bzw. {s[('rr', 0)]['positiv']} von 20 Varianten positiv "
        f"unter Late Acceptance bzw. Rekord-zu-Rekord), bei großem Budget ist es unter Rekord-zu-Rekord gemischt ({s[('rr', 1)]['positiv']} von 20 positiv; "
        f"unter Late Acceptance {s[('la', 1)]['positiv']}). Gemessen sind je Parameter nur drei Werte; für andere Bereiche ist nichts ausgeschlossen."
    )


def preset_erwartung(name: str) -> str:
    """Der Satz der eingefrorenen Zelle im Hilfetext eines Presets."""
    p = C.PRESETS[name]
    x = F.diff(p["akz"], F.key(p["regel"], p["belohnung"]), C.STUFEN.index(p["budget"]), p["menge"])
    wort = {"besser": "vor Zufall", "schlechter": "hinter Zufall", "gleich": "nicht von Zufall zu unterscheiden"}[x["klasse"]]
    return f"Eingefrorene Messung (120 Instanzen × 3 Läufe): {zahl(x)} Prozentpunkte, {wort}."


_PRESET_TEXT = {
    "Rekord-zu-Rekord, kleines Budget": "Voreinstellung: Choice Function mit Standardbelohnung unter Rekord-zu-Rekord, 30 Städte, 50·n Auswertungen.",
    "Late Acceptance: hier verliert Lernen": "Dieselbe Regel, nur die Akzeptanzregel ist Late Acceptance mit einer Liste der Länge 50.",
    "Nur Verbesserungen des Bestwerts belohnen": "Choice Function unter Late Acceptance, belohnt wird nur ein neuer Bestwert; großes Budget.",
    "Großes Budget, „nur besser“": "Q-Lernen unter „nur besser“ bei 200·n Auswertungen.",
    "Der Lernautomat legt sich fest": "Lernautomat unter Late Acceptance bei 200·n: unter den sechs Regeln mit Standardbelohnung der größte Anteil auf einer Zugart.",
    "UCB wählt fast wie Zufall": "UCB unter Late Acceptance bei 200·n: die Anteile bleiben nahe der Gleichverteilung.",
    "Ohne die Zugart 2opt_b5": "Choice Function unter Late Acceptance auf sieben Zugarten, verglichen mit Zufall auf denselben sieben.",
}
for _name, _text in _PRESET_TEXT.items():
    C.PRESET_HELP[_name] = f"{_text} {preset_erwartung(_name)} Die Mini-Reihe mit 24 Instanzen zeigt dieses Ergebnis nicht in jedem Ausschnitt."
