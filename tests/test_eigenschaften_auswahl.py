"""Eigenschaften der Läufe (metamorph, fester Zufalls-Seed): gelten für jede Regel, jede Belohnung und jede der drei Akzeptanzregeln.

Dazu die Zweig-Tests: jede Regel, jede Belohnungsform, jede Einstellung und die zweite Zugmenge ändern das Ergebnis auf mindestens einer Instanz
(eine Variante, die nie abweicht, liefe nie)."""

import pytest

import asw_algorithm as A
import asw_constants as C
import asw_regeln as R
import asw_scenario as S
from asw_rngblock import BlockSplitMix64
from conftest import brute_force, zufallsinstanz

INSTANZEN = [(f, 30, i) for f in C.FAMILIEN for i in (100, 101, 102, 103)]
ALLE_PAARE = (("rand", "r2"),) + C.PAARE


@pytest.mark.parametrize("regel,bel", ALLE_PAARE)
def test_gleicher_seed_gleiche_spur_anderer_seed_andere_und_budget_exakt(regel, bel):
    a = A.run("gleich", 30, 100, 0, regel, "la", bel, budget=1500, spur=True)
    b = A.run("gleich", 30, 100, 0, regel, "la", bel, budget=1500, spur=True)
    c = A.run("gleich", 30, 100, 1, regel, "la", bel, budget=1500, spur=True)
    assert a["konto"].spur == b["konto"].spur and a["best"] == b["best"]
    assert a["konto"].spur != c["konto"].spur
    assert a["used"] == 1500 == sum(a["konto"].evals)                    # 2opt_b5 wird am Budgetrand gekürzt


@pytest.mark.parametrize("akz", C.AKZEPTANZEN)
@pytest.mark.parametrize("regel", C.REGELN)
def test_bestwert_faellt_nie_w_mindestens_eins_und_tour_bleibt_gueltig(regel, akz):
    for familie, n, idx in INSTANZEN[::3]:
        r = A.run(familie, n, idx, 0, regel, akz, "r2", budget=1500, spur=True)
        best = [z[5] for z in r["konto"].spur]
        assert all(x >= y - 1e-12 for x, y in zip(best, best[1:])) and best[-1] == r["best"] <= r["start"]
        assert sorted(r["tour"]) == list(range(n)) and S.tour_cost(A.instance(familie, n, idx)[1], r["tour"]) == pytest.approx(r["final"], rel=1e-9)
        assert r["w"] is None or r["w"] >= 1 - 1e-9
        assert r["anteil_ohne"] is None or 0 <= r["anteil_ohne"] <= 1


@pytest.mark.parametrize("regel", C.LERNREGELN)
def test_unter_nur_besser_ist_der_bestwert_die_aktuelle_laenge_und_beide_belohnungen_sind_gleich(regel):
    for familie, n, idx in INSTANZEN[:6]:
        a = A.run(familie, n, idx, 0, regel, "ob", "r2", budget=3000, spur=True)
        b = A.run(familie, n, idx, 0, regel, "ob", "best", budget=3000, spur=True)
        assert all(z[4] == z[5] for z in a["konto"].spur)                # aktuelle Länge = Bestwert in jedem Schritt
        assert a["w"] == pytest.approx(1.0, abs=1e-12) and a["anteil_ohne"] == 0.0 and a["konto"].verschlechterungen == 0
        assert a["konto"].spur == b["konto"].spur                        # „nur Bestwert“ ist hier bitgleich zur Standardbelohnung
        assert a["konto"].gut_r2 == a["konto"].gut_best


@pytest.mark.parametrize("regel", ["cf", "q", "laut", "ucb", "rg"])
def test_skalieren_der_koordinaten_aendert_die_zugfolge_nicht(regel):
    """Alle Abstände mal 4 (Zweierpotenz, exakt): gleiche Zugarten, gleiche Annahmen, Längen exakt mal 4. Die Belohnungen sind skalenfrei.
    Voraussetzung: keine Änderung liegt im Bereich der festen Toleranz 1e-9 (in diesen Läufen geprüft)."""
    punkte, D = A.instance("gleich", 30, 104)
    D4 = [[4.0 * x for x in zeile] for zeile in D]
    t0 = S.nn_tour(D, 0)
    a = A.run_on(D, t0, BlockSplitMix64(7), regel, "la", "r2", budget=1500, spur=True)
    b = A.run_on(D4, t0, BlockSplitMix64(7), regel, "la", "r2", budget=1500, spur=True)
    assert all(abs(z[1]) > 4e-9 or z[1] == 0.0 for z in a["konto"].spur)
    assert [(z[0], z[3]) for z in a["konto"].spur] == [(z[0], z[3]) for z in b["konto"].spur]
    assert b["best"] == 4.0 * a["best"] and b["konto"].gut_r2 == pytest.approx(a["konto"].gut_r2, rel=1e-12)


def test_eine_einzige_zugart_wird_immer_gewaehlt():
    for regel in C.REGELN:
        r = A.run("gleich", 30, 100, 0, regel, "rr", "r2", menge=(2,), budget=600)
        assert r["apps"][2] == 600 and sum(r["apps"]) == 600


def test_ohne_jede_verbesserung_lernt_keine_regel():
    """Eine Tour, die schon optimal ist (sechs Orte auf einem Rechteck): keine Belohnung, der Lernautomat bleibt bei 1 / m, Q bei 0."""
    _, D = S.hand_instance()
    for regel in ("laut", "q", "cf", "ucb"):
        r = A.run_on(D, [0, 1, 2, 3, 4, 5], BlockSplitMix64(1), regel, "ob", "r2", menge=(0, 1, 2), budget=200)
        k = r["konto"]
        assert k.r2_summe == 0.0 and r["w"] is None and r["anteil_ohne"] is None and r["best"] == 22.0
        if regel == "laut":
            assert k.state["p"] == [1 / 3] * 3
        if regel == "q":
            assert k.state["q"] == [0.0] * 3


def test_zufallsgradient_wiederholt_die_zugart_nach_einem_erfolg():
    r = A.run("gleich", 30, 100, 0, "rg", "la", "r2", budget=1500, spur=True)
    spur = r["konto"].spur
    nach_erfolg = [(a[0], b[0]) for a, b in zip(spur, spur[1:]) if a[1] < -C.EPS]
    assert nach_erfolg and all(x == y for x, y in nach_erfolg)


@pytest.mark.parametrize("regel", C.REGELN)
def test_suche_liegt_nie_unter_dem_optimum(regel):
    """n = 8: Optimum per Aufzählung aller Rundtouren; jede Regel bleibt darüber und erreicht es in mindestens 5 von 6 Instanzen."""
    treffer = 0
    for seed in range(6):
        D, t0 = zufallsinstanz(8, seed)
        opt = brute_force(D)
        r = A.run_on(D, t0, BlockSplitMix64(seed), regel, "la", "r2", budget=3000, check=True)
        assert r["best"] >= opt - 1e-9
        treffer += r["best"] <= opt + 1e-9
    assert treffer >= 5


# ---------------------------------------------------------------- Zweig-Tests
def _bests(regel, bel, akz="la", menge=C.ALLE_ZUGARTEN, wert=None, faktor=50):
    return [A.run(f, n, i, 0, regel, akz, bel, menge, faktor * n, wert=wert)["best"] for f, n, i in INSTANZEN]


def test_jede_regel_weicht_von_zufall_ab():
    zufall = _bests("rand", "r2")
    for regel in C.REGELN[1:]:
        assert _bests(regel, "r2") != zufall, regel


@pytest.mark.parametrize("regel", C.LERNREGELN)
def test_jede_belohnungsform_weicht_von_der_standardform_ab(regel):
    standard = _bests(regel, "r2", faktor=200)                           # bei 50·n rechnet die Choice Function auf diesen 12 Instanzen mit „ohne Kostenbezug“ noch gleich
    for bel in C.BELOHNUNGEN_JE_REGEL[regel][1:]:
        assert _bests(regel, bel, faktor=200) != standard, (regel, bel)


@pytest.mark.parametrize("regel", list(C.PARAMETER))
def test_jede_einstellung_weicht_vom_standard_ab(regel):
    standard = _bests(regel, "r2")
    for einst in ("niedrig", "hoch"):
        assert _bests(regel, "r2", wert=R.parameter_wert(regel, einst)) != standard, (regel, einst)


def test_zugmenge_ohne_2opt_b5_und_verduennung_weichen_ab():
    assert _bests("cf", "r2", menge=C.MENGEN["ohne_2opt_b5"]) != _bests("cf", "r2")
    assert _bests("cfv", "r2", wert=0.5) != _bests("cf", "r2")
    assert A.run("gleich", 30, 100, 0, "cf", "la", "r2", C.MENGEN["ohne_2opt_b5"], 1500)["apps"][7] == 0


def test_leere_und_unbekannte_zugmenge_werden_abgelehnt():
    with pytest.raises(ValueError):
        A.normalize_set(())
    with pytest.raises(ValueError):
        A.normalize_set((0, 9))
    assert A.normalize_set([7, 2, 2, 0]) == (0, 2, 7)


def _w_bedingung(spur, start):
    """Bedingung der README für W = 1: vor dem letzten neuen Bestwert wurde keine Verlängerung angenommen, danach kam keine Verkürzung mehr."""
    letzter = None
    vorher = start
    for k, z in enumerate(spur):
        if z[5] < vorher - C.EPS:
            letzter = k
        vorher = z[5]
    if letzter is None:
        return None
    verlaengert = any(z[3] and z[1] > C.EPS for z in spur[:letzter])
    danach_verkuerzt = any(z[3] and z[1] < -C.EPS for z in spur[letzter + 1:])
    return not verlaengert and not danach_verkuerzt


@pytest.mark.parametrize("akz", C.AKZEPTANZEN)
def test_w_gleich_eins_genau_unter_der_bedingung_der_readme(akz):
    """README: W = 1 gilt, wenn vor dem letzten Bestwert keine Verlängerung angenommen wurde und danach keine Verkürzung mehr kam; sonst W > 1."""
    gesehen = set()
    for regel in ("rand", "cf"):
        for familie, n, idx in INSTANZEN[::2]:
            for budget in (30, 60, 120, 400, 1500):
                r = A.run(familie, n, idx, 0, regel, akz, "r2", budget=budget, spur=True)
                bed = _w_bedingung(r["konto"].spur, r["start"])
                if bed is None:
                    assert r["w"] is None
                    continue
                assert (abs(r["w"] - 1.0) < 1e-9) == bed, (regel, familie, idx, budget, r["w"])
                gesehen.add(bed)
    assert True in gesehen
    if akz != "ob":
        assert False in gesehen
