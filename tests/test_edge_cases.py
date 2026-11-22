"""Randfälle: kleinstes Budget, Budget unter fünf (2opt_b5 wird gekürzt), eine einzige Zugart, alle Belohnungen 0, Regler am Rand, Mini-Reihe."""

import threading

import pytest

import asw_algorithm as A
import asw_constants as C
import asw_evaluation as E
import asw_frozen as F
import asw_visualization as V


@pytest.mark.parametrize("budget", [1, 2, 4, 5, 6])
@pytest.mark.parametrize("regel", C.REGELN)
def test_kleinste_budgets_werden_exakt_verbraucht(regel, budget):
    r = A.run("gitter", 30, 0, 0, regel, "la", "r2", budget=budget, spur=True)
    assert r["used"] == budget and 1 <= r["steps"] <= budget and r["best"] <= r["start"]
    assert all(z[2] <= 5 for z in r["konto"].spur) and sum(z[2] for z in r["konto"].spur) == budget


def test_nur_2opt_b5_mit_budget_unter_fuenf_wird_gekuerzt():
    r = A.run("gleich", 30, 0, 0, "rand", "rr", "r2", menge=(7,), budget=13, spur=True)
    assert [z[2] for z in r["konto"].spur] == [5, 5, 3]


def test_lauf_ohne_verbesserung_hat_keine_kennzahlen():
    assert A.arbeit_je_gewinn(0.0, 100.0, 100.0) is None and A.anteil_ohne_bestwert(0.0, 0.0) is None
    assert A.arbeit_je_gewinn(6.0, 30.0, 28.0) == 3.0 and A.anteil_ohne_bestwert(0.8, 1.2) == pytest.approx(2 / 3)
    assert A.shares([0] * 8, [0] * 8) == ([0.0] * 8, [0.0] * 8)


@pytest.mark.parametrize("familie", C.FAMILIEN)
@pytest.mark.parametrize("n", C.N_GEMESSEN)
def test_regler_am_rand_instanz_und_lauf(familie, n):
    r = A.run(familie, n, C.INSTANZ_MAX, C.LAUF_MAX, "ucb", "ob", "ma", C.MENGEN["ohne_2opt_b5"], C.STUFEN[0] * n)
    assert r["used"] == C.STUFEN[0] * n and r["apps"][7] == 0 and F.reference(familie, n, C.INSTANZ_MAX) is not None


def test_referenz_ausserhalb_des_bereichs_ist_none():
    assert F.reference("gleich", 30, 200) is None and F.reference("gleich", 45, 0) is None and F.reference("gleich", 30, 199) > 0


def test_mini_reihe_klein_und_ohne_referenz():
    """Vier Instanzen, ein Lauf; ohne gespeicherte Referenz gilt der beste Lauf der Reihe. Gepaart: Zufall gegen Zufall gibt exakt 0."""
    mr = E.mini_reihe(lambda *a: None, "gleich", 30, 0, 4, 1, "rand", "rr", "r2", C.ALLE_ZUGARTEN, 50)
    assert mr["je_instanz"] == [0.0] * 4 and mr["d"] == 0.0 and mr["kosten"] == E.mini_kosten(4, 1, 30, 50) and mr["halbbreite"] == 0.0
    mr = E.mini_reihe(F.reference, "gleich", 30, 198, 4, 1, "laut", "la", "best", C.ALLE_ZUGARTEN, 50)
    assert len(mr["je_instanz"]) == 4 and mr["lo"] <= mr["d"] <= mr["hi"] and mr["abstand_zufall"] - mr["abstand_regel"] == pytest.approx(mr["d"])
    assert mr["abstand_zufall"] >= 0 and mr["abstand_regel"] >= 0


def test_mini_reihe_am_reglermaximum_endet():
    """Größte erlaubte Reihe (600 000 Auswertungen): Timeout als Netz, keine Zeit-Assertion. Über der Grenze rechnet die App nicht."""
    assert E.mini_kosten(25, 1, 60, 200) == C.RECHENGRENZE
    ergebnis = {}
    t = threading.Thread(target=lambda: ergebnis.update(wert=E.mini_reihe(F.reference, "cluster", 60, 80, 25, 1, "cf", "la", "rank", C.ALLE_ZUGARTEN, 200)), daemon=True)
    t.start()
    t.join(240)
    assert not t.is_alive(), "Mini-Reihe am Reglermaximum hängt"
    assert ergebnis["wert"]["kosten"] == C.RECHENGRENZE


def test_abbildungen_haben_feste_achsen_und_vertragen_den_rand():
    r = A.run("gleich", 30, 0, 0, "cf", "la", "r2", budget=1500, spur=True)
    k = r["konto"]
    a, e = A.shares(k.apps, k.evals)
    figs = [V.fig_verlauf(k.spur, r["start"], 1), V.fig_verlauf(k.spur, r["start"], len(k.spur)), V.fig_fenster(k.spur, r["arms"], 1),
            V.fig_fenster(k.spur, r["arms"], len(k.spur)), V.fig_anteile(a, e, r["arms"], 12.5), V.fig_konto(k.gut_r2, k.gut_best, r["arms"]),
            V.fig_wirkung([("x", 0.3, 0.1, 0.5, "besser"), ("y", -1.0, -1.5, -0.5, "schlechter")], "t"), V.fig_mini([0.5, -0.2, 0.0])]
    for fig in figs:
        assert fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange
    stellen, anteile = V.fenster_anteile(k.spur, len(k.spur))
    assert len(stellen) <= 120 and all(abs(sum(anteile[h][i] for h in range(C.K)) - 100.0) < 1e-9 for i in range(len(stellen)))
    assert V.fenster_anteile(k.spur, 0) == ([], [[] for _ in range(C.K)])
