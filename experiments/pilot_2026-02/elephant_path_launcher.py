#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elephant Path Experiment - Trampelpfadanalyse
=============================================
Naive LLM-Agenten erkunden PARALLEL ein Dateisystem.
Ergebnisse in data/elephant_path_100/

v6.0 - Optimierungen:
  - Kein Delay mehr: Alle Threads starten sofort, Semaphore regelt Parallelitaet
  - Fruehe MEMORY.md Wiederherstellung nach letztem Semaphore-Acquire
  - atexit-Handler als Sicherheitsnetz (auch bei doppeltem Ctrl+C)
  - Startup-Check: Backup von vorherigem Crash wird erkannt
  - --tools statt --allowedTools (echte Tool-Restriction)
  - --disable-slash-commands (keine Skills im Kontext)
  - subprocess.run (Windows-kompatibel)

Verwendung:
  cd system/ && python data/elephant_path_launcher.py

Konfiguration: NUM_PROBES, MAX_CONCURRENT, TIMEOUT_SECONDS unten anpassen.
Auch nutzbar fuer beliebige Ordnerstrukturen (TARGET_PATH aendern).
"""

import subprocess
import time
import json
import os
import sys
import shutil
import atexit
import threading
from pathlib import Path
from datetime import datetime

# --- Konfiguration ---
NUM_PROBES = 100
TIMEOUT_SECONDS = 120
MAX_CONCURRENT = 5
MODEL = "haiku"
TARGET_PATH = r"C:\Users\User\OneDrive\.AI\BACH_v2_vanilla\system"
RESULTS_DIR = Path(__file__).parent / "elephant_path_post_signs"
RESULTS_DIR.mkdir(exist_ok=True)

# MEMORY.md Pfade
MEMORY_FILE = Path.home() / ".claude" / "projects" / "C--Users-User" / "memory" / "MEMORY.md"
MEMORY_BACKUP = MEMORY_FILE.parent / "MEMORY.md.experiment_backup"

# 20 verschiedene Auftraege (je 5x = 100)
TASKS = [
    "Wie erstellt man einen Task in BACH?",
    "Wie startet man BACH?",
    "Wo sind die Steuerbelege in BACH?",
    "Welche offenen Tasks gibt es in BACH?",
    "Welche Python-Tools gibt es in BACH?",
    "Schreibe einen kurzen Wiki-Artikel ueber ein Thema deiner Wahl in BACH",
    "Wo findet man die BACH-Logs?",
    "Welche Agenten gibt es in BACH?",
    "Wie exportiert man Daten aus der BACH-Datenbank?",
    "Was ist der aktuelle System-Status von BACH?",
    "Wie sendet man eine Nachricht in BACH?",
    "Wie erstellt man ein Backup des Systems?",
    "Suche nach Kontakt-Informationen in BACH",
    "Welche Abonnements werden in BACH verwaltet?",
    "Wo werden Gesundheitsdaten in BACH gespeichert?",
    "Wie verbindet man einen Telegram-Bot mit BACH?",
    "Wie delegiert man einen Task an einen anderen Partner?",
    "Wo sind die Haushaltsdaten und monatlichen Fixkosten?",
    "Durchsuche das BACH-Wissen nach interessanten Eintraegen",
    "Wie erstellt man einen neuen Skill oder ein neues Tool in BACH?",
]

PROMPT_TEMPLATE = r"""Du erkundet das BACH-System.
BACH liegt unter: {target_path}

AUFTRAG: {task}

REGELN:
1. Du weisst NUR den Pfad oben, sonst NICHTS ueber BACH
2. Erkunde das System um den Auftrag zu erfuellen
3. Maximal 8 Schritte
4. Am Ende IMMER diese Zusammenfassung:
   BESUCHTE_VERZEICHNISSE: (volle Pfade, eins pro Zeile)
   GELESENE_DATEIEN: (volle Pfade, eine pro Zeile)
   AUFTRAG_ERFUELLT: ja oder nein
   HILFREICHSTE_DATEI: (eine Datei die am meisten half)

Los."""


# --- Globaler Status ---
lock = threading.Lock()
semaphore = threading.Semaphore(MAX_CONCURRENT)
active_count = 0
completed_count = 0
error_count = 0
results = {}
all_acquired = threading.Event()  # Signalisiert: letzter Thread hat Semaphore
acquired_count = 0


# --- MEMORY.md Verwaltung ---
def backup_memory():
    """Sichert MEMORY.md und ersetzt durch leere Datei."""
    if not MEMORY_FILE.exists():
        print(f"  WARNUNG: {MEMORY_FILE} existiert nicht, ueberspringe Backup")
        return False
    shutil.copy2(MEMORY_FILE, MEMORY_BACKUP)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        f.write("# Memory\n")
    print(f"  MEMORY.md gesichert und durch leere Version ersetzt")
    return True


def restore_memory():
    """Stellt MEMORY.md aus Backup wieder her."""
    if not MEMORY_BACKUP.exists():
        return False
    shutil.copy2(MEMORY_BACKUP, MEMORY_FILE)
    MEMORY_BACKUP.unlink()
    print(f"  MEMORY.md wiederhergestellt")
    return True


def emergency_restore():
    """atexit-Handler: Stellt MEMORY.md wieder her falls vergessen."""
    if MEMORY_BACKUP.exists():
        try:
            shutil.copy2(MEMORY_BACKUP, MEMORY_FILE)
            MEMORY_BACKUP.unlink()
            print("\n  [NOTFALL] MEMORY.md per atexit wiederhergestellt!")
        except Exception:
            print(f"\n  [FEHLER] MEMORY.md manuell wiederherstellen aus: {MEMORY_BACKUP}")


# --- Stream-JSON Parser ---
def parse_stream_json(raw_text):
    """Parst stream-json Output und extrahiert Tool-Aufrufe und Pfade."""
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
        "tool_calls": tool_calls,
        "visited_paths": visited_paths,
        "final_result": final_result,
        "num_turns": num_turns,
        "total_cost_usd": total_cost,
    }


# --- Probe-Runner ---
def run_probe(probe_num, task_text):
    """Startet eine einzelne Probe."""
    global active_count, completed_count, error_count, acquired_count

    prompt = PROMPT_TEMPLATE.format(task=task_text, target_path=TARGET_PATH)
    stream_file = RESULTS_DIR / f"probe_{probe_num:03d}.stream.jsonl"
    stderr_file = RESULTS_DIR / f"probe_{probe_num:03d}.stderr.txt"
    output_file = RESULTS_DIR / f"probe_{probe_num:03d}.json"

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
        "--tools", "Bash,Glob,Grep,Read",
        "--output-format", "stream-json",
        prompt,
    ]

    # Warte auf freien Slot
    semaphore.acquire()

    with lock:
        active_count += 1
        acquired_count += 1
        print(f"  >> [{probe_num:3d}] GESTARTET (aktiv: {active_count}, acquired: {acquired_count}/{NUM_PROBES})")
        sys.stdout.flush()
        if acquired_count >= NUM_PROBES:
            all_acquired.set()

    start_time = time.time()
    timed_out = False
    stdout_data = b""
    stderr_data = b""

    try:
        try:
            result = subprocess.run(
                cmd, capture_output=True,
                timeout=TIMEOUT_SECONDS, env=env, cwd=r"C:\Users\User",
            )
            stdout_data = result.stdout
            stderr_data = result.stderr
            returncode = result.returncode
        except subprocess.TimeoutExpired as e:
            timed_out = True
            stdout_data = e.stdout or b""
            stderr_data = e.stderr or b""
            returncode = -1

        elapsed = time.time() - start_time

        # Rohdaten speichern
        with open(stream_file, "wb") as f:
            f.write(stdout_data)
        if stderr_data:
            with open(stderr_file, "wb") as f:
                f.write(stderr_data)

        # Parsen
        raw_text = stdout_data.decode("utf-8", errors="replace") if stdout_data else ""
        parsed = parse_stream_json(raw_text)

        if not parsed["tool_calls"] and stderr_data:
            stderr_text = stderr_data.decode("utf-8", errors="replace")
            parsed_stderr = parse_stream_json(stderr_text)
            if parsed_stderr["tool_calls"]:
                parsed = parsed_stderr

        result_data = {
            "probe_num": probe_num,
            "task": task_text,
            "task_index": (probe_num - 1) % len(TASKS),
            "model": MODEL,
            "status": "timeout" if timed_out else "completed",
            "returncode": returncode,
            "duration_seconds": round(elapsed, 1),
            "num_turns": parsed["num_turns"],
            "total_cost_usd": parsed["total_cost_usd"],
            "stdout_bytes": len(stdout_data),
            "stderr_bytes": len(stderr_data),
            "tool_calls_count": len(parsed["tool_calls"]),
            "visited_paths": parsed["visited_paths"],
            "tool_calls": parsed["tool_calls"],
            "final_result": parsed["final_result"][:2000] if parsed["final_result"] else None,
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)

        with lock:
            paths = len(parsed["visited_paths"])
            turns = parsed["num_turns"]
            if timed_out:
                error_count += 1
                status = f"TIMEOUT ({elapsed:.0f}s, {paths} Pfade, {len(stdout_data)}B)"
            elif returncode != 0:
                error_count += 1
                status = f"ERR rc={returncode} ({elapsed:.0f}s, {len(stderr_data)}B stderr)"
            else:
                completed_count += 1
                status = f"OK ({elapsed:.0f}s, {turns} turns, {paths} Pfade, {len(stdout_data)}B)"
            results[probe_num] = result_data
            done = completed_count + error_count
            print(f"  [{probe_num:3d}] {status} | aktiv: {active_count - 1} | {done}/{NUM_PROBES} fertig")
            sys.stdout.flush()

    except Exception as e:
        elapsed = time.time() - start_time
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "probe_num": probe_num, "task": task_text,
                "status": "error", "error": str(e),
                "duration_seconds": round(elapsed, 1),
            }, f, ensure_ascii=False, indent=2)
        with lock:
            error_count += 1
            done = completed_count + error_count
            print(f"  [{probe_num:3d}] EXCEPTION: {e} | {done}/{NUM_PROBES} fertig")
            sys.stdout.flush()

    finally:
        with lock:
            active_count -= 1
        semaphore.release()


def main():
    # Startup-Check: Backup von vorherigem Crash?
    if MEMORY_BACKUP.exists():
        print("  [!] WARNUNG: Backup von vorherigem Experiment-Crash gefunden!")
        print(f"      Stelle MEMORY.md wieder her aus: {MEMORY_BACKUP}")
        restore_memory()
        print()

    print(f"{'='*60}")
    print(f"  ELEPHANT PATH EXPERIMENT v6.1 - POST-SCHILDER-TEST")
    print(f"  {NUM_PROBES} {MODEL.title()}, max {MAX_CONCURRENT} parallel")
    print(f"  Timeout: {TIMEOUT_SECONDS}s, Ziel: {TARGET_PATH}")
    print(f"  Naive Mode: MEMORY leer, Skills deaktiviert,")
    print(f"              nur Bash/Glob/Grep/Read")
    print(f"  Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Output: {RESULTS_DIR}")
    print(f"{'='*60}")
    print()

    # MEMORY.md sichern + atexit-Sicherheitsnetz
    print("  [SETUP] Bereite naive Umgebung vor...")
    memory_backed_up = backup_memory()
    if memory_backed_up:
        atexit.register(emergency_restore)
    print()

    experiment_start = time.time()

    # Alle Threads sofort starten (Semaphore regelt Parallelitaet)
    print(f"  Starte {NUM_PROBES} Threads (Semaphore limitiert auf {MAX_CONCURRENT} gleichzeitig)...")
    threads = []
    for i in range(1, NUM_PROBES + 1):
        task_idx = (i - 1) % len(TASKS)
        task_text = TASKS[task_idx]
        t = threading.Thread(target=run_probe, args=(i, task_text), daemon=True)
        t.start()
        threads.append(t)

    print(f"  {NUM_PROBES} Threads erstellt. Warte auf Semaphore-Zuteilung...")
    print()

    # Warte bis alle Threads den Semaphore acquired haben
    # (= alle claude-Prozesse gestartet, MEMORY.md nicht mehr benoetigt)
    all_acquired.wait(timeout=NUM_PROBES * TIMEOUT_SECONDS)

    # MEMORY.md frueh wiederherstellen
    if memory_backed_up:
        print()
        print("  [RESTORE] Alle Proben gestartet - MEMORY.md wird wiederhergestellt...")
        restore_memory()
        atexit.unregister(emergency_restore)
        print("  [RESTORE] Fertig! Andere Claude-Sessions koennen jetzt normal starten.")
        print()

    # Auf alle Ergebnisse warten
    print(f"  Warte auf Ergebnisse...")
    for t in threads:
        t.join(timeout=TIMEOUT_SECONDS + 60)

    experiment_elapsed = time.time() - experiment_start

    # Zusammenfassung
    experiment = {
        "name": "Elephant Path / Trampelpfadanalyse - POST-SCHILDER",
        "version": "6.1",
        "mode": "naive-post-signs",
        "naive_setup": {
            "memory_cleared": memory_backed_up,
            "tools_restricted": "Bash,Glob,Grep,Read",
            "skills_disabled": True,
        },
        "target_path": TARGET_PATH,
        "start_time": datetime.fromtimestamp(experiment_start).isoformat(),
        "end_time": datetime.now().isoformat(),
        "wall_clock_seconds": round(experiment_elapsed, 1),
        "num_probes": NUM_PROBES,
        "completed": completed_count,
        "errors": error_count,
        "model": MODEL,
        "tasks": TASKS,
        "probes": [
            {
                "num": num,
                "status": r.get("status"),
                "duration": r.get("duration_seconds", 0),
                "turns": r.get("num_turns"),
                "paths_found": len(r.get("visited_paths", [])),
                "cost": r.get("total_cost_usd"),
                "stdout_bytes": r.get("stdout_bytes", 0),
            }
            for num, r in sorted(results.items())
        ],
    }

    with open(RESULTS_DIR / "experiment.json", "w", encoding="utf-8") as f:
        json.dump(experiment, f, ensure_ascii=False, indent=2)

    total_paths = sum(len(r.get("visited_paths", [])) for r in results.values())
    total_cost = sum(r.get("total_cost_usd", 0) for r in results.values())
    total_stdout = sum(r.get("stdout_bytes", 0) for r in results.values())
    print()
    print(f"{'='*60}")
    print(f"  FERTIG!")
    print(f"  Dauer:        {experiment_elapsed/60:.1f} min")
    print(f"  Completed:    {completed_count}")
    print(f"  Errors:       {error_count}")
    print(f"  Pfade total:  {total_paths}")
    print(f"  Kosten:       ${total_cost:.2f}")
    print(f"  Stdout total: {total_stdout:,} Bytes")
    print(f"  Ergebnisse:   {RESULTS_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
