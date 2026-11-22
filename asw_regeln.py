"""Auswahlregeln dieser Demo, ergänzend zur Kopie asw_select (Zufall, Choice Function, Lernautomat, Q-Lernen): Zufallsgradient, UCB mit
Vergessen, die verdünnte Choice Function (Kontrollregel) und Fassungen mit einstellbarem Parameter (Quelle für die Folge-Demo der Linie).

Schnittstelle wie in asw_select: je Regel drei reine Funktionen über einem ausdrücklich übergebenen Zustand (dict),
    new(m) -> state,  choose(state, rng) -> arm,  update(state, arm, reward) -> None.
Arme sind die Positionen 0 bis m - 1 in der sortierten Zugmenge. Zufall nur über rng.random(). „Erfolg“ heißt reward > 0.

`regel_funktionen(regel, **parameter)` liefert das Tripel (new, choose, update); ohne Parameter für cf, laut, q genau die Funktionen der
Kopie. Die Fassungen mit Parameter rechnen mit den Standardwerten bitgleich zur Kopie (tests/test_regeln.py)."""

import math
from functools import lru_cache

import asw_constants as C
import asw_select as SE
from asw_rng import exact_log


# ---------------------------------------------------------------- Zufallsgradient
def new_rg(m: int) -> dict:
    return {"m": m, "arm": -1, "erfolg": False}


def choose_rg(state: dict, rng) -> int:
    """Dieselbe Zugart wie zuletzt, solange deren letzte Anwendung ein Erfolg war; sonst (und am Anfang) gleichverteilt neu (eine Zufallszahl)."""
    if state["erfolg"]:
        return state["arm"]
    m = state["m"]
    return 0 if m == 1 else int(rng.random() * m)


def update_rg(state: dict, arm: int, reward: float) -> None:
    state["arm"] = arm
    state["erfolg"] = reward > 0.0


# ---------------------------------------------------------------- UCB mit Vergessen
@lru_cache(maxsize=None)
def log_wirksame_anzahl(t: int, gamma: float) -> float:
    """ln N_t mit N_t = 1 + gamma + ... + gamma^(t-1), der wirksamen Zahl der Anwendungen nach t Schritten; 0 für N_t <= 1.

    N_t hängt nur am Schritt, nicht an den Entscheidungen: die Werte werden je Schritt einmal mit dem plattformfesten Logarithmus der
    Zufallsvorlage gerechnet (math.log käme aus der C-Bibliothek und könnte Gleichstände je Plattform anders auflösen)."""
    if t <= 1:
        return 0.0
    nt = float(t) if gamma == 1.0 else (1.0 - gamma ** t) / (1.0 - gamma)
    return exact_log(nt) if nt > 1.0 else 0.0


def new_ucb(m: int, c: float = C.UCB_C, gamma: float = C.UCB_GAMMA) -> dict:
    """n, s: mit dem Gewicht w gezählte Anwendungen und Belohnungssummen je Arm (w wächst je Schritt um 1 / gamma: ältere zählen weniger);
    rmax: größte bisherige Belohnung (normiert den Mittelwert); t: Schritte."""
    return {"m": m, "n": [0.0] * m, "s": [0.0] * m, "w": 1.0, "rmax": 1e-12, "t": 0, "c": c, "gamma": gamma}


def ucb_index(state: dict) -> list[float]:
    """Index je Arm: s_j / (n_j * rmax) + c * sqrt(2 ln N / (n_j / w)); nur definiert, wenn jeder Arm mindestens einmal gewählt wurde."""
    lg = log_wirksame_anzahl(state["t"], state["gamma"])
    w = state["w"]
    c = state["c"]
    rmax = state["rmax"]
    return [s / nj / rmax + c * math.sqrt(2.0 * lg * w / nj) for s, nj in zip(state["s"], state["n"])]


def choose_ucb(state: dict, rng) -> int:
    """Erst jeden Arm einmal (gleichverteilt unter den noch nicht gewählten, eine Zufallszahl), danach der Arm mit dem größten Index;
    bei gleichem Index gewinnt der kleinere Arm (keine Zufallszahl)."""
    n = state["n"]
    offen = [j for j in range(state["m"]) if n[j] == 0.0]
    if offen:
        return offen[int(rng.random() * len(offen))]
    index = ucb_index(state)
    arm = 0
    best = index[0]
    for j in range(1, state["m"]):
        if index[j] > best:
            best = index[j]
            arm = j
    return arm


def update_ucb(state: dict, arm: int, reward: float) -> None:
    state["w"] /= state["gamma"]
    w = state["w"]
    state["n"][arm] += w
    state["s"][arm] += reward * w
    if reward > state["rmax"]:
        state["rmax"] = reward
    state["t"] += 1


# ---------------------------------------------------------------- Fassungen mit Parameter (Choice Function, Lernautomat, Q-Lernen)
def cf_scores(state: dict) -> list[float]:
    """Wertung der Choice Function je Arm ohne das Rauschen: phi * (f1 / max f1 + f2[Vorgänger] / max f2[Vorgänger]) + (1 - phi) * min(Wartezeit, 50) / 50."""
    m = state["m"]
    f1 = state["f1"]
    phi = state["phi"]
    prev = state["prev"]
    m1 = max(f1) + 1e-12
    werte = []
    for j in range(m):
        s = phi * (f1[j] / m1 + (state["f2"][prev][j] / (max(state["f2"][prev]) + 1e-12) if prev >= 0 else 0.0))
        dt = state["step"] - state["last"][j]
        werte.append(s + (1.0 - phi) * min(dt, C.CF_ZEITFENSTER) / C.CF_ZEITFENSTER)
    return werte


def _cf_mit(alpha: float):
    def update(state, arm, reward):
        state["step"] += 1
        f1 = state["f1"]
        f1[arm] = reward + alpha * f1[arm]
        prev = state["prev"]
        if prev >= 0:
            row = state["f2"][prev]
            row[arm] = reward + alpha * row[arm]
        state["last"][arm] = state["step"]
        if reward > 0.0:
            state["phi"] = C.CF_PHI_ERFOLG
        else:
            phi = state["phi"] - C.CF_PHI_SCHRITT
            state["phi"] = phi if phi > C.CF_PHI_MIN else C.CF_PHI_MIN
        state["prev"] = arm
    return SE.new_cf, SE.choose_cf, update


def _laut_mit(a: float):
    def update(state, arm, reward):
        if reward <= 0.0:
            return
        p = state["p"]
        m = state["m"]
        for j in range(m):
            p[j] *= 1.0 - a
        p[arm] += a
        tot = 0.0
        for j in range(m):
            if p[j] < C.LAUT_BODEN:
                p[j] = C.LAUT_BODEN
            tot += p[j]
        for j in range(m):
            p[j] /= tot
    return SE.new_laut, SE.choose_laut, update


def _q_mit(alpha: float):
    def update(state, arm, reward):
        q = state["q"]
        q[arm] += alpha * (reward + C.Q_GAMMA * max(q) - q[arm])
    return SE.new_q, SE.choose_q, update


def _ucb_mit(c: float):
    def neu(m):
        return new_ucb(m, c=c)
    return neu, choose_ucb, update_ucb


# ---------------------------------------------------------------- verdünnte Choice Function (Kontrollregel „weniger lernen“)
def _cfv_mit(p: float):
    """Mit Wahrscheinlichkeit p gleichverteilt (zwei Zufallszahlen), sonst die Wahl der Choice Function (eine Zufallszahl mehr als sie);
    gelernt wird aus jeder Anwendung."""
    def choose(state, rng):
        if rng.random() < p:
            return int(rng.random() * state["m"])
        return SE.choose_cf(state, rng)
    return SE.new_cf, choose, SE.update_cf


# ---------------------------------------------------------------- Tabelle
REGEL_FUNKTIONEN = dict(SE.REGEL_FUNKTIONEN)
REGEL_FUNKTIONEN.update({"rg": (new_rg, choose_rg, update_rg), "ucb": (new_ucb, choose_ucb, update_ucb)})
_MIT_PARAMETER = {"cf": _cf_mit, "laut": _laut_mit, "q": _q_mit, "ucb": _ucb_mit, "cfv": _cfv_mit}


def regel_funktionen(regel: str, wert: float | None = None):
    """Tripel (new, choose, update) der Regel; `wert` setzt den einen einstellbaren Parameter (asw_constants.PARAMETER: cf alpha, ucb c,
    laut a, q alpha; cfv: Verdünnung p). Ohne `wert` die Standardfassung."""
    if wert is None:
        return REGEL_FUNKTIONEN[regel]
    return _MIT_PARAMETER[regel](wert)


def parameter_wert(regel: str, einstellung: str) -> float | None:
    """Parameterwert zur Einstellung 'standard' (None: Standardfassung), 'niedrig' oder 'hoch'; Regeln ohne Parameter geben None."""
    if einstellung == "standard" or regel not in C.PARAMETER:
        return None
    _, _, niedrig, hoch = C.PARAMETER[regel]
    return niedrig if einstellung == "niedrig" else hoch
