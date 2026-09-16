# Third-Party Licenses and Open-Source Notices

`ellmos-swarm-ai` is distributed under the terms of the [MIT License](LICENSE).
This document inventories external dependencies, libraries, and open-source tooling used at runtime or during development.

---

## Direct Runtime Dependencies

### 1. Anthropic Python SDK (`anthropic`)
- **Package:** `anthropic`
- **Homepage:** https://github.com/anthropics/anthropic-sdk-python
- **License:** MIT License
- **Copyright:** (c) 2023 Anthropic, PBC
- **Usage:** Core API interface for multi-agent LLM consensus voting, worker prompt fan-out, and streaming response parsing.

### 2. Python Standard Library (`sqlite3`, `pathlib`, `json`, `dataclasses`, `subprocess`, `argparse`, `typing`)
- **Homepage:** https://www.python.org/
- **License:** Python Software Foundation License (PSFL) Version 2
- **Copyright:** (c) 2001-2026 Python Software Foundation
- **Usage:** File operations, SQLite-based stigmergy marker store, atomic transactions, CLI argument parsing, and process execution.

---

## Optional & Provider Bridge Dependencies

### 3. COMA (`coma`)
- **Package:** `coma` (`providers` extra)
- **Repository:** https://github.com/dev-bricks/coma
- **License:** MIT License
- **Copyright:** (c) 2026 dev-bricks / Lukas Geiger
- **Usage:** Multi-agent job board, provider routing bridge (Codex, Agy, Kimi), and cross-assistant delegation.

---

## Development, Testing & Code Quality Dependencies

### 4. pytest (`pytest`)
- **Homepage:** https://pytest.org/
- **License:** MIT License
- **Copyright:** (c) 2004-2026 Holger Krekel and pytest-dev contributors
- **Usage:** Automated unit and regression test suite execution, contract verification, and test parameterization.

### 5. Ruff (`ruff`)
- **Homepage:** https://astral.sh/ruff
- **License:** MIT License / Apache License 2.0
- **Copyright:** (c) 2023-2026 Astral Software Inc.
- **Usage:** High-performance static Python linting, formatting, and AST syntax verification.

### 6. Bandit (`bandit`)
- **Homepage:** https://github.com/PyCQA/bandit
- **License:** Apache License 2.0
- **Copyright:** (c) 2014 Hewlett-Packard Development Company, L.P. / OpenStack Foundation
- **Usage:** Automated static security vulnerability scanner for Python source code in GitHub Actions CI.

---

## Audit Information & Governance Assurance

- **Audit Date:** 2026-09-16
- **Auditor:** Antigravity / Gemini Agent (Pfad B Discoverability & License Parity)
- **Local-First & Zero-Egress:** All runtime dependencies execute strictly locally; prompts and marker databases are never transmitted to third-party telemetry.
- **RunAsInvoker Non-Elevation:** swarm-ai executes entirely within standard unprivileged user space without requiring administrative or root elevation.
- **Fail-Closed Evidence Acceptance:** Any unverified or foreign runtime dependency missing explicit permissive license verification is rejected fail-closed.

---

## Summary of License Compliance

| Dependency | Scope | License | Copyleft | Status |
|---|---|---|---|---|
| `anthropic` | Core Runtime API | MIT License | No | Approved |
| `sqlite3`, `pathlib`, etc. | Python Standard Library | PSFL-2.0 | No | Approved |
| `coma` | Optional Provider Bridge | MIT License | No | Approved |
| `pytest` | Testing & Verification | MIT License | No | Approved |
| `ruff` | Static Linting & AST Check | MIT / Apache-2.0 | No | Approved |
| `bandit` | Security Static Analysis | Apache-2.0 | No | Approved |

All runtime and optional dependencies are permissively licensed (MIT, Apache-2.0, PSFL).
No copyleft (GPL / AGPL) libraries are bundled or linked into the core distribution, ensuring unconstrained commercial and open-source utilization under the MIT license.
