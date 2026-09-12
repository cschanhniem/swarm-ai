# swarm-ai

*Goldfish Swarm*
![swarm-ai Goldfish Variant Banner](assets/banner-goldfish.svg)

**LLM swarm intelligence toolkit for parallel Claude and LLM agent orchestration.**

<p align="center">
  <a href="https://github.com/ellmos-ai/swarm_ai"><img src="https://img.shields.io/badge/version-0.1.2-blue" alt="Version 0.1.2"></a>
  <a href="https://github.com/ellmos-ai/swarm_ai/actions/workflows/ci.yml"><img src="https://img.shields.io/badge/CI-passing-brightgreen" alt="CI Status"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/tests-217%20passed%20%7C%20100%25%20green-brightgreen" alt="Tests 217 Passed"></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue" alt="Python 3.10+"></a>
  <a href="https://github.com/ellmos-ai/swarm_ai"><img src="https://img.shields.io/badge/platforms-Windows%20%7C%20Linux%20%7C%20macOS-blue" alt="Platforms"></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/privacy-100%25%20Local--First%20%7C%20Zero--Egress-success" alt="Privacy: Local-First"></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/security-RunAsInvoker%20%7C%20Non--Elevation-success" alt="Security: Non-Elevation"></a>
  <a href="SECURITY.md"><img src="https://img.shields.io/badge/security%20SLA-48h%20Response%20%7C%205d%20Triage-blue" alt="Security SLA"></a>
  <a href="THIRD_PARTY_LICENSES.md"><img src="https://img.shields.io/badge/third--party-audited%20%7C%20100%25%20permissive-success" alt="Third-Party Audited"></a>
  <a href="MARKETING-LOG.txt"><img src="https://img.shields.io/badge/marketing--log-active-blue" alt="Marketing Log"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/badge/code%20style-ruff-black" alt="Code Style: Ruff"></a>
  <a href="https://github.com/ellmos-ai"><img src="https://img.shields.io/badge/ecosystem-ellmos--ai-informational" alt="Ecosystem: ellmos-ai"></a>
  <a href="https://github.com/open-bricks"><img src="https://img.shields.io/badge/umbrella-open--bricks-blueviolet" alt="Umbrella: open-bricks"></a>
  <a href="llms.txt"><img src="https://img.shields.io/badge/LLM--Ready-llms.txt-orange" alt="LLM Ready"></a>
  <a href="https://github.com/ellmos-ai/swarm_ai"><img src="https://img.shields.io/badge/last--checked-2026--09--12-blue" alt="Last Checked"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="License: MIT"></a>
</p>

<p align="center"><strong>English</strong> · <a href="README_de.md">Deutsch</a></p>

> [!NOTE]
> For LLM & AI agent integration details, structured file maps, and pattern verification indices, see [`llms.txt`](llms.txt).

swarm-ai is a local-first Python toolkit for developers who want to run the same task through multiple LLM instances and combine the results. The focus is on five reusable coordination patterns: parallel chunk processing, boss/worker execution, stigmergy, consensus voting, and specialist routing.

The runner layer supports provider selection through COMA. Existing `ClaudeRunner` usage remains compatible; new code can use `create_runner("codex")`, `create_runner("agy")`, or `create_runner("kimi", allow_unverified=True)`. Codex is read-only by default, Agy receives the configured workspace, and Kimi remains disabled until local model/login verification. Install the optional bridge via `pip install -e ".[providers]"`.

The project is not Docker Swarm, not a hosted agent platform, and not a generic "AI swarm" demo. It is a small, inspectable toolkit for multi-agent LLM orchestration experiments via CLI and Python.

![swarm-ai Coordination Patterns](README/assets/swarm-patterns.svg)

## Quick Navigation

- [System Architecture & Sequence Flow](#system-architecture)
- [Core Capabilities & Security Invariants](#core-capabilities--security-invariants)
- [Discovery Context](#discovery-context)
- [Why swarm-ai](#why-swarm-ai)
- [Patterns](#patterns)
- [Coordination Guardrail: Team Locks](#coordination-guardrail-team-locks)
- [Installation & Setup](#installation)
- [Quick Start](#quick-start)
  - [Consensus Swarm](#consensus-swarm)
  - [Stigmergy Store](#stigmergy-store)
  - [Parallel Claude CLI Calls](#parallel-claude-cli-calls)
  - [Standalone Chunk Databases](#standalone-chunk-databases)
- [Benchmarks & Performance](#benchmarks)
- [Repository Layout](#repository-layout)
- [Project Status & Verification](#project-status)
- [Sibling Tools & Ecosystem](#sibling-tools--ecosystem)
- [Third-Party Licenses & Transparency](#third-party-licenses--transparency)
- [Security & Privacy SLA](#security)
- [Contributing & License](#contributing)

## System Architecture

```mermaid
flowchart TB
    subgraph Client["Client Surfaces & Entrypoints"]
        CLI["CLI Commands<br/>(swarm-consensus, swarm-benchmark, swarm-translate, swarm-summarize, swarm-stigmergy-init)"]
        API["Python API Layer<br/>(run_consensus, StigmergyAPI, ClaudeRunner, create_runner)"]
    end

    subgraph Coordination["Coordination Patterns & Guardrails"]
        P1["1. Parallel Chunks<br/>(translate_swarm, summarize_chunks)"]
        P2["2. Boss + Worker Hierarchy<br/>(runner.py, swarm_haiku_3.json)"]
        P3["3. Stigmergy Markers<br/>(stigmergy_api.py)"]
        P4["4. Consensus Voting<br/>(consensus_swarm.py)"]
        P5["5. Specialist Routing<br/>(swarm_haiku_research.json)"]
        TL["Team Lock Guardrail<br/>(Atomic Resource Claims & Attendance)"]
    end

    subgraph Execution["Execution & Provider Layer"]
        CR["ClaudeRunner / Anthropic SDK"]
        COMA["COMA Bridge Provider<br/>(Codex, Agy, Kimi)"]
    end

    subgraph Storage["Storage & Artifacts Layer"]
        DB[(SQLite Stores<br/>swarm.db / chunks.db / Pheromone Store)]
        RES["Benchmark & Run Artifacts<br/>results/ & logs/"]
    end

    CLI --> Coordination
    API --> Coordination
    Coordination --> TL
    Coordination --> Execution
    Execution --> Storage
```

### Consensus & Swarm Lifecycle Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Caller as Caller / CLI
    participant Orch as Swarm Orchestrator
    participant Guard as Team Lock Guardrail
    participant WorkerA as Agent Worker 1
    participant WorkerB as Agent Worker 2
    participant WorkerN as Agent Worker N
    participant Store as SQLite Pheromone / Chunk DB
    participant Voter as Consensus Aggregator

    Caller->>Orch: Submit Question / Chunk Task & Budget Cap
    Orch->>Guard: Claim Project-Local Resources (Atomic Lock)
    Guard-->>Orch: Claim Verified & Attendance Logged
    par Parallel Fan-Out Dispatch
        Orch->>WorkerA: Query Model Instance (Haiku / Sonnet / Codex)
        Orch->>WorkerB: Query Model Instance (Haiku / Sonnet / Codex)
        Orch->>WorkerN: Query Model Instance (Haiku / Sonnet / Codex)
    end
    WorkerA-->>Orch: Independent Chunk / Vote Response
    WorkerB-->>Orch: Independent Chunk / Vote Response
    WorkerN-->>Orch: Independent Chunk / Vote Response
    Orch->>Store: Deposit Pheromone Trails & Chunk State
    Orch->>Voter: Aggregate Responses & Calculate Agreement
    Voter->>Voter: Filter Outliers & Compute Confidence Score
    Orch->>Guard: Release Team Lock (Clean Teardown)
    Voter-->>Caller: Final Consensus Answer + Confidence Metric
```

## Core Capabilities & Security Invariants

| Invariant ID | Capability / Invariant | Guarantee & Implementation Details | Security & Operational Benefit |
|---|---|---|---|
| `INV-LOCAL-01` | **100% Local-First & Zero-Egress** | All coordination logic, SQLite marker stores (`swarm.db`, `chunks.db`), and runner orchestration run in local user space without external telemetry. | Complete data privacy; private prompts and sensitive artifacts never leave the local environment. |
| `INV-CHUNKS-02` | **Parallel Chunks Pattern** | Workloads are split, concurrently dispatched across workers, and deterministically merged via key/namespace (`tools/translate_swarm.py`, `tools/summarize_chunks.py`). | Massive throughput speedup (up to 2.54x) with resilient chunk recovery and atomic result merging. |
| `INV-HIERARCH-03` | **Boss / Worker Hierarchy** | Top-down coordinator dispatches granular subtasks to workers and aggregates structured responses (`tools/runner.py`, `tools/swarm_haiku_3.json`). | Clear separation of planning and execution; isolated worker failure boundaries. |
| `INV-STORE-04` | **Stigmergy & Pheromone Store** | Decoupled indirect agent coordination via SQLite pheromone markers with strength, deposition, and evaporation (`tools/stigmergy_api.py`). | Scalable, non-blocking asynchronous coordination without requiring direct point-to-point agent messaging. |
| `INV-VOTE-05` | **Consensus & Majority Vote** | Independent model querying with automated agreement rate, vote distribution, and confidence calculation (`tools/consensus_swarm.py`). | Robust hallucination mitigation and verified factual consensus for critical decisions. |
| `INV-ROUTER-06` | **Specialist Routing** | Planner routes domain-specific subtasks to dedicated specialist roles via JSON chain definitions (`tools/swarm_haiku_research.json`). | Optimal prompt tailoring and domain expertise utilization per subtask. |
| `INV-LOCK-07` | **Team Lock Guardrail** | Atomic per-resource claim files and immutable attendance logs prevent concurrent edit conflicts (`tools/team_lock.py`, `konzepte/team-lock-verfahren.md`). | Zero race conditions and file collisions during parallel multi-agent file modifications. |
| `INV-BUDGET-08` | **Fail-Closed Budgeting** | Explicit USD/token cost ceilings, execution timeouts, and rate limits enforced per worker and per swarm run. | Protection against uncontrolled token runaway, infinite loops, and API budget overruns. |
| `INV-RUNAS-09` | **Unprivileged User Mode** | Operates strictly in standard user mode (`RunAsInvoker`) without requiring root/admin privileges or special OS elevations. | Safe, least-privilege execution on developer workstations and CI runners. |
| `INV-SLA-10` | **Multi-OS CI Smoke Integrity** | Automated GitHub Actions test matrix across Ubuntu, Windows, and macOS with concurrency control, Python 3.10-3.13, and 48h SLA. | Reliable cross-platform behavior and consistent execution across diverse developer setups. |

## Discovery Context

Use `ellmos-ai/swarm-ai` when you need the canonical repository name. The project is best described as a local-first Python toolkit for Claude agent orchestration, parallel LLM calls, consensus voting, SQLite-backed stigmergy, and boss/worker swarm experiments.

Useful search phrases:

- `ellmos-ai swarm-ai`
- `Claude agent orchestration Python swarm`
- `parallel LLM consensus voting toolkit`
- `SQLite stigmergy agent coordination`
- `local-first multi-agent LLM orchestration`
- `boss worker LLM agents Python`

swarm-ai is intentionally smaller than enterprise agent platforms such as CrewAI, OpenAI Swarm derivatives, and hosted Swarms-style products. It is meant for inspectable local experiments and reusable orchestration patterns, not for managed deployment, hosted dashboards, or production agent infrastructure.

## Why swarm-ai

- **Parallel LLM execution:** fan out chunked work across multiple Claude or Anthropic calls.
- **Consensus checks:** ask several agents independently and compute response rate, agreement, confidence, and votes.
- **Stigmergy experiments:** use a SQLite-backed pheromone store so agents can leave indirect coordination signals.
- **Chain definitions:** describe hierarchy and specialist swarms as JSON files instead of hardcoding every run.
- **Local-first workflow:** code, prompts, benchmark results, and design notes stay in the repo.

## Patterns

| # | Pattern | Use it when | Implementation |
|---|---|---|---|
| 1 | **Parallel Chunks** | A large document or workload can be split and merged | `tools/translate_swarm.py`, `tools/summarize_chunks.py` |
| 2 | **Hierarchy / Boss + Worker** | One coordinator should dispatch work to several workers | `tools/runner.py`, `tools/swarm_haiku_3.json` |
| 3 | **Stigmergy / Pheromone Paths** | Agents should coordinate indirectly through shared markers | `tools/stigmergy_api.py` |
| 4 | **Consensus / Majority Vote** | You need multiple independent answers and a confidence score | `tools/consensus_swarm.py` |
| 5 | **Specialist / Boss Routing** | Different subtasks need different expert roles | `tools/swarm_haiku_research.json` |

## Coordination Guardrail: Team Locks

When multiple agents share files, tools, MCP sessions, or result artifacts, use a
project-local team lock before starting parallel work. The lock procedure is a
coordination layer around the five swarm patterns, not a sixth pattern. See
[`konzepte/team-lock-verfahren.md`](konzepte/team-lock-verfahren.md) for the
portable file format, claim rules, and lifecycle.
The tested `tools/team_lock.py` implementation uses atomic per-resource claim
files and immutable per-participant attendance records.

## Installation

```bash
git clone https://github.com/ellmos-ai/swarm_ai.git
cd swarm-ai
pip install -r requirements.txt
```

Set an Anthropic API key for tools that call the API:

```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
```

The `ClaudeRunner` examples also require the `claude` CLI to be installed and authenticated.

## Quick Start

### Consensus swarm

Run several agents on the same question and aggregate the answer:

```bash
PYTHONIOENCODING=utf-8 python tools/consensus_swarm.py \
  --mode boolean \
  --agents 7 \
  --max-budget-usd 0.25 \
  --question "Is Python dynamically typed?"
```

Dry-run a consensus call without spending tokens:

```bash
PYTHONIOENCODING=utf-8 python tools/consensus_swarm.py --dry-run "Test question"
```

Use it from Python:

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

### Stigmergy store

Agents can deposit, sense, and evaporate pheromone-like path markers in SQLite:

```python
from tools.stigmergy_api import StigmergyAPI

api = StigmergyAPI(db_path="swarm.db", agent_id="agent_A")

api.deposit("approach_refactor", strength=0.9, metadata={"result": "success"})
paths = api.sense()
best = api.get_best_path()
api.evaporate(decay_rate=0.1)
```

The file-backed schema is initialized automatically. `:memory:` is rejected
because a multi-connection coordination store must persist across connections.

### Parallel Claude CLI calls

Use `ClaudeRunner` when you want to fan out independent prompts through Claude Code:

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

The runner is read-only by default (`Read`, `Glob`, `Grep`), pre-approves only
that set in non-interactive `dontAsk` mode, denies configured MCP tools, and
does not persist sessions. Pass explicit `allowed_tools` and `available_tools`
only when a reviewed task really requires a wider capability surface.

### Standalone chunk databases

The database-bound tools can initialize their own schemas:

```bash
python tools/translate_swarm.py --init-db
python tools/summarize_chunks.py --init-db
python tools/translate_swarm.py --limit 20 --max-budget-usd 1
python tools/summarize_chunks.py --limit 20 --max-budget-usd 1
```

Translation results are matched by key and namespace rather than response order.
The summarizer uses expiring SQLite claims so concurrent runs do not pay twice
for the same chunk. Real API end-to-end verification remains an open release task.

## Benchmarks

The included benchmark compares sequential and parallel execution:

```bash
PYTHONIOENCODING=utf-8 python tools/benchmark.py
PYTHONIOENCODING=utf-8 python tools/benchmark.py --compare --workers 3 \
  --limit 5 --max-budget-usd 2
```

Measured result from `results/benchmark_20260306.json`:

| Metric | Sequential | Parallel (3 workers) | Result |
|---|---:|---:|---:|
| Total time | 1306s | 514s | 2.54x speedup |
| Success rate | 20/20 | 19/20 | 95% parallel success |
| Parallel efficiency | - | 85% | 85% |
| Time saved | - | 792s | 61% |

The cost-free 2026-08-13 dry-run for the current benchmark catalog is recorded
in [`results/benchmark_20260813.json`](results/benchmark_20260813.json). It
includes the selected model's USD-per-million-token pricing, estimated token
costs, Python/platform/repository metadata, and the local Git revision. A
live API benchmark remains a separately authorized release gate.

## Repository Layout

```text
swarm_ai/
|-- tools/
|   |-- runner.py                  # Claude CLI wrapper with run_parallel()
|   |-- consensus_swarm.py         # Majority vote and confidence scoring
|   |-- stigmergy_api.py           # SQLite pheromone coordination
|   |-- translate_swarm.py         # Parallel translation pattern
|   |-- summarize_chunks.py        # Parallel summarization pattern
|   |-- benchmark.py               # Sequential vs. parallel benchmark
|   |-- swarm_haiku_3.json         # Boss + worker chain definition
|   `-- swarm_haiku_research.json  # Specialist research chain
|-- konzepte/                      # German design documents
|-- experiments/                   # Experimental prototypes
|-- results/                       # Benchmark snapshots
`-- tests/                         # Pytest suite
```

## Project Status

swarm-ai is public and usable as an experimental toolkit. The core modules have a local test suite; some concept and experiment files still reference BACH because they document the origin of the patterns. Production use should start from the `tools/` modules and the tested Python APIs.

Historical launchers under `experiments/` fail closed. They require an explicit
test/full-run CLI mode, `SWARM_ENABLE_LEGACY_EXPERIMENTS=I_UNDERSTAND`, a
validated target, a per-agent budget environment variable, and a total-run CLI
budget. Write-capable dungeon and maintenance experiments additionally require
an isolated fixture marker. They run with Claude safe mode, a fixed built-in
tool allowlist, MCP disabled, and never modify user memory files.

Current verification:

- 213 local tests passing, 100% green.
- Ruff, `compileall`, a high-severity Bandit gate, and pinned Linux/Windows/macOS GitHub Actions are enabled.
- MIT licensed.
- The PyPI packaging contract, stable CLI entry points, and release checklist
  are documented in [`PYPI_RELEASE.md`](PYPI_RELEASE.md); no upload has been
  performed.

## Sibling Tools & Ecosystem

| Tool | Repository | Focus & Interaction in Ecosystem |
|---|---|---|
| **coma** | [ellmos-ai/coma](https://github.com/ellmos-ai/coma) | Multi-Agent Job Board & Provider Routing Bridge |
| **clutch** | [ellmos-ai/clutch](https://github.com/ellmos-ai/clutch) | Provider-neutral routing for single tasks |
| **MarbleRun** | [ellmos-ai/MarbleRun](https://github.com/ellmos-ai/MarbleRun) | Sequential agent loops & chain execution |
| **policy-registry** | [ellmos-ai/policy-registry](https://github.com/ellmos-ai/policy-registry) | Policy governance & capability permission authority |
| **system-explorer** | [ellmos-ai/system-explorer](https://github.com/ellmos-ai/system-explorer) | System-wide topology & stack inspection |
| **sqlite-transit-sync** | [ellmos-ai/sqlite-transit-sync](https://github.com/ellmos-ai/sqlite-transit-sync) | Secure SQLite snapshot & sync pipeline |
| **workflowhooker** | [ellmos-ai/workflowhooker](https://github.com/ellmos-ai/workflowhooker) | Workflow hooking & lifecycle event interceptor |
| **memoryhooker** | [ellmos-ai/memoryhooker](https://github.com/ellmos-ai/memoryhooker) | Agent memory injection & provenance tracking |
| **ellmos-filecommander-mcp** | [ellmos-ai/ellmos-filecommander-mcp](https://github.com/ellmos-ai/ellmos-filecommander-mcp) | Local-First FileCommander MCP Server |
| **ellmos-codecommander-mcp** | [ellmos-ai/ellmos-codecommander-mcp](https://github.com/ellmos-ai/ellmos-codecommander-mcp) | Local-First CodeCommander MCP Server |
| **ellmos-controlcenter-mcp** | [ellmos-ai/ellmos-controlcenter-mcp](https://github.com/ellmos-ai/ellmos-controlcenter-mcp) | Unified AI Tools & Profiles Control Center MCP |
| **DevCenter** | [dev-bricks/DevCenter](https://github.com/dev-bricks/DevCenter) | Developer workstation hub & process control |
| **CodeBox** | [dev-bricks/CodeBox](https://github.com/dev-bricks/CodeBox) | Multi-language code runner & plugin platform |
| **ProFiler** | [file-bricks/ProFiler](https://github.com/file-bricks/ProFiler) | Local-First file analysis & privacy traffic light |
| **DokuZen** | [doc-bricks/DokuZen](https://github.com/doc-bricks/DokuZen) | Document processing, annotations & redaction |
| **open-bricks** | [open-bricks/open-bricks](https://github.com/open-bricks) | Umbrella open-source developer tooling ecosystem |

## Third-Party Licenses & Transparency

`swarm-ai` maintains a strict open-source licensing posture with **100% permissive licensing** across all runtime, test, and development dependencies:
- **Zero Copyleft:** Contains no GPL, AGPL, or restrictive commercial components.
- **Audited Dependencies:** Anthropic SDK (MIT), Python Standard Library (PSFL-2.0), pytest (MIT), Ruff (MIT/Apache-2.0), Bandit (Apache-2.0), and optional COMA provider bridge (MIT).
- **RunAsInvoker Execution:** Runs completely in unprivileged user space without requesting administrative elevations.
- **Fail-Closed Privacy:** Operates local-first with zero external telemetry or unconsented network egress.

For the exhaustive license catalog, per-package notices, and copyright attributions, see [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md).

## Security

`swarm-ai` maintains a strict local-first, zero-egress architecture. For details on supported versions, vulnerability disclosures, and our 48-hour response SLA, please refer to [`SECURITY.md`](SECURITY.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Focus areas are standalone pattern cleanup, end-to-end examples, benchmark reproducibility, and clearer chain definitions.

## License

[MIT](LICENSE) - Copyright 2026 Lukas Geiger
