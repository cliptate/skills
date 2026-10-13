# Cliptate Skills

Agent-Skills zur Nutzung von [Cliptate](https://github.com/cliptate/cliptate) über die macOS-Kommandozeile.

**Sprachen:** [English](../README.md) · [简体中文](README.zh.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · Deutsch

## Verfügbarer Skill

| Skill | Funktionen |
| --- | --- |
| [cliptate](../cliptate/SKILL.md) | Lokale Audio- und Videodateien transkribieren, Untertitel exportieren, Sprache erzeugen, das Erkennungswörterbuch verwalten und Verlauf sowie Korrekturbelege abfragen |

Der Skill enthält Befehlsbeispiele sowie Hinweise zu JSON, Seitennavigation, Teilerfolgen und Versionsprüfungen. Die Skill-Anweisungen sind derzeit auf vereinfachtem Chinesisch verfasst; ein Agent kann damit auch Anfragen in anderen Sprachen bearbeiten. Dieses Repository stellt Agent-Anweisungen bereit. Die Cliptate-App wird separat installiert.

## Voraussetzungen

- Apple-Silicon-Mac mit macOS 15 oder neuer.
- Cliptate aus GitHub oder als direkter Download. Die App-Store-Version bietet keinen CLI-Dienst.
- Eine CLI-Version, deren `cliptate --help` den benötigten Befehl aufführt. Älteren Versionen können `tts` oder `history` fehlen.
- Bereits heruntergeladene Modelle oder `--download`, wenn Modelle heruntergeladen werden sollen.

## Installation und Nutzung

Dieses Repository klonen und den gesamten Ordner `cliptate/` für Codex nach `~/.codex/skills/cliptate/` kopieren. Die Unterordner `references/` und `agents/` beibehalten. Falls das Ziel bereits existiert, vor dem Ersetzen seinen Inhalt prüfen. Für andere Agenten das jeweils unterstützte Skill-Verzeichnis verwenden. Codex kann den Skill ab dem nächsten Gesprächsschritt nutzen.

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
```

Die öffentliche CLI exportiert SRT/VTT-Dateien. Videoschnitt und das Einbrennen von Untertiteln werden nicht unterstützt. Befehle verwenden die Einstellungen der ausgewählten App. Transkription und Sprachsynthese erzeugen keine Verlaufseinträge; Wörterbuchänderungen werden dauerhaft gespeichert.

## Referenzen

- [Skill-Einstieg](../cliptate/SKILL.md): CLI ermitteln, Ablauf auswählen und Ergebnisse bewerten.
- [Transkription und Untertitel](../cliptate/references/transcription.md): Eingaben, Formate, Ausgabepfade und Batch-JSON.
- [Sprachsynthese](../cliptate/references/tts.md): Textquellen, Modellfamilien, Stimmgestaltung und Stimmenklonen, WAV-Ausgabe.
- [Wörterbuch und Verlauf](../cliptate/references/dictionary-history.md): Begriffe verwalten, Verlauf seitenweise lesen und aus Korrekturen lernen.

Bei der Pflege die Hilfe des tatsächlichen Helpers mit dem [CLI-Leitfaden des Hauptprojekts](https://github.com/cliptate/cliptate/blob/main/docs/cli.md) und dem Argumentparser abgleichen. Funktionen im aktuellen Quellcode können neuer sein als die installierte App.
