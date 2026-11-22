"""Ein Lauf der Suche mit Auswahlregel, Belohnungsform und Gutschriftkonto. Dünne Komposition: keine eigene Regel.

`Konto` hängt am Haken der Suche (asw_search.run_search: `choose(rng)`, `update(index, delta, kosten, angenommen)`), hält den Zustand der
Auswahlregel, rechnet die Belohnung aus und schreibt mit, wer welche Gutschrift bekommt:

    gut_r2[h], gut_best[h]  Summe der Belohnung der Zugart h nach der Standardform und nach „nur Bestwert“ (beide immer, unabhängig davon,
                            welche Form die Regel liest)
    verbesserung            Summe aller strengen Verbesserungen der aktuellen Tour (jede wird unter ob, rr, la angenommen)
    r2_summe, r2_ohne       Summe der Standard-Gutschrift; davon in Anwendungen, nach denen der Bestwert nicht fiel
    apps[h], evals[h]       Anwendungen und Auswertungen je Zugart; `stand` hält alles je Auswertungs-Kontrollpunkt fest

`run` rechnet einen Lauf mit den festen Zufalls-Seeds der Linie: Startlösung und Zufallsstrom hängen nur an (Familie, n, Instanz, Lauf),
alle Varianten eines Laufs lesen denselben Strom von vorn (gemeinsame Zufallszahlen, wie in hyperheuristik-demo und zugmenge-demo)."""

from functools import lru_cache

import asw_belohnung as B
import asw_constants as C
import asw_regeln as R
import asw_scenario as S
from asw_rngblock import BlockSplitMix64
from asw_search import run_search


class Konto:
    def __init__(self, funktionen, arms, belohnung, cost0: float, kante: float, checkpoints=(), spur: bool = False):
        neu, self._choose, self._update = funktionen
        self.arms = tuple(arms)
        self.state = neu(len(self.arms))
        self.belohnung = belohnung
        self.kante = kante
        self.cost0 = cost0
        self.tracker = B.BestTracker(cost0)
        self.used = 0
        self.apps = [0] * C.K
        self.evals = [0] * C.K
        self.gut_r2 = [0.0] * C.K
        self.gut_best = [0.0] * C.K
        self.verbesserung = 0.0
        self.r2_summe = 0.0
        self.r2_ohne = 0.0
        self.verschlechterungen = 0
        self._ck = sorted(checkpoints)
        self._cki = 0
        self.stand: list[dict] = []
        self.spur = [] if spur else None

    def choose(self, rng) -> int:
        return self._choose(self.state, rng)

    def update(self, index: int, delta: float, kosten: int, angenommen: bool) -> None:
        r = self.belohnung(delta, kosten, angenommen)
        self._update(self.state, index, r)
        h = self.arms[index]
        self.used += kosten
        self.apps[h] += 1
        self.evals[h] += kosten
        r2 = B.reward_r2(delta, kosten, self.kante)
        senkung = self.tracker.senkung(delta, angenommen)
        if r2 > 0.0:
            self.verbesserung -= delta
            self.gut_r2[h] += r2
            self.r2_summe += r2
            if senkung <= 0.0:
                self.r2_ohne += r2
        elif angenommen and delta > C.EPS:
            self.verschlechterungen += 1
        if senkung > 0.0:
            self.gut_best[h] += B.reward_best(senkung, kosten, self.kante)
        if self.spur is not None:
            self.spur.append((h, delta, kosten, angenommen, self.tracker.cost, self.tracker.best, r))
        while self._cki < len(self._ck) and self.used >= self._ck[self._cki]:
            self.stand.append(self.snapshot())
            self._cki += 1

    def snapshot(self) -> dict:
        return dict(apps=list(self.apps), evals=list(self.evals), best=self.tracker.best, verbesserung=self.verbesserung,
                    r2_summe=self.r2_summe, r2_ohne=self.r2_ohne, gut_r2=list(self.gut_r2), gut_best=list(self.gut_best),
                    verschlechterungen=self.verschlechterungen)

    def finish(self) -> None:
        """Füllt Kontrollpunkte auf, die das Budget nicht erreicht hat (wie die Suche)."""
        while self._cki < len(self._ck):
            self.stand.append(self.snapshot())
            self._cki += 1


def arbeit_je_gewinn(verbesserung: float, start: float, best: float) -> float | None:
    """W = Summe der strengen Verbesserungen / (Startlänge - Bestwert); None, wenn der Bestwert nicht fiel."""
    netto = start - best
    return verbesserung / netto if netto > C.EPS else None


def anteil_ohne_bestwert(r2_ohne: float, r2_summe: float) -> float | None:
    """Anteil der Standard-Gutschrift in Anwendungen, nach denen der Bestwert nicht fiel; None ohne jede Gutschrift."""
    return r2_ohne / r2_summe if r2_summe > 0.0 else None


def normalize_set(menge) -> tuple[int, ...]:
    """Zugmenge als sortiertes Tupel ohne Doppelte; leer ist nicht erlaubt."""
    arms = tuple(sorted({int(h) for h in menge}))
    if not arms:
        raise ValueError("Die Zugmenge ist leer: mindestens eine Zugart wählen.")
    if arms[0] < 0 or arms[-1] >= C.K:
        raise ValueError(f"unbekannte Zugart in {arms}")
    return arms


@lru_cache(maxsize=512)
def instance(familie: str, n: int, idx: int):
    return S.make_instance(familie, n, idx)


def run_on(D, t0, rng, regel="rand", akz="rr", belohnung="r2", menge=C.ALLE_ZUGARTEN, budget=None, checkpoints=(), spur=False, wert=None,
           funktionen=None, check=False) -> dict:
    """Ein Lauf auf der Abstandsmatrix D ab der Starttour t0 mit dem Zufallsstrom rng.

    regel: Name aus asw_regeln.REGEL_FUNKTIONEN (rand, rg, cf, ucb, laut, q) oder 'cfv'; wert: der einstellbare Parameter der Regel
    (None = Standard); funktionen: eigenes Tripel (new, choose, update) statt des Namens (Tests). belohnung: Name aus C.BELOHNUNGEN.
    Rückgabe: das dict von run_search, ergänzt um start, arms, konto (das Gutschriftkonto), w, anteil_ohne."""
    n = len(t0)
    arms = normalize_set(menge)
    start = S.tour_cost(D, t0)
    kante = start / n
    budget = C.STUFEN[0] * n if budget is None else budget
    konto = Konto(funktionen or R.regel_funktionen(regel, wert), arms, B.make_reward(belohnung, kante, start), start, kante, checkpoints, spur)
    r = run_search(D, t0, budget, arms, akz, rng, checkpoints=checkpoints, selector=konto, check=check)
    konto.finish()
    r.update(start=start, arms=arms, konto=konto, t0=list(t0), w=arbeit_je_gewinn(konto.verbesserung, start, r["best"]),
             anteil_ohne=anteil_ohne_bestwert(konto.r2_ohne, konto.r2_summe))
    return r


def run(familie, n, idx, lauf, regel="rand", akz="rr", belohnung="r2", menge=C.ALLE_ZUGARTEN, budget=None, checkpoints=(), spur=False,
        wert=None) -> dict:
    """Ein Lauf mit den festen Zufalls-Seeds der Linie (Instanz, Starttour und Strom aus Familie, n, Instanz, Lauf)."""
    _, D = instance(familie, n, idx)
    t0 = S.start_tour(D, familie, n, idx, lauf)
    rng = BlockSplitMix64(S.run_seed(familie, n, idx, lauf))
    return run_on(D, t0, rng, regel, akz, belohnung, menge, budget, checkpoints, spur, wert)


def shares(apps, evals) -> tuple[list[float], list[float]]:
    """Anteile je Zugart an den Anwendungen und an den Auswertungen (Nullen, wenn nichts gezählt ist)."""
    sa = sum(apps)
    se = sum(evals)
    return [a / sa if sa else 0.0 for a in apps], [e / se if se else 0.0 for e in evals]
