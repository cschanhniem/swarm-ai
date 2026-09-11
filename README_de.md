# swarm-ai

*Goldfish-Schwarm*
![swarm-ai Goldfish Variant Banner](assets/banner-goldfish.svg)

**LLM-Schwarmintelligenz-Toolkit für parallele Claude- und LLM-Agenten-Orchestrierung.**

<p align="center">
  <a href="https://github.com/ellmos-ai/swarm_ai"><img src="https://img.shields.io/badge/version-0.1.1-blue" alt="Version 0.1.1"></a>
  <a href="https://github.com/ellmos-ai/swarm_ai/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/CI-passing-brightgreen" alt="CI-Status"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/tests-213%20bestanden%20%7C%20100%25%20gr%C3%BCn-brightgreen" alt="Tests: 213 bestanden"></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue" alt="Python 3.10+"></a>
  <a href="https://github.com/ellmos-ai/swarm_ai"><img src="https://img.shields.io/badge/plattformen-Windows%20%7C%20Linux%20%7C%20macOS-blue" alt="Plattformen"></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/datenschutz-100%25%20Local--First%20%7C%20Zero--Egress-success" alt="Datenschutz: Local-First"></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/sicherheit-RunAsInvoker%20%7C%20Non--Elevation-success" alt="Sicherheit: RunAsInvoker"></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/sicherheits--SLA-48h%20Antwort%20%7C%205d%20Triage-blue" alt="Sicherheits-SLA"></a>
  <a href="THIRD_PARTY_LICENSES.md"><img src="https://img.shields.io/badge/drittanbieter-gepr%C3%BCft%20%7C%20100%25%20permissiv-success" alt="Drittanbieter geprüft"></a>
  <a href="MARKETING-LOG.txt"><img src="https://img.shields.io/badge/marketing--log-aktiv-blue" alt="Marketing-Log"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-black" alt="Code-Stil: Ruff"></a>
  <a href="https://github.com/ellmos-ai"><img src="https://img.shields.io/badge/%C3%B6kosystem-ellmos--ai-informational" alt="Ökosystem: ellmos-ai"></a>
  <a href="https://github.com/open-bricks"><img src="https://img.shields.io/badge/dachorganisation-open--bricks-blueviolet" alt="Dachorganisation: open-bricks"></a>
  <a href="llms.txt"><img src="https://img.shields.io/badge/LLM--Ready-llms.txt-orange" alt="LLM Ready"></a>
  <a href="https://github.com/ellmos-ai/swarm_ai"><img src="https://img.shields.io/badge/letzte--pr%C3%BCfung-2026--09--11-blue" alt="Letzte Prüfung"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/lizenz-MIT-blue" alt="Lizenz: MIT"></a>
</p>

<p align="center"><a href="README.md">English</a> · <strong>Deutsch</strong></p>

> [!NOTE]
> Für LLM- & KI-Agenten-Integrationsdetails, strukturierte Dateikarten und Muster-Verifizierungs-Indizes siehe [`llms.txt`](llms.txt).

swarm-ai ist ein local-first Python-Toolkit für Entwicklerinnen und Entwickler, die dieselbe Aufgabe über mehrere LLM-Instanzen ausführen und die Ergebnisse anschließend zusammenführen wollen. Der Fokus liegt auf fünf wiederverwendbaren Koordinationsmustern: parallele Chunk-Verarbeitung, Boss-/Worker-Ausführung, Stigmergie, Konsensabstimmung und Spezialisten-Routing.

Die Runner-Schicht unterstützt jetzt die Provider-Auswahl über COMA. Bestehende `ClaudeRunner`-Verwendungen bleiben kompatibel; neuer Code kann `create_runner("codex")`, `create_runner("agy")` oder `create_runner("kimi", allow_unverified=True)` nutzen. Codex ist standardmäßig schreibgeschützt, Agy erhält den konfigurierten Workspace, und Kimi bleibt bis zur lokalen Modell-/Login-Freigabe gesperrt. Installiere die optionale Bridge mit `pip install -e ".[providers]"`.

Das Projekt ist kein Docker-Swarm-Werkzeug, keine gehostete Agentenplattform und keine generische "AI swarm"-Demo. Es ist ein kleines, prüfbares Toolkit für Experimente mit Multi-Agent-LLM-Orchestrierung über CLI und Python.

![swarm-ai Koordinationsmuster](README/assets/swarm-patterns.svg)

## Schnellnavigation

- [Systemarchitektur & Sequenzfluss](#systemarchitektur)
- [Kernfähigkeiten & Sicherheitsinvarianten](#kernfähigkeiten--sicherheitsinvarianten)
- [Auffindbarkeitskontext](#auffindbarkeitskontext)
- [Warum swarm-ai](#warum-swarm-ai)
- [Koordinationsmuster](#muster)
- [Koordinations-Guardrail: Team-Locks](#koordinations-guardrail-team-locks)
- [Installation & Setup](#installation)
- [Schnellstart](#schnellstart)
  - [Konsens-Schwarm](#konsens-schwarm)
  - [Stigmergie-Speicher](#stigmergie-speicher)
  - [Parallele Claude CLI-Aufrufe](#parallele-claude-cli-aufrufe)
  - [Eigenständige Chunk-Datenbanken](#eigenständige-chunk-datenbanken)
- [Benchmarks & Leistung](#benchmarks)
- [Repository-Struktur](#repository-layout)
- [Projektstatus & Verifikation](#projektstatus)
- [Geschwister-Tools & Ökosystem](#geschwister-tools--ökosystem)
- [Drittanbieter-Lizenzen & Transparenz](#drittanbieter-lizenzen--transparenz)
- [Sicherheit & Datenschutz-SLA](#sicherheit)
- [Mitwirken & Lizenz](#mitwirken)

## Systemarchitektur

```mermaid
flowchart TB
    subgraph Client["Client-Oberflächen & Einstiegspunkte"]
        CLI["CLI-Befehle<br/>(swarm-consensus, swarm-benchmark, swarm-translate, swarm-summarize, swarm-stigmergy-init)"]
        API["Python-API-Schicht<br/>(run_consensus, StigmergyAPI, ClaudeRunner, create_runner)"]
    end

    subgraph Coordination["Koordinationsmuster & Guardrails"]
        P1["1. Parallel Chunks<br/>(translate_swarm, summarize_chunks)"]
        P2["2. Boss + Worker Hierarchie<br/>(runner.py, swarm_haiku_3.json)"]
        P3["3. Stigmergie-Marker<br/>(stigmergy_api.py)"]
        P4["4. Konsens-Abstimmung<br/>(consensus_swarm.py)"]
        P5["5. Spezialisten-Routing<br/>(swarm_haiku_research.json)"]
        TL["Team-Lock-Guardrail<br/>(Atomare Ressourcen-Claims & Anwesenheit)"]
    end

    subgraph Execution["Ausführungs- & Provider-Schicht"]
        CR["ClaudeRunner / Anthropic SDK"]
        COMA["COMA Bridge Provider<br/>(Codex, Agy, Kimi)"]
    end

    subgraph Storage["Speicher- & Artefakt-Schicht"]
        DB[(SQLite-Speicher<br/>swarm.db / chunks.db / Pheromonspeicher)]
        RES["Benchmark- & Lauf-Artefakte<br/>results/ & logs/"]
    end

    CLI --> Coordination
    API --> Coordination
    Coordination --> TL
    Coordination --> Execution
    Execution --> Storage
```

### Konsens- & Schwarm-Lebenszyklus-Sequenz

```mermaid
sequenceDiagram
    autonumber
    actor Caller as Aufrufer / CLI
    participant Orch as Schwarm-Orchestrator
    participant Guard as Team-Lock-Guardrail
    participant WorkerA as Agent Worker 1
    participant WorkerB as Agent Worker 2
    participant WorkerN as Agent Worker N
    participant Store as SQLite Pheromon / Chunk DB
    participant Voter as Konsens-Aggregator

    Caller->>Orch: Frage / Chunk-Aufgabe & Budgetgrenze übermitteln
    Orch->>Guard: Projektlokale Ressourcen beanspruchen (Atomarer Lock)
    Guard-->>Orch: Claim verifiziert & Anwesenheit protokolliert
    par Parallele Abfrage (Fan-Out)
        Orch->>WorkerA: Modell-Instanz abfragen (Haiku / Sonnet / Codex)
        Orch->>WorkerB: Modell-Instanz abfragen (Haiku / Sonnet / Codex)
        Orch->>WorkerN: Modell-Instanz abfragen (Haiku / Sonnet / Codex)
    end
    WorkerA-->>Orch: Unabhängige Antwort / Chunk-Ergebnis zurückliefern
    WorkerB-->>Orch: Unabhängige Antwort / Chunk-Ergebnis zurückliefern
    WorkerN-->>Orch: Unabhängige Antwort / Chunk-Ergebnis zurückliefern
    Orch->>Store: Pheromon-Pfade & Chunk-Zustand hinterlegen
    Orch->>Voter: Antworten aggregieren & Übereinstimmung ermitteln
    Voter->>Voter: Ausreißer filtern & Konfidenzwert berechnen
    Orch->>Guard: Team-Lock freigeben (Sauberer Abschluss)
    Voter-->>Caller: Finales Konsensergebnis + Konfidenzwert
```

## Kernfähigkeiten & Sicherheitsinvarianten

| Invarianten-ID | Kernfähigkeit / Invariante | Garantie & Implementierungsdetails | Sicherheits- & Betriebsvorteil |
|---|---|---|---|
| `INV-LOCAL-01` | **100% Local-First & Zero-Egress** | Sämtliche Koordinationslogik, SQLite-Pheromonspeicher (`swarm.db`, `chunks.db`) und Runner-Orchestrierungen laufen lokal im User-Space ohne Telemetrie. | Vollständige Datenhoheit; private Prompts und Artefakte verlassen niemals die lokale Umgebung. |
| `INV-CHUNKS-02` | **Parallel-Chunks-Muster** | Aufgaben werden partitioniert, nebenläufig an Worker verteilt und deterministisch nach Schlüssel/Namespace gemergt (`tools/translate_swarm.py`, `tools/summarize_chunks.py`). | Bis zu 2,54-fache Beschleunigung mit robuster Chunk-Wiederherstellung und atomarer Zusammenführung. |
| `INV-HIERARCH-03` | **Boss-/Worker-Hierarchie** | Zentraler Koordinator verteilt granulare Teilaufgaben an Worker und aggregiert strukturierte Ergebnisse (`tools/runner.py`, `tools/swarm_haiku_3.json`). | Klare Trennung von Planung und Ausführung; isolierte Fehlergrenzen pro Worker. |
| `INV-STORE-04` | **Stigmergie & Pheromonspeicher** | Entkoppelte indirekte Koordination über SQLite-Pheromonmarker mit Stärke, Ablage und Verdampfung (`tools/stigmergy_api.py`). | Skalierbare, blockierungsfreie asynchrone Koordination ohne direkte Punkt-zu-Punkt-Agentenkommunikation. |
| `INV-VOTE-05` | **Konsens & Mehrheitsentscheid** | Unabhängige Modellabfragen mit automatisierter Zustimmungsrate, Stimmenverteilung und Konfidenzberechnung (`tools/consensus_swarm.py`). | Zuverlässige Reduktion von Halluzinationen und gesicherter faktischer Konsens für kritische Entscheidungen. |
| `INV-ROUTER-06` | **Spezialisten-Routing** | Planer leitet domänenspezifische Teilaufgaben über JSON-Chain-Definitionen an spezialisierte Expertenrollen (`tools/swarm_haiku_research.json`). | Optimale Prompt-Spezialisierung und zielgerichteter Einsatz von Fachexpertise pro Teilschritt. |
| `INV-LOCK-07` | **Team-Lock-Guardrail** | Atomare dateibasierte Ressourcen-Claims und unveränderliche Anwesenheitsprotokolle verhindern Schreibkonflikte (`tools/team_lock.py`, `konzepte/team-lock-verfahren.md`). | Ausschluss von Race-Conditions und Dateikollisionen bei parallelen Agenten-Schreibzugriffen. |
| `INV-BUDGET-08` | **Fail-Closed Budget-Schutz** | Verbindliche USD-/Token-Kostengrenzen, Timeouts und Aufruflimits werden pro Worker und Gesamtlauf strikt durchgesetzt. | Schutz vor unkontrolliertem Token-Verbrauch, Endlosschleifen und unerwarteten API-Kosten. |
| `INV-RUNAS-09` | **Unprivilegierter User-Mode** | Läuft vollständig im Standard-Benutzermodus (`RunAsInvoker`) ohne Root-/Admin-Rechte oder Betriebssystem-Elevationen. | Sicherer Least-Privilege-Betrieb auf Entwickler-Workstations und CI-Systemen. |
| `INV-SLA-10` | **Multi-OS CI-Smoke-Integrität** | Automatisierte GitHub Actions Testmatrix auf Ubuntu, Windows und macOS mit Concurrency-Steuerung, Python 3.10-3.13 und 48h SLA. | Zuverlässiges plattformübergreifendes Verhalten und konsistente Ausführung auf allen Zielsystemen. |

## Auffindbarkeitskontext

Nutze `ellmos-ai/swarm-ai`, wenn der kanonische Repository-Name gemeint ist. Das Projekt lässt sich am besten als local-first Python-Toolkit für Claude-Agenten-Orchestrierung, parallele LLM-Aufrufe, Konsensabstimmung, SQLite-gestützte Stigmergie und Boss-/Worker-Schwarmexperimente beschreiben.

Nützliche Suchphrasen:

- `ellmos-ai swarm-ai`
- `Claude agent orchestration Python swarm`
- `parallel LLM consensus voting toolkit`
- `SQLite stigmergy agent coordination`
- `local-first multi-agent LLM orchestration`
- `boss worker LLM agents Python`

swarm-ai ist bewusst kleiner als Enterprise-Agentenplattformen wie CrewAI, OpenAI-Swarm-Ableitungen oder gehostete Swarms-Produkte. Es ist für prüfbare lokale Experimente und wiederverwendbare Orchestrierungsmuster gedacht, nicht für Managed Deployment, gehostete Dashboards oder produktive Agenteninfrastruktur.

## Warum swarm-ai

- **Parallele LLM-Ausführung:** große Aufgaben in Teilstücke aufteilen und über mehrere Claude- oder Anthropic-Aufrufe verarbeiten.
- **Konsensprüfungen:** mehrere Agenten unabhängig antworten lassen und Antwortrate, Zustimmung, Konfidenz und Stimmen berechnen.
- **Stigmergie-Experimente:** ein SQLite-basierter Pheromonspeicher ermöglicht indirekte Koordinationssignale zwischen Agenten.
- **Chain-Definitionen:** Hierarchie- und Spezialisten-Schwärme werden als JSON beschrieben statt fest verdrahtet.
- **Local-first Workflow:** Code, Prompts, Benchmarks und Designdokumente bleiben lokal und versioniert im Repo.

## Muster

| # | Muster | Geeignet für | Implementierung |
|---|---|---|---|
| 1 | **Parallel-Chunks** | Große Dokumente oder Aufgaben, die teilbar und zusammenführbar sind | `tools/translate_swarm.py`, `tools/summarize_chunks.py` |
| 2 | **Hierarchie / Boss + Worker** | Ein Koordinator verteilt Arbeit an mehrere Worker | `tools/runner.py`, `tools/swarm_haiku_3.json` |
| 3 | **Stigmergie / Pheromonpfade** | Agenten koordinieren sich indirekt über gemeinsame Marker | `tools/stigmergy_api.py` |
| 4 | **Konsens / Mehrheitsentscheid** | Mehrere unabhängige Antworten sollen zu Konfidenz und Abstimmung führen | `tools/consensus_swarm.py` |
| 5 | **Spezialist / Boss-Routing** | Unterschiedliche Teilaufgaben brauchen unterschiedliche Expertenrollen | `tools/swarm_haiku_research.json` |

## Koordinations-Guardrail: Team-Locks

Wenn mehrere Agenten Dateien, Tools, MCP-Sitzungen oder Ergebnisartefakte teilen,
sollte vor der parallelen Arbeit ein projektlokaler Team-Lock gesetzt werden. Das
Lock-Verfahren ist eine Koordinationsschicht um die fünf Schwarmmuster, kein
sechstes Muster. Das portable Dateiformat, Claim-Regeln und der Lebenszyklus sind
in [`konzepte/team-lock-verfahren.md`](konzepte/team-lock-verfahren.md) beschrieben.
Die getestete Implementierung `tools/team_lock.py` nutzt atomare Claims pro
Ressource und unveränderliche Anwesenheitsdateien pro Teilnehmer.

## Installation

```bash
git clone https://github.com/ellmos-ai/swarm_ai.git
cd swarm-ai
pip install -r requirements.txt
```

Für Tools mit API-Aufrufen wird ein Anthropic API-Key benötigt:

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

Die `ClaudeRunner`-Beispiele benötigen zusätzlich eine installierte und authentifizierte `claude`-CLI.

## Schnellstart

### Konsens-Schwarm

Mehrere Agenten beantworten dieselbe Frage, anschließend wird aggregiert:

```bash
PYTHONIOENCODING=utf-8 python tools/consensus_swarm.py \
  --mode boolean \
  --agents 7 \
  --max-budget-usd 0.25 \
  --question "Is Python dynamically typed?"
```

Trockenlauf ohne Tokenkosten:

```bash
PYTHONIOENCODING=utf-8 python tools/consensus_swarm.py --dry-run "Test question"
```

Verwendung aus Python:

```python
from tools.consensus_swarm import run_consensus

result = run_consensus(
    question="Is Rust memory-safe?",
    num_agents=5,
    mode="boolean",
    max_budget_usd=0.25,
)

print(result["consensus"]["consensus_answer"])
print(result["consensus"]["confidence"])
```

### Stigmergie-Speicher

Agenten können Pheromon-Marker in SQLite ablegen, abtasten und verdampfen lassen:

```python
from tools.stigmergy_api import StigmergyAPI

api = StigmergyAPI(db_path="swarm.db", agent_id="agent_A")

api.deposit("approach_refactor", strength=0.9, metadata={"result": "success"})
paths = api.sense()
best = api.get_best_path()
api.evaporate(decay_rate=0.1)
```

Das dateibasierte Schema wird automatisch initialisiert. `:memory:` wird
abgelehnt, da ein Multi-Connection-Koordinationsspeicher über Verbindungen
hinweg persistieren muss.

### Parallele Claude CLI-Aufrufe

Nutze `ClaudeRunner`, um unabhängige Prompts parallel über Claude Code auszuführen:

```python
from tools.runner import ClaudeRunner

runner = ClaudeRunner(
    model="claude-haiku-4-5-20251001",
    max_budget_usd=0.25,
)
results = runner.run_parallel(
    [
        "Analyze security vulnerabilities in Flask apps",
        "Review Python packaging best practices",
        "Compare async frameworks in Python",
    ],
    max_workers=3,
)
```

Der Runner ist standardmäßig schreibgeschützt (`Read`, `Glob`, `Grep`),
genehmigt im nicht-interaktiven `dontAsk`-Modus nur diese Werkzeuge vorab,
lehnt konfigurierte MCP-Werkzeuge ab und persistiert keine Sitzungen. Pass
explizite `allowed_tools` und `available_tools` nur dann an, wenn eine
geprüfte Aufgabe dies ausdrücklich erfordert.

### Eigenständige Chunk-Datenbanken

Die datenbankgebundenen Werkzeuge können ihre Schemas eigenständig initialisieren:

```bash
python tools/translate_swarm.py --init-db
python tools/summarize_chunks.py --init-db
python tools/translate_swarm.py --limit 20 --max-budget-usd 1
python tools/summarize_chunks.py --limit 20 --max-budget-usd 1
```

Übersetzungsergebnisse werden nach Schlüssel und Namespace statt nach
Antwortreihenfolge zugeordnet. Der Summarizer nutzt ablaufende SQLite-Claims,
sodass parallele Läufe nicht doppelt für denselben Chunk zahlen.

## Benchmarks

Der enthaltene Benchmark vergleicht sequenzielle und parallele Ausführung:

```bash
PYTHONIOENCODING=utf-8 python tools/benchmark.py
PYTHONIOENCODING=utf-8 python tools/benchmark.py --compare --workers 3 \
  --limit 5 --max-budget-usd 2
```

Messergebnis aus `results/benchmark_20260306.json`:

| Metrik | Sequenziell | Parallel (3 Worker) | Ergebnis |
|---|---:|---:|---:|
| Gesamtzeit | 1306s | 514s | 2,54x Beschleunigung |
| Erfolgsquote | 20/20 | 19/20 | 95% paralleler Erfolg |
| Parallele Effizienz | - | 85% | 85% |
| Gesparte Zeit | - | 792s | 61% |

Der tokenfreie Trockenlauf für den aktuellen Benchmark-Katalog vom 2026-08-13 ist
in [`results/benchmark_20260813.json`](results/benchmark_20260813.json) erfasst.

<a id="repository-layout"></a>
## Repository-Struktur

```text
swarm_ai/
|-- tools/
|   |-- runner.py                  # Claude CLI-Wrapper mit run_parallel()
|   |-- consensus_swarm.py         # Mehrheitsentscheid und Konfidenzbewertung
|   |-- stigmergy_api.py           # SQLite-Pheromonkoordination
|   |-- translate_swarm.py         # Paralleles Übersetzungsmuster
|   |-- summarize_chunks.py        # Paralleles Zusammenfassungsmuster
|   |-- benchmark.py               # Sequenzieller vs. paralleler Benchmark
|   |-- swarm_haiku_3.json         # Boss + Worker Chain-Definition
|   `-- swarm_haiku_research.json  # Spezialisten-Research-Chain
|-- konzepte/                      # Deutsche Designdokumente
|-- experiments/                   # Experimentelle Prototypen
|-- results/                       # Benchmark-Snapshots
`-- tests/                         # Pytest-Testsuite
```

## Projektstatus

swarm-ai ist öffentlich und als experimentelles Toolkit nutzbar. Die Kernmodule verfügen über eine lokale Testsuite. Für den produktiven Einsatz sollte von den `tools/`-Modulen und den getesteten Python-APIs ausgegangen werden.

Historische Launcher unter `experiments/` schlagen standardmäßig fehl (fail-closed). Sie erfordern einen expliziten CLI-Modus, `SWARM_ENABLE_LEGACY_EXPERIMENTS=I_UNDERSTAND`, ein validiertes Ziel und feste Budgets.

Aktuelle Verifikation:

- 213 lokale Tests erfolgreich, 100% bestanden.
- Ruff, `compileall`, ein High-Severity-Bandit-Gate und GitHub Actions für Linux/Windows/macOS sind aktiv.
- MIT-lizenziert.
- Der PyPI-Packaging-Vertrag, stabile CLI-Einstiegspunkte und die Release-Checkliste sind in [`PYPI_RELEASE.md`](PYPI_RELEASE.md) dokumentiert.

## Geschwister-Tools & Ökosystem

| Werkzeug | Repository | Fokus & Interaktion im Ökosystem |
|---|---|---|
| **coma** | [ellmos-ai/coma](https://github.com/ellmos-ai/coma) | Multi-Agent Job Board & Provider Routing Bridge |
| **clutch** | [ellmos-ai/clutch](https://github.com/ellmos-ai/clutch) | Provider-neutrales Routing für Einzelaufgaben |
| **MarbleRun** | [ellmos-ai/MarbleRun](https://github.com/ellmos-ai/MarbleRun) | Sequenzielle Agentenketten und Schleifenausführung |
| **policy-registry** | [ellmos-ai/policy-registry](https://github.com/ellmos-ai/policy-registry) | Governance, Berechtigungs- und Richtlinienverwaltung |
| **system-explorer** | [ellmos-ai/system-explorer](https://github.com/ellmos-ai/system-explorer) | Systemweite Topologie- und Stack-Inspektion |
| **sqlite-transit-sync** | [ellmos-ai/sqlite-transit-sync](https://github.com/ellmos-ai/sqlite-transit-sync) | Sichere SQLite Snapshot- und Sync-Pipeline |
| **workflowhooker** | [ellmos-ai/workflowhooker](https://github.com/ellmos-ai/workflowhooker) | Workflow-Hooking und Lifecycle-Events |
| **memoryhooker** | [ellmos-ai/memoryhooker](https://github.com/ellmos-ai/memoryhooker) | Agenten-Gedächtnisinjektion & Provenienz-Tracking |
| **ellmos-filecommander-mcp** | [ellmos-ai/ellmos-filecommander-mcp](https://github.com/ellmos-ai/ellmos-filecommander-mcp) | Local-First FileCommander MCP-Server |
| **ellmos-codecommander-mcp** | [ellmos-ai/ellmos-codecommander-mcp](https://github.com/ellmos-ai/ellmos-codecommander-mcp) | Local-First CodeCommander MCP-Server |
| **ellmos-controlcenter-mcp** | [ellmos-ai/ellmos-controlcenter-mcp](https://github.com/ellmos-ai/ellmos-controlcenter-mcp) | Zentrales KI-Werkzeug- & Profil-Steuerzentrum MCP |
| **DevCenter** | [dev-bricks/DevCenter](https://github.com/dev-bricks/DevCenter) | Entwickler-Dashboard & Workspace-Management |
| **CodeBox** | [dev-bricks/CodeBox](https://github.com/dev-bricks/CodeBox) | Multi-Language Code Runner & Plugin Platform |
| **ProFiler** | [file-bricks/ProFiler](https://github.com/file-bricks/ProFiler) | Local-First Dateianalyse & Datenschutz-Ampel |
| **DokuZen** | [doc-bricks/DokuZen](https://github.com/doc-bricks/DokuZen) | Dokumentenverarbeitung, Annotationen & Schwärzung |
| **open-bricks** | [open-bricks/open-bricks](https://github.com/open-bricks) | Dachorganisation für Open-Source-Entwicklerwerkzeuge |

## Drittanbieter-Lizenzen & Transparenz

`swarm-ai` verfolgt eine strikte Open-Source-Lizenzdisziplin mit **100% permissiver Lizenzierung** für alle Laufzeit- und Entwicklungskomponenten:
- **Kein Copyleft:** Enthält keinerlei GPL-, AGPL- oder proprietär einschränkende Abhängigkeiten.
- **Geprüfte Abhängigkeiten:** Anthropic SDK (MIT), Python-Standardbibliothek (PSFL-2.0), pytest (MIT), Ruff (MIT/Apache-2.0), Bandit (Apache-2.0) sowie optionale COMA-Provider-Bridge (MIT).
- **RunAsInvoker-Ausführung:** Läuft vollständig im unprivilegierten Benutzerkontext ohne administrative Rechteerweiterungen.
- **Fail-Closed-Datenschutz:** Arbeitet local-first mit null Telemetrie und ohne unkontrollierten Netzwerk-Egress.

Das vollständige Lizenzinventar, Einzelnachweise und Copyright-Deklarationen sind in [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) dokumentiert.

## Sicherheit

`swarm-ai` verfolgt ein striktes Local-First- und Zero-Egress-Sicherheitskonzept. Details zu unterstützten Versionen, Sicherheitsmeldungen und unserem 48-Stunden-Reaktions-SLA finden Sie in [`SECURITY.md`](SECURITY.md).

## Mitwirken

Siehe [CONTRIBUTING.md](CONTRIBUTING.md). Schwerpunkte sind eigenständige Muster-Bereinigung, End-to-End-Beispiele, Benchmark-Reproduzierbarkeit und präzisere Chain-Definitionen.

## Lizenz

[MIT](LICENSE) - Copyright 2026 Lukas Geiger
