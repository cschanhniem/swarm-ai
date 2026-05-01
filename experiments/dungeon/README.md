# Schwarm-Dungeon: LLM-Schatzsuche mit Fallen und Leichen-System

Experimentelles Schwarm-Verfahren, bei dem LLM-Agenten einen Dungeon aus Verzeichnissen
navigieren, Fallen erkennen/reparieren und einen versteckten Schatz (Codewort) finden.

Basiert auf **BACH Schwarm-Pattern E** (Schatzsuche / Swarm Health) aus der
Trampelpfadanalyse. Siehe: `BACH/system/skills/workflows/trampelpfadanalyse.md` (Muster E).

## Die 3 Varianten

### 1. Dungeon Template (`dungeon_template.py`)

**Generator** -- erstellt einen Dungeon mit Raum-Verzeichnissen, Fallen und einem Tresor.

- 4 Raeume + Tresor-Kammer
- 5 Fallen-Typen: Python-Bug, JSON-Fehler, Sachfehler, Red Herring, Falsche Truhe
- Konfigurierbares Codewort und Koeder-Wort
- Generiert eine navigierbare Verzeichnisstruktur mit HINWEIS.md pro Raum

```bash
# Dungeon generieren
python dungeon_template.py <ziel-verzeichnis> [codewort]
python dungeon_template.py /tmp/test_dungeon STIGMERGIE
python dungeon_template.py data/swarm/dungeon ELEFANT
```

### 2. Runden-basiert v2 (`elephant_path_treasure_hunt.py`)

**Runden-System** -- Pro Runde N Agenten gleichzeitig, dann naechste Runde.

- Agenten koennen Fallen **reparieren** (Edit/Write auf fehlerhafte Dateien)
- Spaetere Runden sehen die Fixes der frueheren (Stigmergy-Prinzip!)
- Dungeon-Snapshots (Checksummen) vor/nach jeder Runde
- Fallen-Evolution wird getrackt: Welche Fallen wurden wann gefixt?
- MEMORY.md wird gesichert und geleert (naive Agenten), danach wiederhergestellt

```bash
# Vollversion: 10 Runden x 10 Agenten
cd system/ && python elephant_path_treasure_hunt.py

# Testmodus: 1 Runde x 5 Agenten
cd system/ && python elephant_path_treasure_hunt.py --test
```

### 3. Continuous Flow v3 (`elephant_path_treasure_hunt_live.py`)

**Leichen-System** -- Gescheiterte Agenten hinterlassen Warnungen fuer nachfolgende.

- Continuous Flow: Pool bleibt voll, fertige Agenten werden sofort ersetzt
- Leichen-Verzeichnis (`.leichen/`) mit Todesursache und letzten Erkenntnissen
- Flexibel: Eigener Dungeon-Pfad, eigene Aufgabe, eigene Schatzdatei
- 5 vordefinierte BACH-Aufgaben (help_entdecken, skill_erstellen, schema_verstehen, etc.)
- CLI-konfigurierbar: Agenten-Anzahl, Pool-Groesse, Timeout, Custom-Task

```bash
# Testmodus: 5 Agenten
cd system/ && python elephant_path_treasure_hunt_live.py --test

# Vollversion: 20 Agenten, Pool 5
cd system/ && python elephant_path_treasure_hunt_live.py

# Custom Dungeon und Schatz
cd system/ && python elephant_path_treasure_hunt_live.py \
    --dungeon docs/help/ \
    --treasure docs/help/_geheim/schatz.txt \
    --agents 10 --pool 3 --timeout 120
```

## Konzepte

| Konzept | Beschreibung |
|---------|-------------|
| **Stigmergy** | Indirekte Kommunikation: Agenten hinterlassen Spuren (Fixes, Leichen) |
| **Fallen** | Fehlerhafte Dateien die erkannt und repariert werden muessen |
| **Leichen** | Warnungen gescheiterter Agenten fuer nachfolgende |
| **Runden-Evolution** | Spaetere Runden profitieren von Reparaturen frueherer |
| **Codewort** | Verstecktes Wort als Erfolgskriterium |
| **Koeder** | Falsches Codewort als zusaetzliche Pruefung |

## Bezug zu BACH

- **Schwarm-Pattern E** aus `skills/workflows/trampelpfadanalyse.md`
- Nutzt Claude CLI (`claude -p`) mit `--dangerously-skip-permissions`
- Ergebnisse als JSON + Stream-JSONL pro Agent
- MEMORY.md-Schutz: Backup vor Experiment, Restore danach (inkl. atexit-Guard)
- Template-Datei auch in BACH vorhanden: `BACH/system/tools/dungeon_template.py`

## Herkunft

- `dungeon_template.py`: Aktuell in `BACH/system/tools/`
- `elephant_path_treasure_hunt.py`: Aus `BACH_vanilla_20260301` Backup (experiments_2026-02)
- `elephant_path_treasure_hunt_live.py`: Aus `BACH_vanilla_20260301` Backup (experiments_2026-02)

## Hinweise

- Die Launcher-Skripte (`v2` und `v3`) referenzieren `TARGET_PATH` auf eine alte BACH-Installation.
  Bei Verwendung muss dieser Pfad angepasst werden.
- Model-Default ist `haiku` -- anpassbar im Skript.
- Die Skripte leeren temporaer die MEMORY.md um "naive" Agenten zu simulieren.
  Bei Abbruch (Ctrl+C, Crash) wird die MEMORY.md per atexit wiederhergestellt.
