"""Konstanten: Zugarten, Familien, Budgetstufen, Auswahlregeln, Belohnungsformen, Marken der Verdikte, Regler-Grenzen, Farben, Presets.

Der obere Teil (Zugarten, Instanzen, Zwecke der Zufalls-Seeds, Akzeptanz, Marken, Parameter von Choice Function, Lernautomat und Q-Lernen)
führt dieselben Namen und Werte wie die Wurzel-Demo der Linie (hyperheuristik-demo) und die Zugmengen-Demo (zugmenge-demo): die kopierten
Module (asw_scenario, asw_moves, asw_accept, asw_search, asw_stats, asw_select) lesen sie hier."""

# ---------------------------------------------------------------- Zugarten (Reihenfolge und Index sind Schnittstelle der Linie)
HNAMEN = ("swap", "insert", "2opt", "2opt_lokal", "oropt2", "oropt3", "dbridge", "2opt_b5")
K = 8
KOSTEN = (1, 1, 1, 1, 1, 1, 1, 5)          # Auswertungen je Anwendung; 2opt_b5 am Budgetrand weniger (asw_moves.cost_of)
H_2OPT, H_2OPT_B5 = 2, 7
ALLE_ZUGARTEN = tuple(range(K))
B5_STICHPROBEN = 5
LOKAL_LMAX = 8                              # 2opt_lokal: Segmentlänge höchstens min(8, n - 2)
HNAMEN_ANZEIGE = {
    "swap": "Tausch", "insert": "Einfügen", "2opt": "2-opt", "2opt_lokal": "2-opt lokal", "oropt2": "Or-opt 2", "oropt3": "Or-opt 3",
    "dbridge": "Doppelbrücke", "2opt_b5": "2-opt, beste von 5",
}

# ---------------------------------------------------------------- Instanzen
FAMILIEN = ("gleich", "cluster", "gitter")  # Index = Schlüssel der Zufalls-Seeds
FAMILIE_HAND = "hand"
FAMILIEN_ANZEIGE = {"gleich": "gleichverteilt", "cluster": "Gruppen", "gitter": "Gitter"}
N_GEMESSEN = (30, 60)                       # nur dort liegt die eingefrorene Messung vor; die App bietet nur diese beiden
SEITE = 1000.0                              # Quadrat 1000 x 1000 (Einheiten, keine Kilometer)
CLUSTER_ZAHL, CLUSTER_SIGMA = 5, 40.0
GITTER_FAKTOR, GITTER_RAUSCHEN = 1.5, 0.1
INSTANZEN_REF = 200                         # Instanzen 0 bis 199 je Familie und n haben einen Referenzwert (asw_refs.json)
MESS_INSTANZEN = 20                         # eingefrorene Messung: Instanzen 0 bis 19 je Familie und n (120 Instanzen, dieselben wie in zugmenge-demo)
MESS_LAEUFE = 3                             # Läufe (Zufalls-Seeds) je Instanz in der eingefrorenen Messung
TRAIN_START, TRAIN_INSTANZEN = 1000, 5      # Verdünnungs-Kontrolle: Stärke auf den Instanzen 1000 bis 1004 je Familie und n gesucht (30 Instanzen)

# Zwecke der Zufalls-Seeds (asw_scenario.derive): je Zweck ein eigener Strom
ZWECK_INSTANZ, ZWECK_START, ZWECK_LAUF, ZWECK_BOOT = 11, 33, 24, 7

# ---------------------------------------------------------------- Budget (in Vielfachen von n) und Rechengrenze
STUFEN = (50, 200)                          # klein, groß: Auswertungen = Faktor mal n
STUFEN_NAMEN = ("klein", "groß")
STUFEN_ANZEIGE = {50: "klein (50·n)", 200: "groß (200·n)"}
RECHENGRENZE = 600_000                      # Auswertungen je Mini-Messreihe: 2 x Instanzen x Läufe x Budget (Python-Schleife, O(Produkt))
MIN_INSTANZEN = 4                           # darunter gibt es kein Urteil

# ---------------------------------------------------------------- Akzeptanz
EPS = 1e-9
RHO = 0.01                                  # Rekord-zu-Rekord: Kandidat <= (1 + RHO) * Bestwert
LA_LEN, LA_LEN_KURZ = 50, 10                # Late Acceptance: Länge der Historie in Anwendungen (hier nur 50)
GD_END = 0.80                               # Sintflut (hier nicht benutzt; Name wird von asw_accept gelesen)
SA_T0, SA_T1 = 0.3, 0.003                   # Annealing (hier nicht benutzt)
AKZEPTANZEN = ("ob", "rr", "la")            # in der App wählbar und eingefroren
AKZ_ANZEIGE = {"ob": "nur besser", "rr": "Rekord-zu-Rekord", "la": "Late Acceptance (L = 50)"}
AKZ_KURZ = {"ob": "„nur besser“", "rr": "Rekord-zu-Rekord", "la": "Late Acceptance"}

# ---------------------------------------------------------------- Auswahlregeln
REGELN = ("rand", "rg", "cf", "ucb", "laut", "q")
LERNREGELN = ("cf", "ucb", "laut", "q")     # lesen die Belohnung als Zahl
DREI_REGELN = ("cf", "laut", "q")           # die drei Regeln der Kreditregel (dieselben wie in zugmenge-demo)
REGEL_ANZEIGE = {"rand": "Zufall", "rg": "Zufallsgradient", "cf": "Choice Function", "ucb": "UCB", "laut": "Lernautomat", "q": "Q-Lernen",
                 "cfv": "Choice Function, verdünnt"}
CF_ALPHA, CF_PHI0, CF_PHI_ERFOLG, CF_PHI_SCHRITT, CF_PHI_MIN, CF_ZEITFENSTER, CF_RAUSCHEN = 0.9, 0.5, 0.99, 0.01, 0.01, 50, 1e-9
LAUT_A, LAUT_BODEN = 0.05, 0.01
Q_EPS, Q_ALPHA, Q_GAMMA = 0.1, 0.1, 0.5
UCB_C, UCB_GAMMA = 0.2, 0.995
# Einstellung der Regel (Experiment 5): je Regel ein Parameter mit dem Standardwert und zwei weiteren gemessenen Werten
PARAMETER = {"cf": ("alpha", CF_ALPHA, 0.5, 0.99), "ucb": ("c", UCB_C, 0.05, 1.0), "laut": ("a", LAUT_A, 0.02, 0.15), "q": ("alpha", Q_ALPHA, 0.03, 0.3)}
PARAMETER_ANZEIGE = {"cf": "Vergessen α", "ucb": "Explorationsfaktor c", "laut": "Schrittweite a", "q": "Lernrate α"}
EINSTELLUNGEN = ("standard", "niedrig", "hoch")
EINSTELLUNG_ANZEIGE = {"standard": "Standardwert", "niedrig": "kleinerer Wert", "hoch": "größerer Wert"}

# ---------------------------------------------------------------- Belohnungsformen
BELOHNUNGEN = ("r2", "best", "r1", "rank", "ma")
BELOHNUNG_ANZEIGE = {
    "r2": "Verbesserung der aktuellen Tour je Auswertung (Standard)", "best": "nur Verbesserung des Bestwerts",
    "r1": "Verbesserung der aktuellen Tour ohne Kostenbezug", "rank": "Rang unter den letzten 30", "ma": "relativ zum gleitenden Mittel",
}
BELOHNUNG_KURZ = {"r2": "Standard", "best": "nur Bestwert", "r1": "ohne Kostenbezug", "rank": "Rang", "ma": "gleitendes Mittel"}
BELOHNUNGEN_JE_REGEL = {"rand": ("r2",), "rg": ("r2",), "cf": BELOHNUNGEN, "ucb": BELOHNUNGEN, "q": BELOHNUNGEN, "laut": ("r2", "best")}
RANK_FENSTER = 30
MA_ALPHA = 0.05
# die 18 Paare (Regel, Belohnung) der Wirkungstabelle: 5 + 5 + 5 + 2 + Zufallsgradient
PAARE = tuple((r, b) for r in ("cf", "ucb", "q") for b in BELOHNUNGEN) + (("laut", "r2"), ("laut", "best"), ("rg", "r2"))
PAARE_STANDARD = tuple((r, "r2") for r in ("rg", "cf", "ucb", "laut", "q"))
# die 20 Varianten der Empfindlichkeit: je Regel zwei Parameterwerte, bei cf, ucb, q mal drei Belohnungsformen
EMPF_BELOHNUNGEN = ("r2", "r1", "rank")
EMPF_VARIANTEN = tuple((r, e, b) for r in ("cf", "ucb", "q") for e in ("niedrig", "hoch") for b in EMPF_BELOHNUNGEN) + \
    (("laut", "niedrig", "r2"), ("laut", "hoch", "r2"))
EMPF_AKZEPTANZEN = ("la", "rr")

# ---------------------------------------------------------------- Zugmengen (nur diese zwei; alle weiteren führt zugmenge-demo)
MENGEN = {"voll": ALLE_ZUGARTEN, "ohne_2opt_b5": tuple(range(7))}
MENGEN_ANZEIGE = {"voll": "alle acht", "ohne_2opt_b5": "ohne 2opt_b5"}

# ---------------------------------------------------------------- Verdikte (gesetzt, nicht abgeleitet)
MARKE_KLAR, MARKE_GLEICH = 0.25, 0.10       # Prozentpunkte: „besser“ ab +0,25, „schlechter“ ab -0,10, jeweils mit Intervall ohne 0
ANTEIL_FEST, ANTEIL_BEVORZUGT = 0.50, 0.25  # Anteil der Anwendungen auf einer Zugart: 4- und 2-fache Gleichverteilung bei acht Zugarten
GUTSCHRIFT_VIEL, GUTSCHRIFT_TEIL = 0.50, 0.10   # Anteil der Standard-Gutschrift in Anwendungen ohne neuen Bestwert
KREDIT_SENKUNG, KREDIT_GUETE = 20.0, 0.5    # Kreditregel: Senkung des Anteils in Prozentpunkten, Güte in Punkten bei beiden Budgets
VERD_MARKE = 0.3                            # Verdünnungs-Kontrolle: Abstand in Punkten bei großem Budget
VERD_BAND = 2.0                             # Zielanteil der verdünnten Regel: höchstens 2 Prozentpunkte neben dem Anteil mit „nur Bestwert“
VERD_RASTER = tuple(round(0.05 * k, 2) for k in range(1, 20))
BOOTSTRAP_ZIEHUNGEN = 4000
FENSTER = 50                                # gleitendes Fenster der Anteile in Experiment 1 (Anwendungen)
SCHRITT_MIN = 5                             # Schritt-Regler in Kernfrage 1: Prozent der Anwendungen, in Fünferschritten

# ---------------------------------------------------------------- Regler
DEFAULT_FAMILIE, DEFAULT_N, DEFAULT_BUDGET, DEFAULT_AKZ, DEFAULT_REGEL, DEFAULT_BELOHNUNG = "gleich", 30, 50, "rr", "cf", "r2"
DEFAULT_MENGE, DEFAULT_EINSTELLUNG = "voll", "standard"
INSTANZ_MAX, DEFAULT_INSTANZ = 99, 0
LAUF_MAX, DEFAULT_LAUF = 9, 0
MINI_INSTANZEN_MIN, MINI_INSTANZEN_MAX, DEFAULT_MINI_INSTANZEN = 6, 30, 24   # Rechenzeit linear in Instanzen x Läufe x Budget
MINI_LAEUFE_MIN, MINI_LAEUFE_MAX, DEFAULT_MINI_LAEUFE = 1, 4, 2

# ---------------------------------------------------------------- Farben
FARBE_ZUGART = ("#9d755d", "#f58518", "#4c78a8", "#72b7b2", "#b279a2", "#ff9da6", "#bab0ac", "#e45756")
COLOR_REGEL = "#2F6B65"
COLOR_ZUFALL = "#888888"
COLOR_BEST = "#4c78a8"
COLOR_SCHLECHT = "#e45756"
COLOR_GUT = "#54a24b"

# ---------------------------------------------------------------- Presets (jedes legt alle Regler fest)
_BASIS = {"familie": "gleich", "n": 30, "budget": 50, "instanz": 0, "lauf": 0, "regel": "cf", "akz": "rr", "belohnung": "r2", "menge": "voll",
          "einstellung": "standard", "mini_instanzen": DEFAULT_MINI_INSTANZEN, "mini_laeufe": DEFAULT_MINI_LAEUFE}


def _preset(**kw):
    p = dict(_BASIS)
    p.update(kw)
    return p


PRESETS = {
    "Rekord-zu-Rekord, kleines Budget": _preset(),
    "Late Acceptance: hier verliert Lernen": _preset(akz="la"),
    "Nur Verbesserungen des Bestwerts belohnen": _preset(akz="la", belohnung="best", budget=200),
    "Großes Budget, „nur besser“": _preset(regel="q", akz="ob", budget=200),
    "Der Lernautomat legt sich fest": _preset(regel="laut", akz="la", budget=200),
    "UCB wählt fast wie Zufall": _preset(regel="ucb", akz="la", budget=200),
    "Ohne die Zugart 2opt_b5": _preset(akz="la", menge="ohne_2opt_b5"),
}
PRESET_HELP: dict[str, str] = {}             # wird in asw_texts gefüllt (die Texte nennen Zahlen der eingefrorenen Messung)
