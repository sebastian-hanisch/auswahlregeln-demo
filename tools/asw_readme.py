"""Schreibt die Sätze mit Messzahlen in die README (zwischen den Marken MESSUNG:START und MESSUNG:ENDE), aus derselben Quelle wie die App.

Aufruf (aus dem Demo-Ordner):  python tools/asw_readme.py            schreibt den Block neu
                               python tools/asw_readme.py --check    prüft nur (Rückgabe 1 bei Abweichung)
Nach jeder neuen Messung (tools/asw_make_frozen.py) aufrufen; tests/test_claims.py prüft dasselbe."""

import sys
from pathlib import Path

ORDNER = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ORDNER))

import asw_saetze as SZ  # noqa: E402
import asw_texts as T  # noqa: E402

START, ENDE = "<!-- MESSUNG:START -->", "<!-- MESSUNG:ENDE -->"
A_START, A_ENDE = "<!-- ANNAHMEN:START -->", "<!-- ANNAHMEN:ENDE -->"


def block() -> str:
    teile = [
        ("Schlägt eine Regel, die den Erfolg beachtet, den Zufall?", SZ.satz_wirkung()),
        ("Wohin geht die Auswahl?", SZ.satz_anteile()),
        ("Wer bekommt das Lob für eine Reparatur?", SZ.satz_gutschrift()),
        ("Ändert eine andere Gutschrift etwas?", SZ.satz_kredit()),
        ("Gutschrift oder weniger lernen?", SZ.satz_verduennung()),
        ("Liegt es an der Einstellung der Regel?", SZ.satz_empfindlichkeit()),
    ]
    return "\n\n".join(f"**{frage}** {text}" for frage, text in teile)


def _ersetze(readme: str, start: str, ende: str, inhalt: str) -> str:
    a, b = readme.index(start) + len(start), readme.index(ende)
    return readme[:a] + "\n" + inhalt.strip("\n") + "\n" + readme[b:]


def einsetzen(readme: str) -> str:
    """Messblock und Annahmen (derselbe Text wie im Abschnitt der App) einsetzen."""
    return _ersetze(_ersetze(readme, START, ENDE, block()), A_START, A_ENDE, T.ASSUMPTIONS_MARKDOWN)


def main() -> int:
    pfad = ORDNER / "README.md"
    alt = pfad.read_text(encoding="utf-8")
    neu = einsetzen(alt)
    if "--check" in sys.argv:
        print("README-Block stimmt" if alt == neu else "README-Block weicht ab: python tools/asw_readme.py")
        return 0 if alt == neu else 1
    pfad.write_text(neu, encoding="utf-8", newline="\n")
    print("README-Block geschrieben")
    return 0


if __name__ == "__main__":
    sys.exit(main())
