# Jarvis - Persönlicher KI-Assistent mit Sprachsteuerung

Ein persönlicher KI-Assistent im Stil von Tony Starks Jarvis: läuft im Chrome-Browser,
hört per Sprache zu, denkt mit Claude, spricht mit ElevenLabs und kann selbstständig
im Internet suchen, Webseiten öffnen und den Bildschirm sehen.

## Architektur

```
Nutzer (Z) --Sprache--> Chrome Browser --Audio--> Lokaler Server (FastAPI)
                          |  Sprache zu Text            |  Systemprompt
                          |  Jarvis Orb UI               |  Aktions-System  --> Claude AI (Haiku, "Gehirn")
                          |  Audio-Ausgabe               |  Sprachausgabe   --> ElevenLabs (Text-to-Speech)
                          <--Antwort------------------   |
                                                          v
                                              Lokale Tools: Browser-Steuerung (Playwright)
                                                            Bildschirm sehen (Claude Vision)

Doppelklatschen --> startet Spotify, VS Code, Obsidian und aktiviert Jarvis
```

## Komponenten

| Ordner | Aufgabe |
|---|---|
| `backend/` | FastAPI-Server: Systemprompt, Anbindung an Claude ("Gehirn"), Aktions-System (Suche, URL öffnen, Bildschirm sehen, News), ElevenLabs-Sprachausgabe |
| `frontend/` | Jarvis Orb UI im Browser: Spracheingabe via Web Speech API, Audiowiedergabe |
| `clap_trigger/` | Lokales Skript, das auf Doppelklatschen lauscht, Apps startet und Jarvis aktiviert |

## Setup

```bash
cd jarvis
cp .env.example .env
# .env ausfuellen: mind. ANTHROPIC_API_KEY, optional ELEVENLABS_API_KEY

pip install -r backend/requirements.txt
playwright install chromium

uvicorn jarvis.backend.main:app --reload --app-dir ../  # aus dem Repo-Root ausfuehren
```

Am einfachsten aus dem Repo-Root starten:

```bash
pip install -r jarvis/backend/requirements.txt
playwright install chromium
uvicorn jarvis.backend.main:app --reload
```

Danach im Chrome-Browser `http://localhost:8000` öffnen. Mikrofonzugriff erlauben,
auf **Sprechen** klicken oder die Leertaste gedrückt halten, oder direkt auf
**Aktivieren** klicken für die "Jarvis activate"-Begrüßung.

## Aktionen

Jarvis hängt bei Bedarf eine Aktion ans Ende seiner Antwort, die vom Server still
ausgeführt wird:

- `[ACTION:SEARCH] suchbegriff` - durchsucht das Internet und fasst die Ergebnisse zusammen
- `[ACTION:OPEN] url` - öffnet eine URL im gesteuerten Browser (Playwright)
- `[ACTION:SCREEN]` - sieht sich den Bildschirm an und beschreibt ihn (Claude Vision)
- `[ACTION:NEWS]` - ruft aktuelle Weltnachrichten ab

## Doppelklatschen-Trigger

Läuft **lokal auf deinem Rechner** (nicht im Server-Container), da es Mikrofon- und
Lautsprecherzugriff braucht:

```bash
pip install -r jarvis/clap_trigger/requirements.txt
python jarvis/clap_trigger/clap_listener.py
```

Startet bei zwei kurz aufeinanderfolgenden Klatschern Spotify, VS Code und Obsidian
und ruft `/api/activate` auf dem Server auf. Welche Apps gestartet werden, lässt sich
über `JARVIS_CLAP_APPS` in `.env` anpassen.

## Aufgabenübersicht bei der Aktivierung

`backend/tasks.json` enthält eine einfache Liste von Aufgaben (Strings), die Jarvis
bei "Jarvis activate" kurz zusammenfasst. Kann frei angepasst oder später an eine
echte Aufgabenverwaltung angebunden werden.
