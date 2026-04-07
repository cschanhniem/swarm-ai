# swarm-ai

**🇬🇧 [English Version](README.md)**

**LLM-Schwarmintelligenz-Toolkit** — 5 parallele Ausführungsmuster zur Orchestrierung mehrerer LLM-Instanzen.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)

---

## Überblick

swarm-ai implementiert fünf Schwarmintelligenz-Muster für parallele LLM-Ausführung. Jedes Muster adressiert einen anderen Koordinationsbedarf — von einfacher paralleler Chunk-Verarbeitung bis hin zu emergenter, pheromonbasierter Pfadauswahl.

| # | Pattern | Beschreibung | Modul |
|---|---------|--------------|-------|
| 1 | **Epstein (Parallel Chunks)** | Arbeit in Chunks aufteilen, parallel verarbeiten, Ergebnisse zusammenführen | `translate_swarm.py`, `summarize_chunks.py` |
| 2 | **Hierarchy (Boss + Worker)** | Koordinator verteilt Aufgaben an Worker, Aggregator führt zusammen | `swarm_haiku_3.json`, `runner.py` |
| 3 | **Stigmergy (Pheromone)** | Agenten kommunizieren indirekt über gemeinsame Marker (Ameisenkolonie-Stil) | `stigmergy_api.py` |
| 4 | **Consensus (Majority Vote)** | Mehrere Agenten beantworten dieselbe Frage, Mehrheitsentscheid gewinnt | `consensus_swarm.py` |
| 5 | **Specialist (Boss Routing)** | Boss leitet Aufgaben an domänenspezifische Experten-Agenten weiter | Chain-Definitionen (JSON) |

---

## Installation

```bash
git clone https://github.com/ellmos-ai/swarm-ai.git
cd swarm-ai
pip install -r requirements.txt
```

API-Schlüssel setzen:

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

---

## Schnellstart

### 1. Epstein — Parallele Chunk-Verarbeitung

Große Arbeitslasten in Chunks aufteilen und mit parallelen LLM-Instanzen verarbeiten:

```bash
PYTHONIOENCODING=utf-8 python tools/translate_swarm.py --dry-run
PYTHONIOENCODING=utf-8 python tools/summarize_chunks.py --dry-run
```

### 2. Hierarchy — Boss + Worker Chain

Koordinator weist Aufgaben zu, Worker führen parallel aus, Aggregator führt Ergebnisse zusammen:

```bash
# Chain-Definitionen (Coordinator + 3 Workers + Aggregator)
cat tools/swarm_haiku_3.json
```

```python
from tools.runner import ClaudeRunner

runner = ClaudeRunner(model="claude-haiku-4-5-20251001")
results = runner.run_parallel([
    "Analyze security vulnerabilities in Flask apps",
    "Review Python packaging best practices",
    "Compare async frameworks in Python",
], max_workers=3)
```

### 3. Stigmergy — Pheromonbasierte Koordination

Agenten hinterlassen Marker („Pheromone") auf Pfaden. Andere Agenten nehmen diese Marker wahr, um vielversprechenden Richtungen zu folgen:

```python
from tools.stigmergy_api import StigmergyAPI

api = StigmergyAPI(db_path="swarm.db", agent_id="agent_A")

# Agent A markiert einen erfolgreichen Pfad
api.deposit("approach_refactor", strength=0.9, metadata={"result": "success"})

# Agent B liest, welche Pfade vielversprechend sind
paths = api.sense()  # sorted by strength DESC
best = api.get_best_path()  # -> "approach_refactor"

# Schwache Pheromone verdunsten lassen (Bereinigung)
api.evaporate(decay_rate=0.1)
```

### 4. Consensus — Mehrheitsentscheid

Mehrere LLM-Instanzen beantworten dieselbe Frage unabhängig voneinander, dann bestimmt ein Mehrheitsentscheid die finale Antwort:

```bash
# Einfache Frage (5 Agenten, Mehrheitsentscheid)
PYTHONIOENCODING=utf-8 python tools/consensus_swarm.py "What is the capital of France?"

# Klassifikationsmodus mit vordefinierten Kategorien
PYTHONIOENCODING=utf-8 python tools/consensus_swarm.py \
    --mode classify \
    --categories "positive,negative,neutral" \
    --question "The movie was okay."

# Boolean-Modus (Ja/Nein)
PYTHONIOENCODING=utf-8 python tools/consensus_swarm.py \
    --mode boolean \
    --agents 7 \
    --question "Is Python dynamically typed?"

# Trockenlauf (nur Kostenschätzung)
PYTHONIOENCODING=utf-8 python tools/consensus_swarm.py --dry-run "Test question"
```

```python
from tools.consensus_swarm import run_consensus

result = run_consensus(
    question="Is Rust memory-safe?",
    num_agents=5,
    mode="boolean",
)
print(result["consensus"]["consensus_answer"])  # "JA"
print(result["consensus"]["confidence"])         # 1.0
```

### 5. Specialist — Boss Routing

Der Boss analysiert eingehende Aufgaben und leitet sie an domänenspezifische Experten-Agenten weiter. Konfiguration über JSON-Chain-Definitionen:

```bash
cat tools/swarm_haiku_research.json  # Planner + 5 Researchers + Synthesizer
```

---

## Benchmarks

Die Benchmark-Suite ausführen, um sequenzielle und parallele Ausführung zu vergleichen:

```bash
# Verfügbare Aufgaben anzeigen (Trockenlauf)
PYTHONIOENCODING=utf-8 python tools/benchmark.py

# Vergleich ausführen
PYTHONIOENCODING=utf-8 python tools/benchmark.py --compare --workers 3

# Ergebnisse exportieren
PYTHONIOENCODING=utf-8 python tools/benchmark.py --compare \
    --export results/benchmark_$(date +%Y%m%d).json
```

### Ergebnisse (2026-03-06, Claude Haiku 4.5, 20 Aufgaben, 3 Worker)

| Metrik | Sequenziell | Parallel (3W) | Speedup |
|--------|------------|---------------|---------|
| Gesamtzeit | 1306s | 514s | **2.54x** |
| Erfolgsrate | 20/20 | 19/20 | — |
| Parallele Effizienz | — | — | 85% |
| Eingesparte Zeit | — | 792s (61%) | — |

Vollständige Ergebnisse: [`results/benchmark_20260306.json`](results/benchmark_20260306.json)

---

## Architektur

```
swarm_ai/
├── tools/
│   ├── runner.py              # ClaudeRunner — CLI-Wrapper mit run_parallel()
│   ├── consensus_swarm.py     # Consensus Pattern (Mehrheitsentscheid)
│   ├── stigmergy_api.py       # Stigmergy Pattern (Pheromon-Koordination)
│   ├── translate_swarm.py     # Epstein Pattern (parallele Übersetzung)
│   ├── summarize_chunks.py    # Epstein Pattern (parallele Zusammenfassung)
│   ├── benchmark.py           # Sequenzielles vs. paralleles Benchmarking
│   ├── swarm_haiku_3.json     # Hierarchy Chain (3 Worker)
│   └── swarm_haiku_research.json  # Specialist Chain (5 Researchers)
├── konzepte/                  # Designdokumente (Deutsch)
│   ├── schwarm-operationen.md
│   ├── schwarm-entscheidungsbaum.md
│   └── trampelpfadanalyse.md
├── results/                   # Benchmark-Ergebnisse (JSON)
└── tests/                     # Testskripte
```

### Kernkomponenten

- **`ClaudeRunner`** (`runner.py`): Kapselt die Claude-CLI mit konfigurierbarem Modell, Timeout, Berechtigungsmodus und paralleler Ausführung über `ThreadPoolExecutor`.
- **`StigmergyAPI`** (`stigmergy_api.py`): SQLite-basierter Pheromon-Speicher. Agenten hinterlegen, erfassen und verdunsten Pheromone, um sich ohne direkte Kommunikation zu koordinieren.
- **`consensus_swarm`**: Führt N Agenten mit demselben Prompt bei `temperature=0.7` für Diversität aus und berechnet dann Übereinstimmungsquote und Konfidenzwert.
- **`benchmark`**: 20 Aufgaben in 4 Kategorien (Softwareentwicklung, Forschung, Wiki, Code-Review) zur Messung des parallelen Speedups.

---

## Mitwirken

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Richtlinien.

---

## Lizenz

[MIT](LICENSE) — Copyright 2026 Lukas Geiger
