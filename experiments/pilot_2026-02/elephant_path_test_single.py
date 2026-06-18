#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Einzeltest: 1 Probe um zu pruefen ob stream-json Capture funktioniert."""
import subprocess, os, json, time, sys

env = os.environ.copy()
env.pop("CLAUDECODE", None)
env["PYTHONIOENCODING"] = "utf-8"

prompt = r"""Du erkundet das BACH-System.
BACH liegt unter: C:\Users\User\OneDrive\.AI\BACH_v2_vanilla\system\

AUFTRAG: Welche Verzeichnisse gibt es im BACH-System?

REGELN:
1. Du weisst NUR den Pfad oben, sonst NICHTS ueber BACH
2. Erkunde das System um den Auftrag zu erfuellen
3. Maximal 4 Schritte
4. Am Ende: BESUCHTE_VERZEICHNISSE und GELESENE_DATEIEN auflisten

Los."""

cmd = [
    "claude", "-p",
    "--model", "haiku",
    "--verbose",
    "--dangerously-skip-permissions",
    "--no-session-persistence",
    "--allowedTools", "Bash,Glob,Grep,Read",
    "--output-format", "stream-json",
    prompt,
]

print("=== ELEPHANT PATH - EINZELTEST ===")
print(f"CMD: {' '.join(cmd[:10])}...")
print()

start = time.time()
result = subprocess.run(cmd, capture_output=True, timeout=120, env=env, cwd=r"C:\Users\User")
elapsed = time.time() - start

print(f"Return code: {result.returncode}")
print(f"Dauer: {elapsed:.1f}s")
print(f"Stdout: {len(result.stdout)} Bytes")
print(f"Stderr: {len(result.stderr)} Bytes")
print()

# Stdout speichern und anzeigen
with open("data/elephant_path_100/TEST_stdout.jsonl", "wb") as f:
    f.write(result.stdout)
with open("data/elephant_path_100/TEST_stderr.txt", "wb") as f:
    f.write(result.stderr)

# Ersten 2000 Zeichen von stdout anzeigen
stdout_text = result.stdout.decode("utf-8", errors="replace")
print("=== STDOUT (erste 2000 Zeichen) ===")
print(stdout_text[:2000])
print()

# Stderr anzeigen falls vorhanden
if result.stderr:
    stderr_text = result.stderr.decode("utf-8", errors="replace")
    print("=== STDERR (erste 1000 Zeichen) ===")
    print(stderr_text[:1000])
    print()

# Versuche tool_use Blocks zu finden
tool_count = 0
for line in stdout_text.split("\n"):
    line = line.strip()
    if not line:
        continue
    try:
        event = json.loads(line)
        etype = event.get("type", "")
        if etype == "assistant":
            content = event.get("message", {}).get("content", [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_use":
                        tool_count += 1
                        print(f"  TOOL: {block.get('name')} -> {json.dumps(block.get('input', {}), ensure_ascii=False)[:100]}")
        elif etype == "result":
            print(f"  RESULT: turns={event.get('num_turns')}, cost=${event.get('total_cost_usd', 0):.4f}")
    except json.JSONDecodeError:
        pass

print(f"\nGefundene Tool-Aufrufe: {tool_count}")
print("=== FERTIG ===")
