"""Zugriff auf die eingefrorene Messung asw_frozen.json (erzeugt von tools/asw_make_frozen.py) und alle Zählungen, die App und README nennen.

Vorzeichen: Unterschied d = Abstand(Zufall) - Abstand(Regel) je Instanz, positiv heißt: die Regel ist besser als die Zufallswahl.
Abstand = Prozent über dem besten bekannten Wert der Instanz, Mittel über die Läufe. Stufe j: 0 = klein (50·n), 1 = groß (200·n).
Intervall: Bootstrap 95 % über die Instanzen (asw_stats.bootstrap_ci, fester Zufalls-Seed)."""

import json
from functools import lru_cache
from pathlib import Path

import asw_constants as C
import asw_stats as ST

ORDNER = Path(__file__).resolve().parent
ZUFALL = "rand/r2"


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads((ORDNER / "asw_frozen.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_refs() -> dict:
    return json.loads((ORDNER / "asw_refs.json").read_text(encoding="utf-8"))


def meta() -> dict:
    return load()["meta"]


def key(regel: str, belohnung: str = "r2") -> str:
    return f"{regel}/{belohnung}"


def gaps(block: str, akz: str, schluessel: str, j: int) -> list[float]:
    """Abstände je Instanz (120) an der Stufe j."""
    return [zeile[j] for zeile in load()["gap"][block][akz][schluessel]]


def mean_gap(block: str, akz: str, schluessel: str, j: int) -> float:
    return ST.mean(gaps(block, akz, schluessel, j))


def klasse(d: float, lo: float, hi: float) -> str:
    """'besser' ab d >= 0,25 mit Intervall über 0; 'schlechter' ab d <= -0,10 mit Intervall unter 0; sonst 'gleich' (Marken gesetzt)."""
    if d >= C.MARKE_KLAR and lo > 0:
        return "besser"
    if d <= -C.MARKE_GLEICH and hi < 0:
        return "schlechter"
    return "gleich"


def vergleich(a: list[float], b: list[float]) -> dict:
    """Gepaarter Unterschied a - b je Instanz: Mittel, Intervall, Klasse, Zahl der Instanzen mit a > b."""
    d = [x - y for x, y in zip(a, b, strict=True)]
    m = ST.mean(d)
    lo, hi = ST.bootstrap_ci(d, C.ZWECK_BOOT)
    return dict(d=m, lo=lo, hi=hi, klasse=klasse(m, lo, hi), vorn=sum(1 for x in d if x > 0), m=len(d))


@lru_cache(maxsize=None)
def diff(akz: str, schluessel: str, j: int, block: str = "voll") -> dict:
    """Zufall minus Regel auf derselben Zugmenge (block 'voll' oder 'ohne_2opt_b5'; 'empf' und 'verd' gegen Zufall auf der vollen Menge)."""
    basis = block if block in ("voll", "ohne_2opt_b5") else "voll"
    return vergleich(gaps(basis, akz, ZUFALL, j), gaps(block, akz, schluessel, j))


@lru_cache(maxsize=None)
def guete(akz: str, regel: str, j: int, von: str = "r2", nach: str = "best") -> dict:
    """Wirkung des Wechsels der Belohnungsform: Abstand(von) - Abstand(nach), positiv heißt: `nach` ist besser."""
    return vergleich(gaps("voll", akz, key(regel, von), j), gaps("voll", akz, key(regel, nach), j))


# ---------------------------------------------------------------- Anteile
def counts(block: str, akz: str, schluessel: str, j: int) -> tuple[list[int], list[int]]:
    z = load()["zaehler"][block][akz][schluessel]
    return z["apps"][j], z["evals"][j]


def share(block: str, akz: str, schluessel: str, j: int = 1, h: int = C.H_2OPT_B5) -> tuple[float, float]:
    """Anteil der Zugart h (Standard 2opt_b5) an den Anwendungen und an den Auswertungen, in Prozent (Summe über alle Läufe)."""
    apps, evals = counts(block, akz, schluessel, j)
    return 100.0 * apps[h] / sum(apps), 100.0 * evals[h] / sum(evals)


def shares(block: str, akz: str, schluessel: str, j: int = 1) -> list[float]:
    """Anteil je Zugart an den Anwendungen in Prozent."""
    apps, _ = counts(block, akz, schluessel, j)
    s = sum(apps)
    return [100.0 * a / s for a in apps]


def top_share(block: str, akz: str, schluessel: str, j: int = 1) -> tuple[int, float]:
    """Die Zugart mit dem größten Anteil der Anwendungen und dieser Anteil in Prozent."""
    s = shares(block, akz, schluessel, j)
    h = max(range(C.K), key=lambda x: s[x])
    return h, s[h]


def gleichverteilung(m: int = C.K, mit_b5: bool = True) -> tuple[float, float]:
    """Anteil einer Zugart bei Gleichverteilung über m Zugarten: an den Anwendungen 1 / m; an den Auswertungen für 2opt_b5 5 / (m + 4)."""
    return 100.0 / m, (100.0 * 5 / (m + 4) if mit_b5 else 100.0 / m)


# ---------------------------------------------------------------- Wirkungstabelle und Zählungen
def wirkung_rows(paare=C.PAARE, block: str = "voll") -> list[dict]:
    """Je Paar (Regel, Belohnung) und Akzeptanz die Unterschiede bei kleinem und großem Budget."""
    rows = []
    for regel, bel in paare:
        for akz in C.AKZEPTANZEN:
            rows.append(dict(regel=regel, belohnung=bel, akz=akz, lo=diff(akz, key(regel, bel), 0, block), hi=diff(akz, key(regel, bel), 1, block)))
    return rows


def zaehlung(paare=C.PAARE, akzeptanzen=C.AKZEPTANZEN) -> dict:
    """Zahl der Zellen je Klasse: {(akz, j): {'besser': k, 'gleich': k, 'schlechter': k, 'zellen': m}} und die Summen je Stufe unter 'alle'."""
    aus = {}
    for j in range(len(C.STUFEN)):
        summe = dict(besser=0, gleich=0, schlechter=0, zellen=0)
        for akz in akzeptanzen:
            z = dict(besser=0, gleich=0, schlechter=0, zellen=0)
            for regel, bel in paare:
                z[diff(akz, key(regel, bel), j)["klasse"]] += 1
                z["zellen"] += 1
            aus[(akz, j)] = z
            for name in summe:
                summe[name] += z[name]
        aus[("alle", j)] = summe
    return aus


def groesster(paare=C.PAARE, j: int = 1, akzeptanzen=C.AKZEPTANZEN) -> dict:
    """Die Zelle mit dem größten Unterschied zugunsten einer Regel an der Stufe j."""
    best = None
    for akz in akzeptanzen:
        for regel, bel in paare:
            x = diff(akz, key(regel, bel), j)
            if best is None or x["d"] > best["d"]:
                best = dict(x, regel=regel, belohnung=bel, akz=akz)
    return best


# ---------------------------------------------------------------- Kreditzuweisung
def kredit_rows(akz: str = "la") -> list[dict]:
    """Je Regel (Choice Function, Lernautomat, Q-Lernen): Anteil auf 2opt_b5 mit Standardbelohnung und mit „nur Bestwert“ (200·n), die Senkung
    in Prozentpunkten, die Güte des Wechsels bei beiden Budgets, die Unterschiede zu Zufall mit „nur Bestwert“ und die zwei Bedingungen der Regel."""
    rows = []
    for regel in C.DREI_REGELN:
        a2 = share("voll", akz, key(regel, "r2"))[0]
        ab = share("voll", akz, key(regel, "best"))[0]
        g = [guete(akz, regel, j) for j in range(2)]
        bed_a = a2 - ab >= C.KREDIT_SENKUNG
        bed_b = all(x["d"] >= C.KREDIT_GUETE and x["lo"] > 0 for x in g)
        rows.append(dict(regel=regel, anteil_r2=a2, anteil_best=ab, senkung=a2 - ab, guete=g, bed_a=bed_a, bed_b=bed_b, erfuellt=bed_a and bed_b,
                         zufall_r2=[diff(akz, key(regel, "r2"), j) for j in range(2)], zufall_best=[diff(akz, key(regel, "best"), j) for j in range(2)]))
    return rows


def gutschrift(akz: str, schluessel: str, j: int = 1, block: str = "voll") -> dict:
    """Mittel über die Instanzen: W (Verbesserungsarbeit je Nettogewinn) und Anteil der Standard-Gutschrift ohne neuen Bestwert (in Prozent)."""
    k = load()["konto"][block][akz][schluessel]
    w = [z[j] for z in k["w"] if z[j] is not None]
    o = [z[j] for z in k["ohne"] if z[j] is not None]
    return dict(w=ST.mean(w), ohne=100.0 * ST.mean(o), m_w=len(w), m_ohne=len(o))


def gutschrift_konto(akz: str, schluessel: str) -> tuple[list[float], list[float]]:
    """Anteil je Zugart an der Gutschrift (Summe über alle Läufe bis 200·n) nach der Standardform und nach „nur Bestwert“, in Prozent."""
    k = load()["konto"]["voll"][akz][schluessel]
    s2, sb = sum(k["gut_r2"]), sum(k["gut_best"])
    return [100.0 * x / s2 for x in k["gut_r2"]], [100.0 * x / sb for x in k["gut_best"]]


# ---------------------------------------------------------------- Verdünnungs-Kontrolle
def verduennung() -> dict:
    """Verdünnte Choice Function (Standardbelohnung) gegen die Choice Function mit „nur Bestwert“, Late Acceptance.

    d[j] = Abstand(verdünnt) - Abstand(nur Bestwert): positiv heißt, die verdünnte Regel ist schlechter."""
    v = load()["verd"]
    return dict(p=v["p"], ziel=100.0 * v["ziel"], anteil=share("verd", "la", "cfv/r2")[0], anteil_best=share("voll", "la", "cf/best")[0],
                d=[vergleich(gaps("verd", "la", "cfv/r2", j), gaps("voll", "la", "cf/best", j)) for j in range(2)],
                zufall=[diff("la", "cfv/r2", j, "verd") for j in range(2)], raster=v["raster"])


# ---------------------------------------------------------------- Empfindlichkeit
def empf_key(regel: str, einstellung: str, belohnung: str) -> str:
    return f"{regel}/{einstellung}/{belohnung}"


def empf_rows(akz: str, j: int) -> list[dict]:
    rows = []
    for regel, einst, bel in C.EMPF_VARIANTEN:
        x = diff(akz, empf_key(regel, einst, bel), j, "empf")
        rows.append(dict(x, regel=regel, einstellung=einst, belohnung=bel, wert=C.PARAMETER[regel][2 if einst == "niedrig" else 3]))
    return rows


def empf_summary(akz: str, j: int) -> dict:
    """Zählung über die 20 Varianten: Klassen, Zahl positiver Vorzeichen, beste Variante (nachträglich gewählt)."""
    rows = empf_rows(akz, j)
    return dict(varianten=len(rows), besser=sum(r["klasse"] == "besser" for r in rows), schlechter=sum(r["klasse"] == "schlechter" for r in rows),
                positiv=sum(r["d"] > 0 for r in rows), beste=max(rows, key=lambda r: r["d"]))


def reference(familie: str, n: int, idx: int) -> float | None:
    """Bester bekannter Wert der Instanz aus asw_refs.json (Instanzen 0 bis 199 je Familie und n), sonst None."""
    werte = load_refs().get("refs", {}).get(familie, {}).get(str(n))
    if werte is None or not 0 <= idx < len(werte):
        return None
    return werte[idx]
