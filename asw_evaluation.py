"""Auswertung: die Mini-Messreihe (Regel gegen Zufall, gepaart) und alle Verdikte der App als reine Funktionen `verdict_*(...) -> (Art, Text)`.

Die App ruft `getattr(st, Art)(Text)`. Jede Zahl in einem Verdikt ist ein Argument (aus einer Rechnung oder der eingefrorenen Messung),
nie von Hand im Text. Die Schwellen stehen in asw_constants und sind gesetzt, nicht abgeleitet."""

import asw_algorithm as A
import asw_constants as C
import asw_stats as ST


def de(x: float, stellen: int = 2, vz: bool = False) -> str:
    """Zahl mit Dezimalkomma; vz = Vorzeichen immer zeigen (Minuszeichen als U+2212)."""
    s = f"{x:+.{stellen}f}" if vz else f"{x:.{stellen}f}"
    return s.replace(".", ",").replace("-", "−")


def tsd(n: int) -> str:
    """Ganze Zahl mit schmalen Tausendergruppen: 600000 -> '600 000' (nur die Zahl, nie ein ganzer Satz)."""
    return f"{n:,}".replace(",", " ")


def intervall(lo: float, hi: float, stellen: int = 2) -> str:
    return f"[{de(lo, stellen, True)}; {de(hi, stellen, True)}]"


# ---------------------------------------------------------------- Mini-Messreihe
def mini_kosten(instanzen: int, laeufe: int, n: int, faktor: int) -> int:
    """Auswertungen einer Mini-Messreihe: zwei Regeln (die gewählte und Zufall) x Instanzen x Läufe x Budget."""
    return 2 * instanzen * laeufe * faktor * n


def mini_erlaubt(instanzen: int, laeufe: int, n: int, faktor: int) -> bool:
    return mini_kosten(instanzen, laeufe, n, faktor) <= C.RECHENGRENZE


def mini_indices(start: int, m: int) -> list[int]:
    """Instanzen der Mini-Reihe: m aufeinanderfolgende ab `start`, im Bereich der vorgerechneten Referenzwerte (0 bis 199) umlaufend."""
    return [(start + j) % C.INSTANZEN_REF for j in range(m)]


def mini_reihe(referenz, familie: str, n: int, start: int, m: int, laeufe: int, regel: str, akz: str, belohnung: str, menge, faktor: int,
               wert=None) -> dict:
    """Regel gegen Zufall auf denselben Instanzen, Starttouren und Zufallsströmen (gepaart).

    referenz: Funktion (familie, n, idx) -> bester bekannter Wert oder None. Je Instanz gilt das Minimum aus diesem Wert und den Läufen der
    Reihe. Rückgabe: d je Instanz (Abstand Zufall minus Abstand Regel, Mittel über die Läufe), Mittel, Intervall, Halbbreite, Kosten."""
    budget = faktor * n
    d = []
    kosten = 0
    abstand = [0.0, 0.0]
    for idx in mini_indices(start, m):
        zufall = [A.run(familie, n, idx, lauf, "rand", akz, "r2", menge, budget) for lauf in range(laeufe)]
        gelernt = [A.run(familie, n, idx, lauf, regel, akz, belohnung, menge, budget, wert=wert) for lauf in range(laeufe)]
        kosten += sum(r["used"] for r in zufall) + sum(r["used"] for r in gelernt)
        ref = referenz(familie, n, idx)
        kleinste = min(r["best"] for r in zufall + gelernt)
        ref = kleinste if ref is None or kleinste < ref else ref
        gz = ST.mean(ST.gap(r["best"], ref) for r in zufall)
        gr = ST.mean(ST.gap(r["best"], ref) for r in gelernt)
        abstand[0] += gz / m
        abstand[1] += gr / m
        d.append(gz - gr)
    ci = ST.bootstrap_ci(d, C.ZWECK_BOOT)
    mittel = ST.mean(d)
    lo, hi = ci if ci else (mittel, mittel)
    return dict(d=mittel, lo=lo, hi=hi, halbbreite=(hi - lo) / 2.0, je_instanz=d, m=m, laeufe=laeufe, kosten=kosten, abstand_zufall=abstand[0],
                abstand_regel=abstand[1])


def urteil_unterschied(d: float, lo: float, hi: float) -> str:
    """'besser' ab d >= 0,25 mit Intervall über 0; 'schlechter' ab d <= -0,10 mit Intervall unter 0; sonst 'gleich'."""
    if d >= C.MARKE_KLAR and lo > 0:
        return "besser"
    if d <= -C.MARKE_GLEICH and hi < 0:
        return "schlechter"
    return "gleich"


# ---------------------------------------------------------------- Verdikte
def verdict_anteil(regel: str, zugart: str, anteil: float, anteil_ausw: float, erwartet: float, erwartet_ausw: float) -> tuple[str, str]:
    """Anteile in Prozent. Ab 50 % 'legt sich fest' (warning), ab 25 % 'bevorzugt' (info), darunter 'verteilt fast gleichmäßig' (info)."""
    zahlen = (f"{de(anteil, 1)} % der Anwendungen und {de(anteil_ausw, 1)} % der Auswertungen gehen an `{zugart}`; bei Gleichverteilung wären es "
              f"{de(erwartet, 1)} % und {de(erwartet_ausw, 1)} %.")
    if anteil >= 100 * C.ANTEIL_FEST:
        return "warning", (f"{regel} legt sich in diesem Lauf fest: {zahlen} Ob die Festlegung der Suche nützt, zeigt erst der Vergleich mit "
                           "Zufall (Kernfrage 2).")
    if anteil >= 100 * C.ANTEIL_BEVORZUGT:
        return "info", f"{regel} bevorzugt in diesem Lauf eine Zugart: {zahlen}"
    return "info", (f"{regel} verteilt in diesem Lauf fast gleichmäßig: die häufigste Zugart ist `{zugart}` mit {de(anteil, 1)} % der Anwendungen "
                    f"(Gleichverteilung {de(erwartet, 1)} %) und {de(anteil_ausw, 1)} % der Auswertungen.")


def verdict_zelle(regel: str, belohnung: str, akz: str, stufe: str, d: float, lo: float, hi: float, instanzen: int, laeufe: int) -> tuple[str, str]:
    """Die eingefrorene Zelle (Regel, Belohnung, Akzeptanz, Budget) gegen Zufall."""
    kopf = (f"Eingefrorene Messung ({instanzen} Instanzen × {laeufe} Läufe, Zähleinheit Auswertungen): {regel} mit der Belohnung „{belohnung}“ "
            f"unter {akz} bei Budget {stufe}")
    k = urteil_unterschied(d, lo, hi)
    if k == "besser":
        return "success", f"{kopf} liegt {de(d)} Prozentpunkte vor Zufall {intervall(lo, hi)}."
    if k == "schlechter":
        return "warning", f"{kopf} liegt {de(-d)} Prozentpunkte hinter Zufall {intervall(lo, hi)}."
    return "info", f"{kopf} ist von Zufall nicht zu unterscheiden (Unterschied {de(d, 2, True)} {intervall(lo, hi)}, Marke 0,25 mit Intervall ohne 0)."


def verdict_vergleich(regel: str, akz: str, stufe: str, d: float, lo: float, hi: float, instanzen: int, laeufe: int) -> tuple[str, str]:
    """Die Mini-Messreihe: Regel gegen Zufall, gepaart über die Instanzen."""
    kopf = f"In dieser Mini-Reihe ({instanzen} Instanzen × {laeufe} Läufe, Zähleinheit Auswertungen) liegt {regel} unter {akz} bei Budget {stufe}"
    if instanzen < C.MIN_INSTANZEN:
        return "info", f"Mit {instanzen} Instanzen gibt es kein Urteil (mindestens {C.MIN_INSTANZEN})."
    k = urteil_unterschied(d, lo, hi)
    if k == "besser":
        return "success", f"{kopf} {de(d)} Prozentpunkte vor Zufall {intervall(lo, hi)} (Abstand zum besten bekannten Wert)."
    if k == "schlechter":
        return "warning", f"{kopf} {de(-d)} Prozentpunkte hinter Zufall {intervall(lo, hi)} (Abstand zum besten bekannten Wert)."
    return "info", (f"In dieser Mini-Reihe ({instanzen} Instanzen × {laeufe} Läufe) ist {regel} unter {akz} bei Budget {stufe} nicht von Zufall zu "
                    f"unterscheiden (Unterschied {de(d, 2, True)} {intervall(lo, hi)}). Diese Reihe trennt Unterschiede unter etwa "
                    f"{de((hi - lo) / 2.0)} Prozentpunkten nicht; die eingefrorene Messung hat die Marke 0,25.")


def verdict_gutschrift(akz: str, anteil_ohne: float | None, w: float | None) -> tuple[str, str]:
    """Kennzahlen dieses einen Laufs: Anteil der Standard-Gutschrift (0 bis 1) in Anwendungen ohne neuen Bestwert, W = Arbeit je Nettogewinn."""
    if anteil_ohne is None or w is None:
        return "info", "In diesem Lauf gab es keine einzige Verbesserung: es wurde keine Gutschrift vergeben, die Kennzahlen sind nicht definiert."
    if akz == "ob":
        return "info", (f"Kontrolle: unter „nur besser“ ist jede Verbesserung zugleich ein neuer Bestwert. Anteil der Gutschrift ohne neuen "
                        f"Bestwert in diesem Lauf: {de(100 * anteil_ohne, 1)} %, Verbesserungsarbeit je Nettogewinn W = {de(w)}.")
    zahlen = (f"{de(100 * anteil_ohne, 1)} % der Standard-Gutschrift dieses Laufs gingen an Anwendungen, nach denen der Bestwert nicht fiel; die "
              f"Summe aller Verbesserungen ist das {de(w)}-Fache des Nettogewinns (W).")
    if anteil_ohne >= C.GUTSCHRIFT_VIEL:
        return "warning", "Mehr als die Hälfte der Gutschrift belohnt hier keine neue Bestleistung: " + zahlen
    if anteil_ohne >= C.GUTSCHRIFT_TEIL:
        return "info", "Ein Teil der Gutschrift belohnt hier keine neue Bestleistung: " + zahlen
    return "success", "Kaum Gutschrift ohne neue Bestleistung: " + zahlen


def urteil_kredit(zeilen) -> str:
    """Vorab-Regel: 'gestützt', wenn mindestens zwei der drei Regeln beide Bedingungen erfüllen, 'teilweise' bei einer, sonst 'nicht gestützt'."""
    k = sum(1 for z in zeilen if z["bed_a"] and z["bed_b"])
    return "gestützt" if k >= 2 else ("teilweise" if k == 1 else "nicht gestützt")


def urteil_verduennung(d: float, lo: float, anteil: float, ziel: float) -> str:
    """Kontrolle „weniger lernen“ bei großem Budget. d = Abstand(verdünnt) - Abstand(nur Bestwert) mit unterer Intervallgrenze lo; Anteile in Prozent.

    'nicht vergleichbar', wenn die verdünnte Regel den Zielanteil um mehr als 2 Prozentpunkte verfehlt; 'gutschrift', wenn sie mindestens
    0,3 Punkte schlechter ist (Intervall über 0); 'weniger lernen', wenn der Abstand unter 0,3 liegt oder sie besser ist; sonst 'nicht getrennt'."""
    if abs(anteil - ziel) > C.VERD_BAND:
        return "nicht vergleichbar"
    if d >= C.VERD_MARKE:
        return "gutschrift" if lo > 0 else "nicht getrennt"
    return "weniger lernen"


_VERD_SATZ = {
    "gutschrift": "Die Kontrolle spricht für die Gutschrift: eine Choice Function, die nur seltener ihrer Wertung folgt, ist schlechter als die mit der anderen Belohnung",
    "weniger lernen": "Die Kontrolle spricht für „weniger lernen“: eine Choice Function, die nur seltener ihrer Wertung folgt, ist nicht um die Marke schlechter als die mit der anderen Belohnung (Gleichwertigkeit ist damit nicht gezeigt)",
    "nicht getrennt": "Gutschrift und „weniger lernen“ sind nicht getrennt: der Abstand der Kontrolle erreicht die Marke, sein Intervall enthält aber die 0",
    "nicht vergleichbar": "Gutschrift und „weniger lernen“ sind nicht getrennt: die Kontrolle hat den Zielanteil nicht getroffen",
}


def verdict_kredit(zeilen, verd_urteil: str, verd_d: float, verd_lo: float, verd_hi: float, akz: str = "Late Acceptance") -> tuple[str, str]:
    """Kreditregel über die drei Regeln (zeilen: je Regel senkung, guete[2] mit d, lo; bed_a, bed_b; zufall_best[2] mit d, klasse) und die Kontrolle."""
    urteil = urteil_kredit(zeilen)
    k = sum(1 for z in zeilen if z["bed_a"] and z["bed_b"])
    ka = sum(1 for z in zeilen if z["bed_a"])
    kb = sum(1 for z in zeilen if z["bed_b"])
    vorn = sum(1 for z in zeilen for x in z["zufall_best"] if x["klasse"] == "besser")
    hinten = sum(1 for z in zeilen for x in z["zufall_best"] if x["klasse"] == "schlechter")
    zufall = (f"Gegen Zufall bleibt mit dieser Belohnung in {hinten} von {2 * len(zeilen)} Zellen (Regel × Budget) ein Rückstand, in {vorn} ein "
              "Vorsprung über der Marke.")
    kontrolle = f"{_VERD_SATZ[verd_urteil]} (Unterschied bei großem Budget {de(verd_d, 2, True)} {intervall(verd_lo, verd_hi)})."
    kopf = (f"Unter {akz} erfüllen {k} von {len(zeilen)} Regeln beide Bedingungen der Vorab-Regel (Anteil von `2opt_b5` sinkt um mindestens "
            f"{de(C.KREDIT_SENKUNG, 0)} Prozentpunkte: {ka} von {len(zeilen)}; Güte bei beiden Budgets mindestens {de(C.KREDIT_GUETE, 1)} Punkte besser mit "
            f"Intervall über 0: {kb} von {len(zeilen)}).")
    if urteil == "gestützt":
        return "success", f"Die Belohnung „nur Bestwert“ wirkt so, wie die Vorab-Regel es verlangt. {kopf} {zufall} {kontrolle}"
    if urteil == "teilweise":
        return "info", f"Die Gutschrift ist nur teilweise gestützt. {kopf} {zufall} {kontrolle}"
    return "info", f"Die Belohnung ändert hier nicht beides in dem Maß der Vorab-Regel. {kopf} {zufall} {kontrolle}"


def verdict_einstellung(akz: str, stufe: str, varianten: int, besser: int, schlechter: int, name: str, d: float, lo: float, hi: float) -> tuple[str, str]:
    """Empfindlichkeit: Zählung über die Varianten und die nachträglich beste."""
    beste = (f"Beste Variante (nachträglich auf denselben Instanzen gewählt, also optimistisch): {name} mit {de(d, 2, True)} {intervall(lo, hi)}.")
    zaehl = f"{besser} von {varianten} Varianten liegen unter {akz} bei Budget {stufe} vor Zufall (Marke 0,25 mit Intervall über 0), {schlechter} dahinter."
    if besser == 0:
        return "warning", f"Keine andere Einstellung dreht das Bild: {zaehl} {beste}"
    return "info", f"Die Einstellung verschiebt die Zahlen; welche Richtung vorherrscht, hängt an der Akzeptanzregel und am Budget: {zaehl} {beste}"


def verdict_ohne_b5(akz: str, stufe: str, zeilen) -> tuple[str, str]:
    """Gegenzeile „ohne 2opt_b5“: zeilen = [(Regelname, d, lo, hi, klasse)] gegen Zufall auf derselben Menge."""
    teile = "; ".join(f"{name} {de(d, 2, True)} {intervall(lo, hi)}" for name, d, lo, hi, _ in zeilen)
    vorn = sum(1 for z in zeilen if z[4] == "besser")
    hinten = sum(1 for z in zeilen if z[4] == "schlechter")
    return "info", (f"Ohne die Zugart `2opt_b5` unter {akz} bei Budget {stufe}: {teile}. Das sind {vorn} von {len(zeilen)} Regeln vor und "
                    f"{hinten} hinter Zufall. Die Mengen selbst vergleicht die Demo „Die Zugmenge entscheidet“.")
