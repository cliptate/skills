# Cliptate Skills

Agent-Skills zur Nutzung von [Cliptate](https://github.com/cliptate/cliptate) über die macOS-Kommandozeile.

**Sprachen:** [English](../README.md) · [简体中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · Deutsch

## Verfügbarer Skill

| Skill | Funktionen |
| --- | --- |
| [cliptate](../cliptate/SKILL.md) | Lokale Audio- und Videodateien transkribieren, Untertitel exportieren, Sprache erzeugen, das Erkennungswörterbuch verwalten und Verlauf sowie Korrekturbelege abfragen |
| [cliptate-long2shorts](../cliptate-long2shorts/SKILL.md) | Lange Videos mit Cliptate transkribieren, Höhepunkte und Übersetzungen durch den Agenten auswählen und mit FFmpeg als kurze Hochformatvideos rendern |

Der Skill enthält Befehlsbeispiele sowie Hinweise zu JSON, Seitennavigation, Teilerfolgen und Versionsprüfungen. Die Skill-Anweisungen sind derzeit auf vereinfachtem Chinesisch verfasst; ein Agent kann damit auch Anfragen in anderen Sprachen bearbeiten. Dieses Repository stellt Agent-Anweisungen bereit. Die Cliptate-App wird separat installiert.

## Voraussetzungen

- Apple-Silicon-Mac mit macOS 15 oder neuer.
- Cliptate aus GitHub oder als direkter Download. Die App-Store-Version bietet keinen CLI-Dienst.
- Eine CLI-Version, deren `cliptate --help` den benötigten Befehl aufführt. Älteren Versionen können `tts` oder `history` fehlen.
- Bereits heruntergeladene Modelle oder `--download`, wenn Modelle heruntergeladen werden sollen.
- Für `cliptate-long2shorts`: Python 3.9+, ffprobe, FFmpeg mit libass und eine Untertitelschrift; yt-dlp für YouTube-Quellen.

## Installation und Nutzung

### Mit npx installieren

Mit installiertem Node.js und npm lassen sich Skills und Zielagenten über die [skills CLI](https://github.com/vercel-labs/skills) interaktiv auswählen:

```sh
npx skills add cliptate/skills
```

Beide Skills global für Codex installieren:

```sh
npx skills add cliptate/skills --agent codex --global --skill cliptate --skill cliptate-long2shorts
```

Mit `--global` sind die Skills in allen Projekten verfügbar; ohne diese Option werden sie im aktuellen Projekt installiert. Für `cliptate` allein `--skill cliptate-long2shorts` weglassen. Für `cliptate-long2shorts` beide Skills installieren, da es `cliptate` zur Transkription nutzt. Andere Agenten interaktiv auswählen oder `--agent` auf deren unterstützte Kennung ändern.

### Manuelle Installation

Dieses Repository klonen und den vollständigen Ordner jedes gewünschten Skills, `cliptate/` oder `cliptate-long2shorts/`, für Codex nach `~/.codex/skills/` kopieren. Alle enthaltenen Unterordner `references/`, `agents/` und `scripts/` beibehalten. `cliptate` kann eigenständig verwendet werden. `cliptate-long2shorts` nutzt den Skill `cliptate` für die Transkription; dafür beide Ordner im selben Skill-Verzeichnis installieren. Falls das Ziel bereits existiert, vor dem Ersetzen seinen Inhalt prüfen. Für andere Agenten das jeweils unterstützte Skill-Verzeichnis verwenden. Codex kann die Skills ab dem nächsten Gesprächsschritt nutzen.

In Cliptate unter **Einstellungen → Kommandozeile** den angezeigten Installationsbefehl verwenden, um den Helper in `~/.local/bin` zu verknüpfen. Dieses Verzeichnis muss im PATH stehen; alternativ den Helper direkt aus dem App-Bundle aufrufen. Den tatsächlichen Befehl prüfen:

```sh
cliptate --version
cliptate --help
```

Beispielanfragen:

```text
Verwende $cliptate, um interview.mp4 zu transkribieren und als interview.srt zu speichern.
Verwende $cliptate, um narration.txt als narration.wav zu vertonen.
Verwende $cliptate, um aktuelle Korrekturen auszuwerten und verlässliche neue Begriffe zum Wörterbuch hinzuzufügen.
Verwende $cliptate-long2shorts, um interview.mp4 in drei Hochformatclips von 30–90 Sekunden mit chinesischen und englischen Untertiteln umzuwandeln. Zeige zuerst eine Vorschau des ersten Clips.
```

Die öffentliche CLI exportiert SRT/VTT-Dateien. Videoschnitt und das Einbrennen von Untertiteln werden nicht unterstützt. Befehle verwenden die Einstellungen der ausgewählten App. Transkription und Sprachsynthese erzeugen keine Verlaufseinträge; Wörterbuchänderungen werden dauerhaft gespeichert.

`cliptate-long2shorts` ergänzt Videoschnitt und Untertitelrendering mit FFmpeg. Standardmäßig bleibt das vollständige Quellbild mit Randflächen erhalten. Ausgegeben werden MP4, ASS, eine zweizeilige Zusammenfassung, Titel- und Vorschaubilder sowie Metadaten zum Quellbereich. Die CLI liefert Segmentzeitstempel; der Ablauf verspricht keine Wortgenauigkeit und veröffentlicht nichts auf Plattformen.

## Referenzen

- [Skill-Einstieg](../cliptate/SKILL.md): CLI ermitteln, Ablauf auswählen und Ergebnisse bewerten.
- [Transkription und Untertitel](../cliptate/references/transcription.md): Eingaben, Formate, Ausgabepfade und Batch-JSON.
- [Sprachsynthese](../cliptate/references/tts.md): Textquellen, Modellfamilien, Stimmgestaltung und Stimmenklonen, WAV-Ausgabe.
- [Wörterbuch und Verlauf](../cliptate/references/dictionary-history.md): Begriffe verwalten, Verlauf seitenweise lesen und aus Korrekturen lernen.
- [Kurzvideo-Ablauf](../cliptate-long2shorts/SKILL.md), [Laufzeitumgebung](../cliptate-long2shorts/references/runtime.md) und [Render-Manifest](../cliptate-long2shorts/references/manifest.md).

Bei der Pflege die Hilfe des tatsächlichen Helpers mit dem [CLI-Leitfaden des Hauptprojekts](https://github.com/cliptate/cliptate/blob/main/docs/cli.md) und dem Argumentparser abgleichen. Funktionen im aktuellen Quellcode können neuer sein als die installierte App.
