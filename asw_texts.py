"""Texte der App: Einleitung, Erklärtabellen, Annahmen, Formelblock. Sätze mit Messzahlen stehen in asw_saetze (aus der eingefrorenen Messung gerechnet).

ASSUMPTIONS_MARKDOWN steht wortgleich in der README (tests/test_claims.py vergleicht)."""

import asw_constants as C

TITEL = "🎰 Wer belohnt wen? Kreditzuweisung bei der Wahl der Zugart"
SEITENTITEL = "Wer belohnt wen – Sebastian Hanisch"

INTRO = """
Dritte **Demo der Linie „Hyperheuristiken erklärt“**: Eine Suche auf der **Rundtour** hat acht **Zugarten** zur Verfügung, und eine **Regel**
entscheidet in jedem Schritt, welche gerade dran ist. Sechs Regeln stehen im Vergleich (Zufall, Zufallsgradient, Choice Function, UCB,
Lernautomat, Q-Lernen); die Frage ist, **wer die Gutschrift bekommt**, wenn die Suche zwischendurch Verschlechterungen annimmt.
Gemessen wird in **Auswertungen** (bewertete Kandidaten) auf erzeugten Rundtouren mit 30 und 60 Städten, mit eigenen, vereinfachten
Umsetzungen der Regeln. Die Voreinstellung der Akzeptanz ist hier **Rekord-zu-Rekord** (wie in „Die Zugmenge entscheidet“), nicht „nur besser“
wie in der ersten Demo der Linie; wie Akzeptanz und Auswahl zusammenwirken, zerlegt die Demo „Akzeptanz mal Auswahl“.

Wer zuerst ohne Fachbegriffe lesen will, öffnet „💬 In einfachen Worten“. Unten stehen fünf Kernfragen mit je einem Experiment, der Abschnitt **🚧 Wo die Annahmen enden** und die Formeln im Expander
**📐 Mathematische Formulierung**.
"""

ABLAUF = """
1. **Start:** eine Rundtour nach der Regel „Nächster Nachbar“. Jede Anwendung einer Zugart bewertet einen zufälligen Vorschlag (eine
   **Auswertung**; `2opt_b5` bewertet bis zu fünf und nimmt den besten).
2. **Auswahl:** die **Regel** bestimmt die Zugart der nächsten Anwendung. Zufall würfelt, die anderen fünf lesen, was zuletzt Erfolg hatte.
3. **Akzeptanz:** die **Akzeptanzregel** entscheidet, ob der Vorschlag bleibt. „Nur besser“ nimmt nur Verkürzungen an; Rekord-zu-Rekord und
   Late Acceptance nehmen auch begrenzte Verlängerungen an.
4. **Gutschrift:** die Zugart bekommt eine **Belohnung** zwischen 0 und 1. In der Standardform zählt jede Verkürzung der aktuellen Tour, auch
   wenn sie nur eine vorher angenommene Verlängerung aufholt. Die Form „nur Bestwert“ zählt allein Verkürzungen der besten bisher gefundenen Tour.
5. **Lernen:** die Regel schreibt ihren Zustand mit der Belohnung fort. Das Budget endet nach einer festen Zahl von Auswertungen.
"""

REGEL_TABELLE = """
| Regel | Was sie tut (eigene, vereinfachte Umsetzung) | feste Einstellung |
|---|---|---|
| Zufall | wählt jede Zugart der Menge gleich oft, beachtet keinen Erfolg | keine |
| Zufallsgradient | behält die Zugart, solange ihre letzte Anwendung die aktuelle Tour verkürzte, sonst würfelt sie neu | keine |
| Choice Function | wertet je Zugart die jüngsten Belohnungen (allein und nach dem Vorgänger) und die Wartezeit seit der letzten Anwendung; nimmt die höchste Wertung | Vergessen α = 0,9 |
| UCB | Mittelwert der Belohnung plus ein Bonus für selten gewählte Zugarten; ältere Anwendungen zählen weniger | c = 0,2, γ = 0,995 |
| Lernautomat | hält je Zugart eine Wahrscheinlichkeit und erhöht sie nach jedem Erfolg (Linear Reward-Inaction) | Schrittweite a = 0,05, Boden 0,01 (vor dem Normieren) |
| Q-Lernen | ein Zustand, ein Wert je Zugart; meist die Zugart mit dem höchsten Wert, mit Wahrscheinlichkeit 0,1 eine zufällige | α = 0,1, γ = 0,5, ε = 0,1 |
"""

BELOHNUNG_TABELLE = """
| Belohnung | Formel in Worten | gelesen von |
|---|---|---|
| Standard | Verkürzung der aktuellen Tour, geteilt durch Auswertungen der Anwendung mal mittlere Kantenlänge der Starttour, höchstens 1 | allen fünf lernenden Regeln (Zufallsgradient nur: größer als 0) |
| nur Bestwert | dieselbe Formel, aber mit der Senkung des Bestwerts statt der Verkürzung der aktuellen Tour | Choice Function, UCB, Q-Lernen, Lernautomat |
| ohne Kostenbezug | Verkürzung der aktuellen Tour durch die mittlere Kantenlänge, ohne durch die Auswertungen zu teilen | Choice Function, UCB, Q-Lernen |
| Rang | Anzahl der letzten 30 Standardbelohnungen, die kleiner sind, geteilt durch 30 (auch solange weniger als 30 Werte vorliegen) | Choice Function, UCB, Q-Lernen |
| gleitendes Mittel | Standardbelohnung geteilt durch das gleitende Mittel der bisherigen Erfolge, höchstens 1 | Choice Function, UCB, Q-Lernen |
"""

AKZEPTANZ_TABELLE = """
| Akzeptanzregel | Ein Vorschlag bleibt, wenn … |
|---|---|
| nur besser | er die Tour streng verkürzt |
| Rekord-zu-Rekord | er nicht verlängert oder die neue Länge höchstens 1 % über dem Bestwert liegt |
| Late Acceptance (L = 50) | er nicht verlängert oder die neue Länge höchstens so groß ist wie die Länge vor 50 Anwendungen |
"""

ZUGART_TABELLE = """
| Zugart | Was sie ändert | Auswertungen |
|---|---|---|
| `swap` | zwei Städte tauschen die Plätze | 1 |
| `insert` | eine Stadt wird an eine andere Stelle gesetzt | 1 |
| `2opt` | ein Stück der Tour wird umgedreht | 1 |
| `2opt_lokal` | ein kurzes Stück (höchstens 8 Städte) wird umgedreht | 1 |
| `oropt2`, `oropt3` | zwei bzw. drei aufeinanderfolgende Städte wandern gemeinsam | 1 |
| `dbridge` | die Tour wird an drei Stellen geschnitten und über Kreuz verbunden (Doppelbrücke) | 1 |
| `2opt_b5` | fünf 2-opt-Vorschläge, der beste wird angewandt | bis 5 |
"""

ASSUMPTIONS_MARKDOWN = """
1. **Maßstab:** 30 und 60 Städte, Budgets 50·n und 200·n Auswertungen (1 500 bis 12 000), drei Familien erzeugter Rundtouren. Die Aussagen gelten für diesen Bereich, nicht für größere Instanzen und nicht für andere Aufgaben.
2. **Eigene Umsetzungen:** Alle sechs Regeln sind vereinfacht und mit festen, nicht abgestimmten Parametern gebaut. Die Choice Function misst im Original Zeit; hier zählen Auswertungen und Schritte, und ihre Formel folgt dem Muster, nicht dem Original. Kein irace, kein HyFlex, kein Fremdcode.
3. **Referenz:** Der Abstand bezieht sich auf den besten bekannten Wert je Instanz (das Minimum aus langen Referenzläufen und allen Messläufen), nicht auf ein Optimum. Gepaarte Unterschiede zwischen zwei Regeln hängen daran nur über den Nenner (der Unterschied wird durch die Referenz geteilt; in 30 von 120 Instanzen unterboten Messläufe die Referenzläufe).
4. **Akzeptanz:** Nur drei Akzeptanzregeln, hier als Bedingung der Gutschrift. Das Vorzeichen des Lerngewinns hängt an der Akzeptanzregel; die Zerlegung von Akzeptanz und Auswahl und die Länge der Liste von Late Acceptance gehören der Demo „Akzeptanz mal Auswahl“.
5. **Gutschrift:** „Nur Bestwert“ ist die einfachste Entflechtung. Eine Belohnung über Folgen von Anwendungen (Verschlechtern, dann Reparieren) ist nicht gebaut und nicht gemessen. Die Kontrolle „weniger lernen“ ist nur für die Choice Function gemessen.
6. **Zählung:** Die Zählungen über viele Zellen stehen ohne Korrektur für Mehrfachvergleiche; die Paare je Akzeptanzregel sind nicht unabhängig (gleiche Regel, mehrere Belohnungsformen). Sie sind ein Bild, keine Einzelbefunde.
7. **Zähleinheit:** Gleiche Auswertungszahl vergleicht Regeln mit verschiedenem Verwaltungsaufwand nur begrenzt; Rechenzeit ist hier kein Befund.
8. **Einstellung:** Je Regel sind nur ein Parameter und drei Werte gemessen, unter zwei Akzeptanzregeln. Für andere Bereiche ist nichts ausgeschlossen.
9. **Nicht gemessen:** zustandsabhängige Auswahl, eine Lernphase als Parameter, die Verzerrung von Schätzungen nach adaptiver Auswahl, andere Zugmengen als alle acht und ohne `2opt_b5`, Sintflut und Annealing.
10. **Nutzen im Betrieb:** nicht belegt. Die Rundtouren sind erzeugt; es gibt keine reale Datenquelle, und in den gelesenen Quellen gab es keine Messung, ob eine solche Auswahlregel in Logistik, Lager oder Fertigung bessere Entscheidungen liefert.
"""

FORMELN = (
    ("Länge der Rundtour", r"L(t)=\sum_{k=1}^{n} d_{t_k t_{k+1}},\qquad t_{n+1}=t_1"),
    ("Längenänderung von 2-opt (Stück $a \\ldots b$ umgedreht, $p$ vor $a$, $q$ nach $b$)", r"\Delta_{2\text{-opt}}=d_{pb}+d_{aq}-d_{pa}-d_{bq}"),
    ("Budget", r"\sum_{k}c_{h_k}\le B,\qquad c_h=1,\quad c_{\mathrm{2opt\_b5}}\le 5"),
    ("Akzeptanz „nur besser“", r"\Delta_k<0"),
    ("Akzeptanz Rekord-zu-Rekord", r"\Delta_k\le 0\ \ \text{oder}\ \ L(t')\le(1+\rho)\,L^{*}_{k-1},\qquad \rho=0{,}01"),
    ("Akzeptanz Late Acceptance", r"\Delta_k\le 0\ \ \text{oder}\ \ L(t')\le\ell_{k \bmod \Lambda},\qquad \Lambda=50"),
    ("Standardbelohnung", r"r_k=\min\Bigl(1,\ \frac{\max(0,-\Delta_k)}{c_{h_k}\,\bar e}\Bigr),\qquad \bar e=\frac{L(t_0)}{n}"),
    ("Belohnung „nur Bestwert“ (ihre Summe der Senkungen ist der Nettogewinn)",
     r"r_k^{\mathrm{best}}=\min\Bigl(1,\ \frac{L^{*}_{k-1}-L^{*}_{k}}{c_{h_k}\,\bar e}\Bigr),\qquad \sum_k\bigl(L^{*}_{k-1}-L^{*}_{k}\bigr)=L(t_0)-L^{*}_{K}"),
    ("Gutschrift je Zugart und Verbesserungsarbeit je Nettogewinn", r"G_h=\sum_{k:\,h_k=h} r_k,\qquad W=\frac{\sum_k \max(0,-\Delta_k)}{L(t_0)-L^{*}_{K}}\ \ge 1"),
    ("Lernautomat (nur nach $r>0$; danach $p_j\\ge 0{,}01$ und neu normiert; der Boden gilt vor dem Normieren)", r"p_j\leftarrow(1-a)\,p_j+a\,[j=h],\qquad a=0{,}05"),
    ("Q-Lernen mit einem Zustand", r"Q_h\leftarrow Q_h+\alpha\bigl(r+\gamma\max_j Q_j-Q_h\bigr),\qquad \alpha=0{,}1,\ \gamma=0{,}5,\ \varepsilon=0{,}1"),
    ("Choice Function: Wertung ($i$ ist die zuletzt angewandte Zugart)",
     r"F_j=\varphi\Bigl(\frac{f_{1,j}}{\max_l f_{1,l}}+\frac{f_{2,i,j}}{\max_l f_{2,i,l}}\Bigr)+(1-\varphi)\,\frac{\min(\tau_j,50)}{50}"),
    ("Choice Function: Fortschreiben nach der Anwendung von $h$",
     r"f_{1,h}\leftarrow r+\alpha_{\mathrm{cf}}\,f_{1,h},\qquad f_{2,i,h}\leftarrow r+\alpha_{\mathrm{cf}}\,f_{2,i,h},\qquad \alpha_{\mathrm{cf}}=0{,}9"),
    ("UCB mit Vergessen", r"s_j=\frac{S_j}{n_j\,r_{\max}}+c\,\sqrt{\frac{2\ln N}{n_j}},\qquad c=0{,}2,\ \gamma=0{,}995"),
)

FORMEL_NACHSATZ = """
**Was die Formeln nicht zeigen.** Choice Function: $\\varphi$ startet bei 0,5, springt nach einem Erfolg ($r>0$) auf 0,99 und sinkt sonst je
Schritt um 0,01 bis auf 0,01; Gleichstände löst ein Zufallswert unter $10^{-9}$. UCB wählt zuerst jede Zugart einmal; $S_j$ und $n_j$ werden je
Anwendung mit $\\gamma$ abgewertet. Der Zufallsgradient behält die Zugart nach $r>0$ und würfelt sonst neu. „Ohne Kostenbezug“ lässt $c_h$ im
Nenner weg; „Rang“ und „gleitendes Mittel“ stehen in der Tabelle der Belohnungen oben. Eine Verbesserung zählt erst ab $10^{-9}$.

**Beweisbar und als Eigenschaft getestet:** $W\\ge 1$ (jede strenge Verkürzung wird unter allen drei Akzeptanzregeln angenommen, und der Bestwert
fällt höchstens um die Summe der Verkürzungen). Unter „nur besser“ gilt $W=1$ und $r^{\\mathrm{best}}=r$, solange die Kappung bei 1 nicht greift.

**Quellen (mit Belegstufe: V = im Volltext eingesehen, A = nur Zusammenfassung, S = Sekundärquelle).** Burke u. a. 2013, „Hyper-heuristics: a survey
of the state of the art“, JORS 64(12) (V: Auswahl und Akzeptanz als getrennte Bausteine, Kreditzuweisung als Begriff der adaptiven Operatorwahl).
Bilgin, Özcan, Korkmaz 2007 und Özcan u. a. 2008 (V: die Akzeptanz wirkte dort stärker als die Auswahl; Prüfungspläne und Testfunktionen, keine
Touren). Drake, Özcan, Burke 2012 (V: Choice Function mit Paarterm und Zeit). Cowling u. a. 2000 und 2001 (nur aus zweiter Hand, Original nicht
gelesen). Fialho u. a. 2010 (S: Kreditzuweisung als Baustein bandit-basierter Operatorwahl). Lissovoi u. a. 2020 (A: Lernen verbessert nicht
notwendig; Bit-Funktionen). Branke u. a. 2016 (V: begrenzte Gültigkeit des Vergleichs bei gleicher Auswertungszahl). Die UCB-Grundform steht in
der Demo „bandit-demo“; die Originalarbeit wurde hier nicht eingesehen. Nichts davon ist neu; neu ist nur die Vorführung mit Zähleinheit.
"""

NACHBARN = """
**Verwandte Demos.** „Heuristiken auswählen statt Lösungen“ (Zufallsmischung gegen einzelne Zugart) und „Die Zugmenge entscheidet“ (welche
Zugarten in die Menge gehören) sind die Vorgänger in dieser Linie; „Akzeptanz mal Auswahl“ folgt. Die Bandit-Mechanik (UCB1, Regret) zeigt die
Demo „bandit-demo“ mit festen Erfolgswahrscheinlichkeiten; hier hängt der Erfolg einer Zugart
von der aktuellen Tour ab.
"""


def regel_name(regel: str) -> str:
    return C.REGEL_ANZEIGE[regel]


def stufe_name(faktor: int) -> str:
    return C.STUFEN_ANZEIGE[faktor]
