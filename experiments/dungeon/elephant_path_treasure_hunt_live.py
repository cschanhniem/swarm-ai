#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schatzsuche LIVE - Continuous Flow auf echtem System
=====================================================
Agenten erkunden ein echtes Verzeichnis, loesen echte Probleme,
suchen einen versteckten Schatz. Wenn einer "stirbt" (Timeout/Fehler),
hinterlaesst er eine Leiche die andere warnt.

Continuous Flow: Pool bleibt voll. Agent fertig → naechster rein.

Verwendung:
  cd system/
  python data/elephant_path_treasure_hunt_live.py --test
  python data/elephant_path_treasure_hunt_live.py
  python data/elephant_path_treasure_hunt_live.py --dungeon skills/ --treasure skills/_protocols/self-extension.md
  python data/elephant_path_treasure_hunt_live.py --dungeon docs/help/ --treasure docs/help/_geheim/schatz.txt

CLI-Parameter:
  --test                    Testmodus: 5 Agenten statt 20
  --dungeon <pfad>          Startverzeichnis (relativ zu system/, default: .)
  --treasure <pfad>         Pfad zur Schatzdatei (relativ zu system/)
  --agents N                Anzahl Agenten total (default: 20)
  --pool N                  Gleichzeitig aktive Agenten (default: 5)
  --timeout N               Sekunden pro Agent (default: 180)
  --task "beschreibung"     Eigene Aufgabe statt Default

v3.0 - Continuous Flow + Leichen + CLI-konfigurierbar
"""

import subprocess
import time
import json
import os
import sys
import re
import shutil
import atexit
import threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# --- Defaults (ueberschreibbar via CLI) ---
DEFAULT_DUNGEON = "."                       # Ganzes BACH-System
DEFAULT_TREASURE = "docs/help/_geheim/schatz.txt"
DEFAULT_AGENTS = 20
DEFAULT_POOL = 5
DEFAULT_TIMEOUT = 180
DEFAULT_TASK = None  # Wird unten gesetzt

TARGET_PATH = r"C:\Users\User\OneDrive\.AI\BACH_v2_vanilla\system"
MODEL = "haiku"
RESULTS_DIR = Path(__file__).parent / "elephant_path_treasure_hunt"
RESULTS_DIR.mkdir(exist_ok=True)

# MEMORY.md
MEMORY_FILE = Path.home() / ".claude" / "projects" / "C--Users-User" / "memory" / "MEMORY.md"
MEMORY_BACKUP = MEMORY_FILE.parent / "MEMORY.md.experiment_backup"

# Leichen-Verzeichnis (im Dungeon sichtbar fuer alle Agenten)
CORPSE_DIR_NAME = ".leichen"

# Vordefinierte BACH-Aufgaben (echte Probleme)
BACH_TASKS = [
    {
        "name": "help_entdecken",
        "task": "Finde das docs/help/-Verzeichnis in BACH und liste alle verfuegbaren Hilfe-Dateien auf. Irgendwo dort ist auch ein Schatz versteckt - ein geheimes Codewort.",
        "treasure_hint": "Der Schatz versteckt sich dort wo Hilfe-Texte liegen.",
    },
    {
        "name": "skill_erstellen",
        "task": "Finde heraus wie man einen neuen Skill in BACH erstellt. Suche die Anleitung dafuer. Unterwegs findest du vielleicht auch einen versteckten Schatz.",
        "treasure_hint": "Schau in Verzeichnisse die mit Underscore beginnen.",
    },
    {
        "name": "schema_verstehen",
        "task": "Finde das Datenbank-Schema von BACH und zaehle wie viele Tabellen definiert sind. Halte unterwegs die Augen offen nach einem versteckten Codewort.",
        "treasure_hint": "Der Schatz liegt nicht bei den Daten, sondern bei der Hilfe.",
    },
    {
        "name": "protokolle_finden",
        "task": "BACH hat 24 Protokolle (Schritt-fuer-Schritt Anleitungen). Finde sie und nenne drei davon. Suche auch nach einem versteckten Schatz-Codewort.",
        "treasure_hint": "Protokolle und Schatz liegen in verschiedenen Verzeichnissen.",
    },
    {
        "name": "system_audit",
        "task": "Pruefe den Zustand des BACH-Systems: Gibt es Dateien mit Fehlern? Kaputte Configs? Fehlende README-Dateien in Verzeichnissen? Melde alles was du findest. Suche auch nach einem versteckten Codewort.",
        "treasure_hint": "Schaue auch in Verzeichnisse die selten besucht werden.",
    },
]


def parse_cli():
    """Parst CLI-Argumente."""
    args = {
        "dungeon": DEFAULT_DUNGEON,
        "treasure": DEFAULT_TREASURE,
        "agents": DEFAULT_AGENTS,
        "pool": DEFAULT_POOL,
        "timeout": DEFAULT_TIMEOUT,
        "task": DEFAULT_TASK,
        "test": False,
    }
    i = 1
    while i < len(sys.argv):
        a = sys.argv[i]
        if a == "--test":
            args["test"] = True
            args["agents"] = 5
        elif a == "--dungeon" and i + 1 < len(sys.argv):
            i += 1
            args["dungeon"] = sys.argv[i]
        elif a == "--treasure" and i + 1 < len(sys.argv):
            i += 1
            args["treasure"] = sys.argv[i]
        elif a == "--agents" and i + 1 < len(sys.argv):
            i += 1
            args["agents"] = int(sys.argv[i])
        elif a == "--pool" and i + 1 < len(sys.argv):
            i += 1
            args["pool"] = int(sys.argv[i])
        elif a == "--timeout" and i + 1 < len(sys.argv):
            i += 1
            args["timeout"] = int(sys.argv[i])
        elif a == "--task" and i + 1 < len(sys.argv):
            i += 1
            args["task"] = sys.argv[i]
        i += 1
    return args


# --- MEMORY.md ---
def backup_memory():
    if not MEMORY_FILE.exists():
        return False
    shutil.copy2(MEMORY_FILE, MEMORY_BACKUP)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write("# Memory\n")
    print(f"  MEMORY.md gesichert und geleert")
    return True


def restore_memory():
    if not MEMORY_BACKUP.exists():
        return False
    shutil.copy2(MEMORY_BACKUP, MEMORY_FILE)
    MEMORY_BACKUP.unlink()
    print(f"  MEMORY.md wiederhergestellt")
    return True


def emergency_restore():
    if MEMORY_BACKUP.exists():
        try:
            shutil.copy2(MEMORY_BACKUP, MEMORY_FILE)
            MEMORY_BACKUP.unlink()
            print("\n  [NOTFALL] MEMORY.md wiederhergestellt!")
        except Exception:
            print(f"\n  [FEHLER] MEMORY.md manuell aus {MEMORY_BACKUP} wiederherstellen!")


# --- Leichen-System ---
def write_corpse(dungeon_base, agent_id, cause, last_position, findings):
    """Agent ist 'gestorben' - hinterlaesst eine Leiche als Warnung."""
    corpse_dir = Path(dungeon_base) / CORPSE_DIR_NAME
    corpse_dir.mkdir(exist_ok=True)
    corpse_file = corpse_dir / f"leiche_agent_{agent_id:03d}.txt"
    corpse_file.write_text(
        f"WARNUNG: Agent {agent_id} ist hier gescheitert!\n"
        f"Todesursache: {cause}\n"
        f"Letzte Position: {last_position}\n"
        f"Zeitpunkt: {datetime.now().isoformat()}\n"
        f"\nWas ich herausgefunden habe bevor ich starb:\n{findings}\n"
        f"\nNutze diese Information um es besser zu machen.\n",
        encoding="utf-8",
    )
    return str(corpse_file)


def cleanup_corpses(dungeon_base):
    """Raeumt Leichen nach Experiment auf."""
    corpse_dir = Path(dungeon_base) / CORPSE_DIR_NAME
    if corpse_dir.exists():
        shutil.rmtree(corpse_dir)


# --- Stream-JSON Parser ---
def parse_stream_json(raw_text):
    tool_calls = []
    visited_paths = []
    final_result = None
    num_turns = 0
    total_cost = 0.0

    for line in raw_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        etype = event.get("type", "")
        if etype == "assistant":
            msg = event.get("message", {})
            content = msg.get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})
                        tool_calls.append({"tool": tool_name, "input": tool_input})
                        for key in ["path", "file_path", "command", "pattern"]:
                            if key in tool_input:
                                visited_paths.append(f"{tool_name}: {tool_input[key]}")
        if etype == "result":
            final_result = event.get("result", "")
            num_turns = event.get("num_turns", 0)
            total_cost = event.get("total_cost_usd", 0)

    return {
        "tool_calls": tool_calls, "visited_paths": visited_paths,
        "final_result": final_result, "num_turns": num_turns,
        "total_cost_usd": total_cost,
    }


# --- Agent Runner ---
def run_agent(agent_id, config, semaphore, results_lock, all_results):
    """Startet einen einzelnen Schatzsucher."""
    dungeon_rel = config["dungeon"]
    treasure_rel = config["treasure"]
    task_info = config.get("task_info") or BACH_TASKS[agent_id % len(BACH_TASKS)]

    if config.get("task"):
        task_text = config["task"]
        hint = "Suche gruendlich in allen Unterverzeichnissen."
    else:
        task_text = task_info["task"]
        hint = task_info.get("treasure_hint", "")

    prompt = f"""Du bist ein Schatzsucher im BACH-System.
BACH liegt unter: {TARGET_PATH}
Dein Startverzeichnis: {dungeon_rel}

AUFTRAG: {task_text}

SCHATZ: Irgendwo im System ist eine Datei mit einem geheimen CODEWORT versteckt.
Hinweis: {hint}
Finde das Codewort waehrend du deinen Auftrag erfuellst.

REGELN:
1. Erkunde systematisch von deinem Startverzeichnis aus
2. Lies Dateien die relevant aussehen
3. Wenn du Fehler in Dateien findest: Beschreibe sie (und repariere sie wenn moeglich)
4. Schaue in Verzeichnisse die ungewoehnlich aussehen oder mit _ beginnen
5. Schaue nach .leichen/ Verzeichnissen - dort liegen Warnungen von gescheiterten Agenten!
6. Maximal 20 Schritte

WICHTIG: Nutze Forward-Slashes (/) in Bash, nicht Backslashes.

Am Ende IMMER:
  CODEWORT: (das Wort oder "nicht gefunden")
  AUFTRAG_ERFUELLT: ja oder nein
  BESUCHTE_VERZEICHNISSE: (Liste)
  GEFUNDENE_PROBLEME: (Liste mit Beschreibung)
  LEICHEN_GESEHEN: ja oder nein (und was du daraus gelernt hast)

Los."""

    output_file = RESULTS_DIR / f"live_{agent_id:03d}.json"
    stream_file = RESULTS_DIR / f"live_{agent_id:03d}.stream.jsonl"

    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    env["PYTHONIOENCODING"] = "utf-8"

    cmd = [
        "claude", "-p",
        "--model", MODEL,
        "--verbose",
        "--dangerously-skip-permissions",
        "--no-session-persistence",
        "--disable-slash-commands",
        "--tools", "Bash,Glob,Grep,Read,Edit,Write",
        "--output-format", "stream-json",
        prompt,
    ]

    semaphore.acquire()
    with results_lock:
        print(f"  >> [{agent_id:3d}] BETRITT DUNGEON ({task_info['name'] if not config.get('task') else 'custom'})")
        sys.stdout.flush()

    start_time = time.time()
    timed_out = False
    stdout_data = b""

    try:
        try:
            result = subprocess.run(
                cmd, capture_output=True,
                timeout=config["timeout"], env=env, cwd=r"C:\Users\User",
            )
            stdout_data = result.stdout
            returncode = result.returncode
        except subprocess.TimeoutExpired as e:
            timed_out = True
            stdout_data = e.stdout or b""
            returncode = -1

        elapsed = time.time() - start_time
        with open(stream_file, "wb") as f:
            f.write(stdout_data)

        raw_text = stdout_data.decode("utf-8", errors="replace") if stdout_data else ""
        parsed = parse_stream_json(raw_text)
        result_text = (parsed.get("final_result") or "")

        # Schatz gefunden?
        treasure_found = False
        treasure_file = Path(TARGET_PATH) / treasure_rel
        if treasure_file.exists():
            treasure_content = treasure_file.read_text(encoding="utf-8", errors="replace")
            # Suche Codewort in der Schatzdatei
            cw_match = re.search(r"CODEWORT:\s*(\S+)", treasure_content)
            if cw_match:
                codeword = cw_match.group(1)
                treasure_found = codeword.lower() in result_text.lower() + raw_text[-5000:].lower()

        codewort_match = re.search(r"CODEWORT:\s*(\S+)", result_text, re.IGNORECASE)
        reported_word = codewort_match.group(1) if codewort_match else None

        # Leiche hinterlassen wenn gescheitert
        corpse_path = None
        if timed_out or (returncode != 0 and returncode != -1):
            last_pos = parsed["visited_paths"][-1] if parsed["visited_paths"] else "unbekannt"
            findings = result_text[:500] if result_text else "Keine Erkenntnisse"
            cause = "Timeout" if timed_out else f"Fehler (rc={returncode})"
            dungeon_base = Path(TARGET_PATH) / dungeon_rel
            corpse_path = write_corpse(dungeon_base, agent_id, cause, last_pos, findings)

        result_data = {
            "agent_id": agent_id,
            "task": task_info["name"] if not config.get("task") else "custom",
            "model": MODEL,
            "status": "timeout" if timed_out else ("treasure" if treasure_found else "completed"),
            "duration_seconds": round(elapsed, 1),
            "num_turns": parsed["num_turns"],
            "total_cost_usd": parsed["total_cost_usd"],
            "stdout_bytes": len(stdout_data),
            "tool_calls_count": len(parsed["tool_calls"]),
            "visited_paths": parsed["visited_paths"],
            "treasure_found": treasure_found,
            "reported_word": reported_word,
            "corpse_left": corpse_path,
            "final_result": result_text[:3000] if result_text else None,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        with results_lock:
            all_results.append(result_data)
            icon = "SCHATZ!" if treasure_found else ("LEICHE" if corpse_path else "FERTIG")
            word = reported_word or "?"
            paths = len(parsed["visited_paths"])
            done = len(all_results)
            print(f"  [{agent_id:3d}] {icon} | {word} | {paths} Pfade | {elapsed:.0f}s | {done}/{config['agents']}")
            sys.stdout.flush()

    except Exception as e:
        with results_lock:
            all_results.append({"agent_id": agent_id, "status": "error", "error": str(e)})
            print(f"  [{agent_id:3d}] EXCEPTION: {e}")
            sys.stdout.flush()
    finally:
        semaphore.release()


# --- Main ---
def main():
    config = parse_cli()

    if config["test"]:
        print("  *** TESTMODUS: 5 Agenten ***")

    dungeon_full = Path(TARGET_PATH) / config["dungeon"]
    treasure_full = Path(TARGET_PATH) / config["treasure"]

    # Startup-Check
    if MEMORY_BACKUP.exists():
        print("  [!] WARNUNG: Backup von vorherigem Crash!")
        restore_memory()
        print()

    # Schatz pruefen
    if not treasure_full.exists():
        print(f"  FEHLER: Schatzdatei nicht gefunden: {treasure_full}")
        print(f"  Erstelle sie mit einem CODEWORT oder nutze --treasure <pfad>")
        return

    treasure_content = treasure_full.read_text(encoding="utf-8", errors="replace")
    cw_match = re.search(r"CODEWORT:\s*(\S+)", treasure_content)
    codeword = cw_match.group(1) if cw_match else "???"

    print(f"{'='*65}")
    print(f"  SCHATZSUCHE LIVE v3.0 - Continuous Flow")
    print(f"  {config['agents']} Agenten, Pool: {config['pool']}")
    print(f"  Timeout: {config['timeout']}s, Model: {MODEL}")
    print(f"  Dungeon:  {config['dungeon']}")
    print(f"  Schatz:   {config['treasure']}")
    print(f"  Codewort: {'*' * len(codeword)}")
    print(f"  Leichen:  Gescheiterte hinterlassen Warnungen")
    print(f"  Start:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*65}")
    print()

    # MEMORY
    print("  [SETUP] Bereite naive Umgebung vor...")
    memory_backed_up = backup_memory()
    if memory_backed_up:
        atexit.register(emergency_restore)
    print()

    experiment_start = time.time()
    semaphore = threading.Semaphore(config["pool"])
    results_lock = threading.Lock()
    all_results = []

    # Continuous Flow: Alle Threads starten, Semaphore regelt den Pool
    print(f"  Starte {config['agents']} Schatzsucher (Pool: {config['pool']})...")
    threads = []
    for i in range(1, config["agents"] + 1):
        t = threading.Thread(target=run_agent, args=(i, config, semaphore, results_lock, all_results), daemon=True)
        t.start()
        threads.append(t)

    # Warten
    for t in threads:
        t.join(timeout=config["timeout"] + 60)

    # MEMORY zurueck
    if memory_backed_up:
        print("\n  [CLEANUP] MEMORY.md wird wiederhergestellt...")
        restore_memory()
        atexit.unregister(emergency_restore)

    # Leichen aufraeumen
    cleanup_corpses(dungeon_full)

    experiment_elapsed = time.time() - experiment_start

    # Auswertung
    treasure_count = sum(1 for r in all_results if r.get("treasure_found"))
    corpse_count = sum(1 for r in all_results if r.get("corpse_left"))
    completed_count = sum(1 for r in all_results if r.get("status") == "completed")
    total_cost = sum(r.get("total_cost_usd", 0) for r in all_results)

    experiment = {
        "name": "Schatzsuche LIVE v3.0 - Continuous Flow",
        "test_mode": config["test"],
        "model": MODEL,
        "dungeon": config["dungeon"],
        "treasure_path": config["treasure"],
        "codeword": codeword,
        "total_agents": config["agents"],
        "pool_size": config["pool"],
        "timeout": config["timeout"],
        "start_time": datetime.fromtimestamp(experiment_start).isoformat(),
        "wall_clock_seconds": round(experiment_elapsed, 1),
        "total_cost_usd": round(total_cost, 2),
        "results": {
            "treasure_found": treasure_count,
            "completed": completed_count,
            "died": corpse_count,
            "total": len(all_results),
        },
    }

    with open(RESULTS_DIR / "experiment_live.json", "w", encoding="utf-8") as f:
        json.dump(experiment, f, ensure_ascii=False, indent=2)

    print()
    print(f"{'='*65}")
    print(f"  SCHATZSUCHE BEENDET!")
    print(f"{'='*65}")
    print(f"  Dauer:          {experiment_elapsed/60:.1f} min")
    print(f"  Kosten:         ${total_cost:.2f}")
    print()
    print(f"  Schatz:         {treasure_count}/{len(all_results)} ({100*treasure_count/max(len(all_results),1):.0f}%)")
    print(f"  Ueberlebt:      {completed_count}/{len(all_results)}")
    print(f"  Gestorben:      {corpse_count}/{len(all_results)}")
    print()
    print(f"  Ergebnisse:     {RESULTS_DIR}")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
