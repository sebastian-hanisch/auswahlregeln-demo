# Wer belohnt wen? Kreditzuweisung bei der Wahl der Zugart – Streamlit-Demo

Dritte Demo der Linie **„Hyperheuristiken erklärt“** unter den „Konzepten“ der Website „Sebastian Hanisch – Operations Research und Machine Learning“. Sie steht auf dem Ast **Auswählen**. Vorgänger ist „Die Zugmenge entscheidet“ (`zugmenge-demo`): dort ist die Auswahlregel gegeben, und die Menge der Zugarten wird variiert. Hier bleibt die Menge fest (alle acht Zugarten), und es variieren die **Regel**, die die Zugart wählt, und die **Gutschrift**, aus der sie lernt. Nachfolger ist „Akzeptanz mal Auswahl“, das die Wechselwirkung von Akzeptanzregel und Auswahlregel zerlegt und die Länge der Liste von Late Acceptance führt; beides steht hier nur als Verweis.

Das Fahrzeug ist wie in der ganzen Linie eine erzeugte Rundtour (Städte in der Ebene, kürzeste geschlossene Tour gesucht; ein Modell, kein Datensatz). Instanzen, Zugarten, Akzeptanzregeln, Suche und Zufallsströme sind aus der Wurzel-Demo `hyperheuristik-demo` kopiert, vier Auswahlregeln und die Referenzwerte aus `zugmenge-demo` (Kopier-Tests). **Die Akzeptanzregel ist in der Voreinstellung Rekord-zu-Rekord wie in `zugmenge-demo`, in der Wurzel-Demo ist es „nur besser“.**

## Kernfrage

Wer bekommt die Gutschrift, wenn eine Hyperheuristik die Zugart nach Erfolg wählt und die Suche zwischendurch Verschlechterungen annimmt, und schlägt das den Zufall?

**Befund als Aufhänger:** Dieselbe Regel, dieselben acht Zugarten, dieselben 120 Instanzen, dasselbe kleine Budget: Die Choice Function liegt unter Rekord-zu-Rekord vor der Zufallswahl und unter Late Acceptance dahinter. Die Zahlen mit ihren Voraussetzungen stehen unter „Befunde“.

Die Rundtouren sind erzeugt; es gibt keine reale Datenquelle, und in den gelesenen Quellen gab es keine Messung, ob eine solche Auswahlregel in Logistik, Lager oder Fertigung bessere Entscheidungen liefert. Gezählt werden Auswertungen (bewertete Kandidaten); gleiche Auswertungszahl vergleicht Regeln mit verschiedenem Aufwand nur begrenzt. Die Regeln sind eigene, vereinfachte Umsetzungen mit nicht abgestimmten Parametern; die Choice Function misst im Original Zeit.

## Befunde und Korrekturen gegenüber der Vormessung

Die Planung stützte sich auf Vormessungen mit dem Zufallsgenerator von numpy (90 Instanzen × 4 Läufe und 180 Instanzen × 20 Läufe, andere Referenzwerte). Der Bau hat mit den Zufallsströmen der App (SplitMix64) neu gemessen: **120 Instanzen** (3 Familien × n = 30 und 60 × Instanzen 0 bis 19, dieselben wie in `zugmenge-demo`) × **3 Läufe**, 116 Varianten, 375 840 000 Auswertungen. Die Spalte links ist die Vormessung (nicht im Test), rechts steht die Neumessung (Abschnitt „Befunde“, im Test).

| Aussage der Planung (Vormessung) | Neumessung |
|---|---|
| „Keine gelernte Regel schlägt Zufall“ als Hauptaussage | gilt in dieser Messung bei beiden Budgets unter Late Acceptance und bei 200·n mit der Standardbelohnung auch unter „nur besser“ und Rekord-zu-Rekord (0 von je 5 Regeln vor Zufall); bei 50·n liegen unter Rekord-zu-Rekord vier von den fünf Regeln ohne Zufall (Choice Function, Lernautomat, Q-Lernen, UCB; nicht der Zufallsgradient) mit der Standardbelohnung vor Zufall, unter „nur besser“ Q-Lernen |
| Rekord-zu-Rekord, 50·n, Standardbelohnung: Choice Function +0,48, Lernautomat +0,63, Q-Lernen +0,60, UCB −0,18 | deutlicher: siehe „Befunde“ (Choice Function, Lernautomat, Q-Lernen und UCB mit Marke, UCB +0,51) |
| Late Acceptance, 50·n: Choice Function −1,95, Lernautomat −1,44, Q-Lernen −1,72, UCB −0,39 | gleiche Richtung, kleinere Beträge; UCB ohne belegten Unterschied |
| 18 von 51 Zellen mit Vorteil bei kleinem, 0 von 51 bei großem Budget (17 Paare) | mit dem Zufallsgradienten 18 Paare und 54 Zellen; bei großem Budget **nicht 0**: vier Zellen unter Rekord-zu-Rekord erreichen die Marke knapp (bei anderen Bootstrap-Ziehungen drei oder vier), keine davon mit der Standardbelohnung |
| Anteil auf `2opt_b5` unter Late Acceptance: Choice Function 63,6 %, Lernautomat 73,8 %, Q-Lernen 32,7 % | gleiche Größenordnung (siehe „Befunde“) |
| Kreditregel erfüllt für 2 von 3 Regeln (Choice Function, Lernautomat) | bestätigt |
| „Kredit“ gegen „weniger lernen“ nicht getrennt (Messlücke) | **gemessen:** eine verdünnte Choice Function ist bei großem Budget nicht um die Marke schlechter als die mit „nur Bestwert“ (Gleichwertigkeit ist nicht gezeigt); die Gutschrift ist für sie nicht als Ursache belegt |
| Gutschrift ohne Nettogewinn unter Late Acceptance und Rekord-zu-Rekord nicht gemessen | gemessen (siehe „Befunde“); der Anteil ist auch unter Rekord-zu-Rekord hoch |
| ohne `2opt_b5` nur bei 50·n gemessen | auch bei 200·n gemessen (Tabelle in der App, Kernfrage 4) |
| „Kein Parameterartefakt“: 0 von 18 Varianten schlagen Zufall unter Late Acceptance | 20 Varianten; unter Late Acceptance bei 50·n **eine** mit Marke (UCB mit c = 1,0), bei 200·n keine. Neu: unter Rekord-zu-Rekord gemessen |
| `rank`, `ma`, `r1` ändern die Güte der Choice Function unter Late Acceptance nicht erkennbar (Intervalle mit 0) | bestätigt (Tabelle in der App; Zugart-Anteile nicht geprüft) |
| „Nur Bestwert“ ist unter „nur besser“ bitgleich zur Standardbelohnung | bestätigt (Eigenschaftstest) |

## Modell

Eine Suche startet mit der Nächster-Nachbar-Tour. In jeder Anwendung wählt die **Auswahlregel** eine der Zugarten, die Zugart bewertet einen zufälligen Vorschlag (eine Auswertung; `2opt_b5` bis zu fünf), die **Akzeptanzregel** entscheidet, ob er bleibt, und die Regel bekommt eine **Belohnung** in [0, 1]. Das Budget ist eine Zahl von Auswertungen (50·n oder 200·n). Die Formeln (Länge, Längenänderung von 2-opt, drei Akzeptanzregeln, Belohnungen, Gutschrift, die Regeln) stehen im Expander „📐 Mathematische Formulierung“ der App. Zwei Kennzahlen der Gutschrift:

* **W** = Summe aller strengen Verkürzungen der aktuellen Tour, geteilt durch den Nettogewinn (Startlänge minus Bestwert). W ≥ 1; W = 1 gilt, wenn vor dem letzten Bestwert keine Verlängerung angenommen wurde und danach keine Verkürzung mehr vorkam, sonst ist W > 1 (Eigenschaftstest).
* **Anteil ohne neuen Bestwert** = Anteil der Standard-Gutschrift, der an Anwendungen ging, nach denen der Bestwert nicht fiel.

## Methodik

* **Acht Zugarten** (wie in der Linie): `swap`, `insert`, `2opt`, `2opt_lokal`, `oropt2`, `oropt3`, `dbridge`, `2opt_b5`.
* **Sechs Auswahlregeln:** Zufall, Zufallsgradient, Choice Function (Vergessen α = 0,9), UCB mit Vergessen (c = 0,2, γ = 0,995), Lernautomat (Linear Reward-Inaction, a = 0,05, Boden 0,01 vor dem Normieren; danach liegt er knapp darunter), Q-Lernen mit einem Zustand (α = 0,1, γ = 0,5, ε = 0,1).
* **Drei Akzeptanzregeln:** „nur besser“, Rekord-zu-Rekord (Toleranz 1 %), Late Acceptance (Liste der Länge 50).
* **Fünf Belohnungsformen:** Standard (Verkürzung der aktuellen Tour je Auswertung, in mittleren Kantenlängen der Starttour, höchstens 1), „nur Bestwert“ (Senkung des Bestwerts statt der aktuellen Tour), ohne Kostenbezug, Rang unter den letzten 30, relativ zum gleitenden Mittel. Der Lernautomat liest nur, ob die Belohnung größer als 0 ist; für ihn sind nur Standard und „nur Bestwert“ gemessen.
* **Vergleichszahl:** Abstand zum besten bekannten Wert je Instanz in Prozent (Minimum aus Referenzläufen mit 1000·n Auswertungen und allen Messläufen; ein Messlauf unterbot die Referenz in 30 von 120 Instanzen). Unterschied = Abstand(Zufall) − Abstand(Regel), gepaart je Instanz (gleiche Starttour, gleicher Zufallsstrom), Mittel über 3 Läufe; Intervall = Bootstrap 95 % über die 120 Instanzen (4000 Ziehungen).
* **Klassen (gesetzt, nicht abgeleitet):** „vor Zufall“ ab +0,25 Punkte mit Intervall über 0, „hinter Zufall“ ab −0,10 Punkte mit Intervall unter 0, sonst „nicht zu unterscheiden“.
* **Kreditregel (vor der Messung festgelegt):** „nur Bestwert“ senkt den Anteil von `2opt_b5` um mindestens 20 Prozentpunkte **und** verbessert die Güte bei beiden Budgets um mindestens 0,5 Punkte mit Intervall über 0.
* **Kontrolle „weniger lernen“ (vor der Messung festgelegt):** eine Choice Function, die mit Wahrscheinlichkeit p würfelt; p wird auf 30 anderen Instanzen (1000 bis 1004 je Familie und n) im Raster 0,05 bis 0,95 so gewählt, dass ihr Anteil auf `2opt_b5` dem der Choice Function mit „nur Bestwert“ am nächsten kommt. Ist sie bei 200·n mindestens 0,3 Punkte schlechter (Intervall über 0), spricht das für die Gutschrift; liegt sie unter 0,3 oder ist sie besser, für „weniger lernen“.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen dieses Abschnitts: eingefrorene Messung (`asw_frozen.json`), 120 erzeugte Instanzen mit 30 oder 60 Städten aus drei Familien, 3 Läufe je Instanz, Budget 50·n („klein“) und 200·n („groß“) Auswertungen, eigene Umsetzungen mit festen Parametern. Unterschiede in Prozentpunkten des Abstands, in Klammern das 95-%-Intervall. Die Sätze werden von `tools/asw_readme.py` aus derselben Quelle geschrieben wie die Texte der App.

<!-- MESSUNG:START -->
**Schlägt eine Regel, die den Erfolg beachtet, den Zufall?** Ob eine Regel, die den Erfolg der Zugarten beachtet, die Zufallswahl schlägt, hängt in dieser Messung an der Akzeptanzregel und am Budget. Bei kleinem Budget (50·n Auswertungen) liegen Choice Function, Lernautomat und Q-Lernen mit der Standardbelohnung unter Rekord-zu-Rekord +1,14 / +0,84 / +0,88 Prozentpunkte vor Zufall (alle drei über der gesetzten Marke 0,25, siehe Methodik, mit Intervall über 0) und unter Late Acceptance −1,57 / −1,18 / −1,36 Punkte dahinter (alle drei mit Intervall unter 0). Unter Rekord-zu-Rekord liegt bei kleinem Budget auch UCB vor Zufall (+0,51 [+0,15; +0,88]), der Zufallsgradient nicht (+0,23 [−0,10; +0,55]); von den fünf Regeln ohne Zufall (sechs mit Zufall) erreichen dort also 4 die Marke. Unter „nur besser“ erreicht von den fünf Regeln nur Q-Lernen die Marke (+0,50 [+0,13; +0,87]). Bei großem Budget (200·n) erreicht mit der Standardbelohnung keine der 15 Zellen (fünf Regeln × drei Akzeptanzregeln) die Marke, 4 liegen hinter Zufall. Über alle 18 Paare aus Regel und Belohnung sind es bei kleinem Budget 21 von 54 Zellen vor und 14 hinter Zufall, bei großem 4 vor und 13 dahinter. Je Akzeptanzregel (18 Paare): „nur besser“ 5 vor und 0 hinter Zufall bei kleinem, 0 und 2 bei großem Budget; Rekord-zu-Rekord 16 vor und 0 hinter Zufall bei kleinem, 4 und 0 bei großem Budget; Late Acceptance 0 vor und 14 hinter Zufall bei kleinem, 0 und 11 bei großem Budget. Die Zellen mit Vorsprung bei großem Budget liegen knapp an der Marke; bei anderen Bootstrap-Ziehungen sind es drei oder vier. Der größte gemessene Vorsprung bei großem Budget (nachträglich unter 54 Zellen gewählt) ist +0,29 [+0,02; +0,57] (Choice Function, Belohnung „ohne Kostenbezug“, Rekord-zu-Rekord). Der Zufallsgradient ist in allen sechs Zellen nicht von Zufall zu unterscheiden. Die Zählungen stehen ohne Korrektur für Mehrfachvergleiche, und die Paare sind nicht unabhängig.

**Wohin geht die Auswahl?** **Eingefrorene Messung, Anteil der Zugart `2opt_b5` bis 200·n, Standardbelohnung:** Unter Late Acceptance setzt die Choice Function 59,9 % der Anwendungen (88,2 % der Auswertungen) auf `2opt_b5`, der Lernautomat 72,7 % der Anwendungen (93,0 % der Auswertungen), Q-Lernen 32,6 % der Anwendungen (70,8 % der Auswertungen); bei Gleichverteilung wären es 12,5 % und 41,7 %. Unter Rekord-zu-Rekord sind es 49,3 % der Anwendungen (82,9 % der Auswertungen), 68,1 % der Anwendungen (91,4 % der Auswertungen) und 32,9 % der Anwendungen (71,1 % der Auswertungen), unter „nur besser“ 17,8 %, 40,5 % und 16,1 % der Anwendungen. UCB verteilt unter allen drei Akzeptanzregeln fast gleichmäßig (12,7 bis 12,9 % auf `2opt_b5`). Ein hoher Anteil sagt allein nichts über die Güte: unter Rekord-zu-Rekord setzen Choice Function und Lernautomat ebenfalls rund die Hälfte und mehr ihrer Anwendungen auf `2opt_b5` und liegen bei kleinem Budget trotzdem vor Zufall (Kernfrage 2).

**Wer bekommt das Lob für eine Reparatur?** **Eingefrorene Messung, bis 200·n, Mittel über 120 Instanzen:** Unter Late Acceptance gehen bei der Zufallswahl 46,7 % (W = 2,97) der Standard-Gutschrift an Anwendungen, nach denen der Bestwert nicht fiel, bei der Choice Function 71,6 % (W = 8,36), beim Lernautomaten 67,6 % (W = 7,11), bei Q-Lernen 67,5 % (W = 6,77), bei UCB 51,5 % (W = 3,39). Unter Rekord-zu-Rekord sind es 39,1 % (W = 2,80) (Zufall) und 44,4 % (W = 3,29) (Choice Function), unter „nur besser“ 0 % mit W = 1 (Kontrolle, als Eigenschaft getestet). Bei der Choice Function unter Late Acceptance bekommt `2opt_b5` 73,5 % der Standard-Gutschrift und 51,6 % der Gutschrift nach „nur Bestwert“. Dass die Gutschrift ohne neuen Bestwert den Rückstand verursacht, zeigt diese Zählung nicht: auch unter Rekord-zu-Rekord liegt ihr Anteil bei der Choice Function bei 44,4 % (Zufall 39,1 %; unter Late Acceptance 71,6 % gegen 46,7 %), und dort liegt die Regel bei kleinem Budget vorn.

**Ändert eine andere Gutschrift etwas?** **Vorab-Regel unter Late Acceptance** (Belohnung „nur Bestwert“ statt Standard; Anteil von `2opt_b5` an den Anwendungen bis 200·n): Choice Function: Anteil 59,9 → 21,5 % (Senkung 38,4 Punkte), Güte +0,67 [+0,43; +0,92] bei kleinem und +1,44 [+1,17; +1,69] bei großem Budget, gegen Zufall dann −0,90 und −0,08. Lernautomat: Anteil 72,7 → 39,7 % (Senkung 33,0 Punkte), Güte +0,93 [+0,66; +1,20] bei kleinem und +1,20 [+0,94; +1,45] bei großem Budget, gegen Zufall dann −0,24 und −0,32. Q-Lernen: Anteil 32,6 → 20,0 % (Senkung 12,6 Punkte), Güte +0,81 [+0,54; +1,10] bei kleinem und +0,71 [+0,48; +0,95] bei großem Budget, gegen Zufall dann −0,54 und +0,07. Die Vorab-Regel (Senkung des Anteils um mindestens 20 Punkte und Güte um mindestens 0,5 Punkte mit Intervall über 0 bei beiden Budgets) erfüllen 2 von 3 Regeln (Choice Function, Lernautomat); es fehlt: Q-Lernen (Senkung 12,6 statt mindestens 20 Punkte). **Gegenprobe unter Rekord-zu-Rekord:** Dort senkt „nur Bestwert“ den Anteil ebenfalls (49,3 → 21,2 % bei der Choice Function), die Güte ändert sich aber in keiner der sechs Zellen mit Intervall ohne 0 (Choice Function −0,20 [−0,47; +0,07] und +0,08 [−0,14; +0,32]; Lernautomat −0,07 [−0,40; +0,27] und +0,03 [−0,18; +0,25]; Q-Lernen −0,29 [−0,60; +0,02] und −0,18 [−0,39; +0,05]). Unter „nur besser“ sind beide Belohnungen dieselbe (Kontrolle).

**Gutschrift oder weniger lernen?** **Kontrolle „weniger lernen“ (nur Choice Function, Late Acceptance):** Eine Choice Function mit Standardbelohnung, die in 60 % der Anwendungen würfelt statt ihrer Wertung zu folgen, setzt 22,0 % der Anwendungen auf `2opt_b5` (Ziel: die 21,5 % der Choice Function mit „nur Bestwert“; die Stärke wurde auf 30 anderen Instanzen gesucht). Ihr Abstand minus der Abstand mit „nur Bestwert“: −0,36 [−0,67; −0,06] bei kleinem und −0,08 [−0,31; +0,14] bei großem Budget (negativ: die verdünnte Regel ist besser). Nach der vorab gesetzten Marke von 0,3 Punkten bei großem Budget ist bloßes Verdünnen hier nicht um die Marke schlechter als die andere Belohnung (Gleichwertigkeit ist damit nicht gezeigt); dass die bessere Gutschrift der Grund der Besserung ist, belegt diese Messung für die Choice Function nicht. Gegen Zufall liegt die verdünnte Regel bei −0,54 [−0,86; −0,23] (klein) und +0,00 [−0,27; +0,27] (groß).

**Liegt es an der Einstellung der Regel?** **Eingefrorene Messung, 20 Varianten je Akzeptanzregel** (je Regel ein Parameter mit zwei Werten neben dem Standard): Unter Late Acceptance liegen bei kleinem Budget 1 von 20 Varianten vor und 16 hinter Zufall, bei großem 0 und 16. Die beste Variante bei kleinem Budget ist UCB mit c = 1,0, Belohnung „Standard“ mit +0,37 [+0,06; +0,70]; sie ist nachträglich unter 20 gewählt. Unter Rekord-zu-Rekord liegen bei kleinem Budget 18 von 20 vor Zufall und 0 dahinter, bei großem 2 und 0. Die Einstellung verschiebt die Zahlen; das Vorzeichen folgt bei kleinem Budget der Akzeptanzregel (2 bzw. 20 von 20 Varianten positiv unter Late Acceptance bzw. Rekord-zu-Rekord), bei großem Budget ist es unter Rekord-zu-Rekord gemischt (13 von 20 positiv; unter Late Acceptance 3). Gemessen sind je Parameter nur drei Werte; für andere Bereiche ist nichts ausgeschlossen.
<!-- MESSUNG:ENDE -->

**Handbeispiel (exakt, ohne Zufall).** Sechs Städte mit ganzzahligen Manhattan-Abständen, Starttour der Länge 30 (Optimum 24) und mittlerer Kantenlänge 30 / 6 = 5, drei Zugarten mit je einer Auswertung, Late Acceptance mit einer Liste der Länge 2, fünf vorgegebene Züge: A kürzt die Tour von 30 auf 28, B verlängert sie auf 30, C kürzt auf 28, B verlängert wieder auf 30, C kürzt auf 28. Der Bestwert fällt nur im ersten Schritt von 30 auf 28; die Summe der Verkürzungen ist 6, der Nettogewinn 2, also W = 3. Die Belohnung eines Zuges ist die Verkürzung geteilt durch Auswertungen mal mittlere Kantenlänge, hier 2 geteilt durch 5, also 2/5, je Verkürzung um 2; die Gutschrift einer Zugart ist die Summe ihrer Belohnungen, kein Anteil an den Schritten. Nach der Standardform bekommt die reparierende Zugart C die Gutschrift 4/5 (zweimal 2/5) und die Zugart A, die den Bestwert senkte, 2/5; nach „nur Bestwert“ bekommt A 2/5 und C 0. Mit der Standardform ziehen Lernautomat (Wahrscheinlichkeit 9199/24000 für C), Q-Lernen und Choice Function danach C vor, mit „nur Bestwert“ alle drei A. Unter „nur besser“ werden die vier Züge nach dem ersten abgelehnt, und W = 1.

### Zahl gegen Test

| Zahl der README | Test | Art |
|---|---|---|
| alle Sätze zwischen den Marken (Unterschiede, Intervalle, Zählungen, Anteile, W, Kreditregel, Verdünnung, 20 Varianten) | `test_claims::test_readme_block_ist_aus_der_messung_geschrieben` und die Einzeltests in `test_claims.py`, die jede Zahlengruppe unabhängig aus der Datei nachrechnen | exakt aus der Datei; Intervalle als Band ±0,03 |
| die Datei selbst | `test_frozen::test_ausschnitt_neu_gerechnet_stimmt_als_band` (3 Instanzen × 8 Varianten neu gerechnet) | Band 0,002 Punkte |
| 375 840 000 Auswertungen, 116 Varianten, 120 Instanzen, 3 Läufe, 30 von 120 unterboten | `test_frozen`, `test_claims::test_groesse_der_messung` | exakt |
| Gleichverteilung 12,5 % und 41,7 % | `test_claims::test_gleichverteilung` | exakt (Brüche) |
| Handbeispiel (30, 24, 28, W = 3, 4/5, 2/5, 9199/24000) | `test_handbeispiel.py` | exakt (Brüche) |
| unter „nur besser“ W = 1, Anteil 0, beide Belohnungen gleich; W = 1 nach der Bedingung der Methodik | `test_eigenschaften_auswahl.py` | exakt |
| Abgleich mit `zugmenge-demo` (gleiche Läufe bei 50·n) | `test_frozen::test_standardlaeufe_sind_dieselben_wie_in_der_zugmengen_demo_falls_vorhanden` | Band 0,02 Punkte |
| linke Spalte der Tabelle „Vormessung“ | Messung der Planung, nicht im Test | – |

## Ehrliche Grenzen
<!-- ANNAHMEN:START -->
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
<!-- ANNAHMEN:ENDE -->

Weitere Punkte:

* **Verhältnis zu den Nachbarn der Linie.** `zugmenge-demo` misst dieselben Läufe für Choice Function, Lernautomat und Q-Lernen bei 50·n (dort als Kontrollpunkt eines Laufs bis 400·n) und nennt für Rekord-zu-Rekord +1,15 / +0,84 / +0,88 und für Late Acceptance −1,57 / −1,18 / −1,36; die Zahlen hier weichen um höchstens 0,02 Punkte ab, weil die Referenz das Minimum über andere Läufe ist. Die Anteile auf `2opt_b5` dort (37,9 / 79,9 / 23,5 % unter Late Acceptance) zählen bis 400·n, hier bis 200·n.
* **Die Mini-Messreihe der App** (6 bis 30 Instanzen) trennt nur große Unterschiede; sie zeigt nicht in jedem Ausschnitt das Vorzeichen der eingefrorenen Messung. Ihre Halbbreite wird je Klick angezeigt, nicht hier behauptet.
* **Deutung, nicht gemessen:** Warum Late Acceptance mit einer Liste der Länge 50 das Lernen bestraft, ist hier nicht isoliert. Die Kontrolle zeigt nur, dass die Besserung durch „nur Bestwert“ bei der Choice Function auch durch selteneres Folgen der Wertung zu haben ist.
* **Plattform:** gemessen unter Windows; die Läufe benutzen Grundrechenarten, die Wurzel und eine Potenz (das Vergessen in UCB), der Logarithmus in UCB kommt aus der plattformfesten Zufallsvorlage. Eine Linux-Prüfung steht aus.

## Befunde und Korrekturen gegenüber dem Plan

* **120 Instanzen × 3 Läufe** statt 90 × 4: dieselben Instanzen, Starttouren und Zufallsströme wie `zugmenge-demo`, damit beide Demos an denselben Läufen hängen.
* **Belohnung und Einstellung werden nicht ausgeblendet**, sondern zeigen nur die Werte, die die gewählte Regel kennt, und sind gesperrt, wenn es nur einen gibt.
* **Ein Regler „Einstellung der Regel“** (Standard, kleinerer, größerer Wert) statt vier Parameterregler; 20 statt 18 Varianten, gemessen unter Late Acceptance **und** Rekord-zu-Rekord.
* **Late Acceptance mit einer Liste der Länge 10** ist hier weder Regler noch Tabellenzeile (gehört „Akzeptanz mal Auswahl“).
* **Klasse „hinter Zufall“** ab −0,10 Punkten wie im Plan (asymmetrisch zur Marke +0,25); `zugmenge-demo` benutzt ±0,25.
* **Zufallsgradient:** am Anfang würfelt er (die Vormessung begann mit der ersten Zugart).
* **Bibliotheken zur Laufzeit:** Streamlit, Plotly und NumPy (NumPy für den blockweisen Zufallsstrom und das Bootstrap der kopierten Module; der Plan sah reines Python vor).
* **Kein Literaturtest für UCB1:** die Originalarbeit wurde nicht eingesehen; der Test prüft die Grundform der Formel an einer Handrechnung.

## Bewusst nicht enthalten

Thompson-Sampling und kontextuelle Bandits; zustandsabhängige Auswahl; Belohnung über Folgen von Anwendungen; die Listenlänge von Late Acceptance, Sintflut und Annealing („Akzeptanz mal Auswahl“); weitere Zugmengen (`zugmenge-demo`); die Verzerrung von Schätzungen nach adaptiver Auswahl; Offline-Training der Auswahl und Gesamtkosten; eine Lernphase als Parameter; irace und HyFlex; Korrektur für Mehrfachvergleiche; Städtezahlen außer 30 und 60; Rechenzeit als Befund.

## Quellen

Mit Belegstufe (V = im Volltext eingesehen, A = nur Zusammenfassung, S = Sekundärquelle). Burke u. a. (2013), „Hyper-heuristics: a survey of the state of the art“, Journal of the Operational Research Society 64(12) (V: Auswahl und Akzeptanz als getrennte Bausteine, Kreditzuweisung als Begriff der adaptiven Operatorwahl). Bilgin, Özcan, Korkmaz (2007) und Özcan u. a. (2008) (V: die Akzeptanz wirkte dort stärker als die Auswahl; Prüfungspläne und Testfunktionen, keine Touren). Drake, Özcan, Burke (2012) (V: Choice Function mit Paarterm und Zeit). Cowling u. a. (2000, 2001) (nur aus zweiter Hand, Original nicht gelesen). Fialho u. a. (2010) (S: Kreditzuweisung als Baustein bandit-basierter Operatorwahl). Lissovoi u. a. (2020) (A: Lernen verbessert nicht notwendig; Bit-Funktionen). Branke u. a. (2016) (V: begrenzte Gültigkeit des Vergleichs bei gleicher Auswertungszahl). Die UCB-Grundform steht in der Demo `bandit-demo`; die Originalarbeit wurde hier nicht eingesehen. Die App nennt dieselben Quellen im Expander „📐 Mathematische Formulierung“; Titel und Fundstelle stehen nur bei Burke u. a. (2013), bei den übrigen sind nur Autoren und Jahr genannt.

## Tests

843 Tests (`pytest --collect-only -q tests`), Laufzeit in einem Prozess rund 100 Sekunden (gemessen). Zusammensetzung: kopierter Rundtour-Kern (Zufall, Szenario, Zugarten, Akzeptanz, Suche, Statistik, vier Auswahlregeln) und Kopier-Tests; eigene Regeln und Belohnungen je Einheit; Handbeispiel in Brüchen; Orakel (Regeln gegen Brüche auf 50 Zufallsfolgen, Nachrechner der Spur, Optimum per Aufzählung bei 8 Städten); Eigenschaften und Zweig-Tests; eingefrorene Messung (Aufbau, Neurechnung als Band); Aussagen der README; Verdikte; Randfälle und Reglermaximum; Presets, Layout, App-Läufe, Footer, Laufzeit-Importe.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Seite: Kopf, Einleitung, fünf Kernfragen mit Experiment, Annahmen, Formeln |
| `asw_constants.py` | Zugarten, Regeln, Belohnungen, Marken, Reglergrenzen, Presets |
| `asw_rng.py`, `asw_rngblock.py`, `asw_scenario.py`, `asw_moves.py`, `asw_accept.py`, `asw_search.py`, `asw_stats.py` | Kopien aus `hyperheuristik-demo` |
| `asw_select.py`, `asw_refs.json` | Kopien aus `zugmenge-demo` (Zufall, Choice Function, Lernautomat, Q-Lernen; Referenzwerte) |
| `asw_regeln.py` | Zufallsgradient, UCB, verdünnte Choice Function, Fassungen mit Parameter |
| `asw_belohnung.py` | die fünf Belohnungsformen |
| `asw_algorithm.py` | ein Lauf mit Gutschriftkonto (`Konto`, `run`) |
| `asw_hand.py` | das Handbeispiel |
| `asw_frozen.py`, `asw_frozen.json` | eingefrorene Messung und ihre Auswertung |
| `asw_evaluation.py` | Mini-Messreihe und Verdikte als reine Funktionen |
| `asw_saetze.py`, `asw_texts.py` | Sätze mit Messzahlen (aus der Datei gerechnet), feste Texte und Formeln |
| `asw_presets.py`, `asw_layout.py`, `asw_visualization.py`, `modul_frisch.py` | Presets und Permalink, Kopf, Abbildungen, Neuladen der Hilfsmodule |
| `tools/asw_make_frozen.py`, `tools/asw_readme.py` | erzeugen die Messdatei und den Messblock dieser README |
| `tests/` | siehe oben |

## Lokal ausführen

```
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt`, dann `pytest tests -q`.

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Hyperheuristiken: Auswählen und Erzeugen](https://sebastianhanisch.net/konzepte-hyperheuristiken.html).
