"""Belohnungsformen: was eine Auswahlregel nach einer Anwendung als Erfolg gutgeschrieben bekommt (Quelle für die Folge-Demo der Linie).

Reine Formeln (`reward_*`) und je Form ein Objekt mit dem Aufruf `(delta, kosten, angenommen) -> Belohnung in [0, 1]`, wie ihn
asw_select.Selector und asw_algorithm.Konto erwarten. `kante` = Länge der Starttour / n (mittlere Kantenlänge), `kosten` = Auswertungen
der Anwendung. Eine strenge Verbesserung ist delta < -1e-9; sie wird unter allen drei Akzeptanzregeln der Demo angenommen.

    r2    Verbesserung der aktuellen Tour je Auswertung (Standard, dieselbe Formel wie asw_select.reward_standard)
    best  Senkung des Bestwerts je Auswertung (0, wenn die Anwendung keinen neuen Bestwert bringt)
    r1    Verbesserung der aktuellen Tour ohne Kostenbezug
    rank  Anteil der letzten 30 Werte von r2 (alle Anwendungen, auch die mit 0), die kleiner sind; 0 ohne Verbesserung
    ma    r2 geteilt durch das gleitende Mittel der positiven r2 (Glättung 0,05), höchstens 1; 0 ohne Verbesserung"""

import asw_constants as C

EPS = C.EPS


def reward_r2(delta: float, kosten: int, kante: float) -> float:
    if delta >= -EPS:
        return 0.0
    r = -delta / (kosten * kante)
    return 1.0 if r > 1.0 else r


def reward_r1(delta: float, kante: float) -> float:
    if delta >= -EPS:
        return 0.0
    r = -delta / kante
    return 1.0 if r > 1.0 else r


def reward_best(senkung: float, kosten: int, kante: float) -> float:
    """`senkung` = Bestwert vorher minus Bestwert nachher (0 ohne neuen Bestwert)."""
    if senkung <= 0.0:
        return 0.0
    r = senkung / (kosten * kante)
    return 1.0 if r > 1.0 else r


def reward_rank(r2: float, fenster: list[float], laenge: int = C.RANK_FENSTER) -> float:
    """Anteil der Fensterwerte unter r2, bezogen auf die volle Fensterlänge (auch solange das Fenster noch nicht gefüllt ist)."""
    if r2 <= 0.0:
        return 0.0
    return sum(1 for v in fenster if v < r2) / float(laenge)


def reward_ma(r2: float, mittel: float) -> float:
    """r2 relativ zum gleitenden Mittel `mittel` (schon mit diesem r2 fortgeschrieben), höchstens 1."""
    if r2 <= 0.0:
        return 0.0
    r = r2 / mittel
    return 1.0 if r > 1.0 else r


class BestTracker:
    """Rechnet aus den Meldungen der Suche die Länge der aktuellen Tour und den Bestwert nach (dieselbe Arithmetik wie asw_search)."""

    def __init__(self, cost0: float):
        self.cost = cost0
        self.best = cost0

    def senkung(self, delta: float, angenommen: bool) -> float:
        """Senkung des Bestwerts durch diese Anwendung (0, wenn keiner fällt); schreibt Länge und Bestwert fort."""
        if not angenommen:
            return 0.0
        am_bestwert = self.cost == self.best                  # die aktuelle Tour ist die beste: die Senkung ist genau -delta
        self.cost = self.cost + delta
        if self.cost < self.best - 1e-12:
            s = -delta if am_bestwert else self.best - self.cost
            self.best = self.cost
            return s
        return 0.0


class Belohnung:
    """Eine Belohnungsform mit ihrem Gedächtnis (Bestwert, Fenster, gleitendes Mittel). Aufruf: (delta, kosten, angenommen) -> [0, 1]."""

    def __init__(self, form: str, kante: float, cost0: float):
        if form not in C.BELOHNUNGEN:
            raise ValueError(f"unbekannte Belohnungsform {form!r}")
        self.form = form
        self.kante = kante
        self.tracker = BestTracker(cost0)
        self.fenster: list[float] = []
        self.mittel = 0.0

    def __call__(self, delta: float, kosten: int, angenommen: bool) -> float:
        form = self.form
        if form == "r2":
            return reward_r2(delta, kosten, self.kante)
        if form == "best":
            return reward_best(self.tracker.senkung(delta, angenommen), kosten, self.kante)
        if form == "r1":
            return reward_r1(delta, self.kante)
        r2 = reward_r2(delta, kosten, self.kante)
        if form == "rank":
            r = reward_rank(r2, self.fenster)
            self.fenster.append(r2)
            if len(self.fenster) > C.RANK_FENSTER:
                self.fenster.pop(0)
            return r
        if r2 > 0.0:                                              # ma
            self.mittel = r2 if self.mittel == 0.0 else self.mittel + C.MA_ALPHA * (r2 - self.mittel)
        return reward_ma(r2, self.mittel)


def make_reward(form: str, kante: float, cost0: float) -> Belohnung:
    """Belohnungsobjekt für einen Lauf: `kante` = cost0 / n, `cost0` = Länge der Starttour."""
    return Belohnung(form, kante, cost0)
