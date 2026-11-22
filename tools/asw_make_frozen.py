"""Erzeugt asw_frozen.json: die eingefrorene Messung der Demo (Wirkungstabelle, Anteile, Gutschrift, Empfindlichkeit, Verdünnungs-Kontrolle).

Aufruf (aus dem Demo-Ordner):  python tools/asw_make_frozen.py [--procs 2]      rechnet alles neu und schreibt die Datei
                               python tools/asw_make_frozen.py --check          rechnet drei Instanzen neu und vergleicht als Band

Größe: 120 Instanzen (3 Familien x n = 30, 60 x Instanzen 0 bis 19, dieselben wie in zugmenge-demo) x 3 Läufe, je Lauf bis 200·n
Auswertungen mit Kontrollpunkt bei 50·n. Je Instanz 116 Varianten (57 Wirkungstabelle, 18 ohne 2opt_b5, 40 Empfindlichkeit, 1 Verdünnung).
Die Werte der Datei werden nie von Hand geändert: Fehler hier beheben und neu erzeugen."""

import argparse
import json
import platform
import sys
from datetime import date
from multiprocessing import Pool
from pathlib import Path

ORDNER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ORDNER))

import asw_algorithm as A  # noqa: E402
import asw_constants as C  # noqa: E402
import asw_regeln as R  # noqa: E402

DATEI = ORDNER / "asw_frozen.json"
REFS = ORDNER / "asw_refs.json"


def instanzen() -> list[tuple[str, int, int]]:
    return [(f, n, i) for f in C.FAMILIEN for n in C.N_GEMESSEN for i in range(C.MESS_INSTANZEN)]


def varianten() -> list[tuple[str, str, str, str, str, float | None]]:
    """Alle Varianten der Hauptmessung: (Block, Akzeptanz, Schlüssel, Regel, Belohnung, Parameterwert)."""
    v = []
    for akz in C.AKZEPTANZEN:
        v.append(("voll", akz, "rand/r2", "rand", "r2", None))
        for regel, bel in C.PAARE:
            v.append(("voll", akz, f"{regel}/{bel}", regel, bel, None))
        for regel in C.REGELN:
            v.append(("ohne_2opt_b5", akz, f"{regel}/r2", regel, "r2", None))
    for akz in C.EMPF_AKZEPTANZEN:
        for regel, einst, bel in C.EMPF_VARIANTEN:
            v.append(("empf", akz, f"{regel}/{einst}/{bel}", regel, bel, R.parameter_wert(regel, einst)))
    return v


def ein_lauf(familie, n, idx, lauf, block, akz, regel, bel, wert) -> dict:
    menge = C.MENGEN["ohne_2opt_b5"] if block == "ohne_2opt_b5" else C.ALLE_ZUGARTEN
    ck = tuple(f * n for f in C.STUFEN)
    r = A.run(familie, n, idx, lauf, regel, akz, bel, menge, ck[-1], checkpoints=ck, wert=wert)
    st = r["konto"].stand
    return dict(best=[s["best"] for s in st], apps=[s["apps"] for s in st], evals=[s["evals"] for s in st],
                w=[A.arbeit_je_gewinn(s["verbesserung"], r["start"], s["best"]) for s in st],
                ohne=[A.anteil_ohne_bestwert(s["r2_ohne"], s["r2_summe"]) for s in st],
                gut_r2=st[-1]["gut_r2"], gut_best=st[-1]["gut_best"], used=r["used"])


def _mittel(werte):
    werte = [w for w in werte if w is not None]
    return sum(werte) / len(werte) if werte else None


def messe_instanz(arg) -> dict:
    """Alle Varianten einer Instanz über die Läufe; je Variante Bestwerte je Lauf und Stufe und die Zähler als Summen."""
    familie, n, idx, liste = arg
    aus = {}
    used = 0
    for block, akz, key, regel, bel, wert in liste:
        laeufe = [ein_lauf(familie, n, idx, lauf, block, akz, regel, bel, wert) for lauf in range(C.MESS_LAEUFE)]
        used += sum(x["used"] for x in laeufe)
        ns = len(C.STUFEN)
        aus[(block, akz, key)] = dict(
            best=[x["best"] for x in laeufe],
            apps=[[sum(x["apps"][j][h] for x in laeufe) for h in range(C.K)] for j in range(ns)],
            evals=[[sum(x["evals"][j][h] for x in laeufe) for h in range(C.K)] for j in range(ns)],
            w=[_mittel([x["w"][j] for x in laeufe]) for j in range(ns)],
            ohne=[_mittel([x["ohne"][j] for x in laeufe]) for j in range(ns)],
            gut_r2=[sum(x["gut_r2"][h] for x in laeufe) for h in range(C.K)],
            gut_best=[sum(x["gut_best"][h] for x in laeufe) for h in range(C.K)],
        )
    return dict(inst=(familie, n, idx), aus=aus, used=used)


def anteil_training(arg) -> tuple[float, list[int]]:
    """Verdünnungs-Kontrolle: Anwendungen je Zugart der verdünnten Choice Function (Late Acceptance, 200·n) auf den Trainingsinstanzen."""
    p, = arg
    apps = [0] * C.K
    for f in C.FAMILIEN:
        for n in C.N_GEMESSEN:
            for i in range(C.TRAIN_START, C.TRAIN_START + C.TRAIN_INSTANZEN):
                k = A.run(f, n, i, 0, "cfv", "la", "r2", C.ALLE_ZUGARTEN, C.STUFEN[-1] * n, wert=p)["konto"]
                apps = [a + b for a, b in zip(apps, k.apps)]
    return p, apps


def _karte(pool, fn, args):
    return list(pool.imap(fn, args)) if pool else [fn(a) for a in args]


def rechne(procs: int) -> dict:
    refs = json.loads(REFS.read_text(encoding="utf-8"))["refs"]
    inst = instanzen()
    pool = Pool(procs) if procs > 1 else None
    haupt = _karte(pool, messe_instanz, [(f, n, i, varianten()) for f, n, i in inst])
    used = sum(x["used"] for x in haupt)

    # Verdünnung: Ziel ist der Anteil auf 2opt_b5 der Choice Function mit „nur Bestwert“ (Late Acceptance, 200·n) in dieser Messung
    apps_best = [sum(x["aus"][("voll", "la", "cf/best")]["apps"][-1][h] for x in haupt) for h in range(C.K)]
    ziel = apps_best[C.H_2OPT_B5] / sum(apps_best)
    raster = _karte(pool, anteil_training, [(p,) for p in C.VERD_RASTER])
    raster = [(p, a[C.H_2OPT_B5] / sum(a)) for p, a in raster]
    p_wahl = min(raster, key=lambda z: (abs(z[1] - ziel), z[0]))[0]
    verd = _karte(pool, messe_instanz, [(f, n, i, [("verd", "la", "cfv/r2", "cfv", "r2", p_wahl)]) for f, n, i in inst])
    used += sum(x["used"] for x in verd)
    if pool:
        pool.close()
        pool.join()
    for x, y in zip(haupt, verd):
        x["aus"].update(y["aus"])

    # Referenz: Minimum aus dem vorgerechneten Wert und allen Läufen dieser Messung
    ref = []
    unterboten = 0
    for (f, n, i), x in zip(inst, haupt):
        alt = refs[f][str(n)][i]
        kleinste = min(b[-1] for v in x["aus"].values() for b in v["best"])
        if kleinste < alt - 1e-6:
            unterboten += 1
        ref.append(round(min(alt, kleinste), 6))

    def gap_zeilen(schluessel):
        zeilen = []
        for x, rf in zip(haupt, ref):
            best = x["aus"][schluessel]["best"]
            zeilen.append([round(sum(100.0 * (b[j] - rf) / rf for b in best) / len(best), 4) for j in range(len(C.STUFEN))])
        return zeilen

    def summe(schluessel, feld):
        return [[sum(x["aus"][schluessel][feld][j][h] for x in haupt) for h in range(C.K)] for j in range(len(C.STUFEN))]

    def je_instanz(schluessel, feld):
        return [[None if v is None else round(v, 4) for v in x["aus"][schluessel][feld]] for x in haupt]

    gap: dict = {}
    zaehler: dict = {}
    konto: dict = {}
    for block, akz, key in haupt[0]["aus"]:
        s = (block, akz, key)
        gap.setdefault(block, {}).setdefault(akz, {})[key] = gap_zeilen(s)
        zaehler.setdefault(block, {}).setdefault(akz, {})[key] = dict(apps=summe(s, "apps"), evals=summe(s, "evals"))
        if block in ("voll", "verd"):
            konto.setdefault(block, {}).setdefault(akz, {})[key] = dict(
                w=je_instanz(s, "w"), ohne=je_instanz(s, "ohne"),
                gut_r2=[round(sum(x["aus"][s]["gut_r2"][h] for x in haupt), 4) for h in range(C.K)],
                gut_best=[round(sum(x["aus"][s]["gut_best"][h] for x in haupt), 4) for h in range(C.K)])
    return dict(
        meta=dict(instanzen=len(inst), laeufe=C.MESS_LAEUFE, stufen=list(C.STUFEN), akzeptanzen=list(C.AKZEPTANZEN), paare=[list(p) for p in C.PAARE],
                  empf_varianten=[list(v) for v in C.EMPF_VARIANTEN], empf_akzeptanzen=list(C.EMPF_AKZEPTANZEN), auswertungen_gesamt=used,
                  python=platform.python_version(), system=platform.system(), datum=date.today().isoformat(),
                  zufall="SplitMix64 (asw_rng, asw_rngblock)"),
        instanzen=[list(x) for x in inst], ref=ref, unterboten=unterboten, gap=gap, zaehler=zaehler, konto=konto,
        verd=dict(p=p_wahl, ziel=round(ziel, 6), raster=[[p, round(a, 6)] for p, a in raster],
                  training=[C.TRAIN_START, C.TRAIN_START + C.TRAIN_INSTANZEN - 1]),
    )


CHECK_INSTANZEN = (("gleich", 30, 0), ("cluster", 60, 7), ("gitter", 30, 19))
CHECK_VARIANTEN = (("voll", "rr", "rand/r2"), ("voll", "rr", "cf/r2"), ("voll", "la", "cf/best"), ("voll", "la", "ucb/rank"), ("voll", "ob", "q/ma"),
                   ("ohne_2opt_b5", "la", "laut/r2"), ("empf", "la", "ucb/hoch/r1"), ("verd", "la", "cfv/r2"))


def check(daten: dict, instanzen_check=CHECK_INSTANZEN, varianten_check=CHECK_VARIANTEN, toleranz: float = 2e-3) -> list[str]:
    """Rechnet einen Ausschnitt neu und vergleicht die Abstände (Band `toleranz` Prozentpunkte) und die Zähler dieser Instanzen nicht (Summen).
    Rückgabe: Liste der Abweichungen (leer = in Ordnung)."""
    alle = {(b, a, k): (b, a, k, r, bel, w) for b, a, k, r, bel, w in varianten()}
    alle[("verd", "la", "cfv/r2")] = ("verd", "la", "cfv/r2", "cfv", "r2", daten["verd"]["p"])
    fehler = []
    index = {tuple(x): j for j, x in enumerate(daten["instanzen"])}
    for f, n, i in instanzen_check:
        j = index[(f, n, i)]
        rf = daten["ref"][j]
        aus = messe_instanz((f, n, i, [alle[s] for s in varianten_check]))["aus"]
        for s in varianten_check:
            best = aus[s]["best"]
            neu = [sum(100.0 * (b[k] - rf) / rf for b in best) / len(best) for k in range(len(C.STUFEN))]
            alt = daten["gap"][s[0]][s[1]][s[2]][j]
            if any(abs(a - b) > toleranz for a, b in zip(neu, alt)):
                fehler.append(f"{f}/{n}/{i} {s}: neu {neu}, Datei {alt}")
    return fehler


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--procs", type=int, default=2)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        fehler = check(json.loads(DATEI.read_text(encoding="utf-8")))
        print(f"{len(CHECK_INSTANZEN) * len(CHECK_VARIANTEN)} Vergleiche, {len(fehler)} Abweichungen")
        for f in fehler:
            print("  " + f)
        return 1 if fehler else 0
    daten = rechne(a.procs)
    DATEI.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    print(f"{DATEI.name}: {daten['meta']['auswertungen_gesamt']} Auswertungen, Verdünnung p = {daten['verd']['p']}, unterboten {daten['unterboten']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
