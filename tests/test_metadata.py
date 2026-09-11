"""Metadata and manifest parity tests for ellmos-ai/swarm-ai."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_manifest_and_pyproject_version_parity():
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version_match = re.search(r'^version = "([^"]+)"', pyproject_text, re.MULTILINE)
    assert version_match, "version not found in pyproject.toml"
    pyproject_version = version_match.group(1)

    manifest_path = ROOT / "ellmos-module.v2.json"
    assert manifest_path.exists(), "ellmos-module.v2.json must exist"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["package"] == "ellmos-swarm-ai"
    assert manifest["id"] == "swarm_ai"
    assert pyproject_version == "0.1.1"


def test_cli_entrypoints_parity():
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    expected_tools = [
        ("tools/consensus_swarm.py", "swarm-consensus"),
        ("tools/benchmark.py", "swarm-benchmark"),
        ("tools/translate_swarm.py", "swarm-translate"),
        ("tools/summarize_chunks.py", "swarm-summarize"),
        ("tools/stigmergy_init.py", "swarm-stigmergy-init"),
    ]

    for rel_path, entrypoint in expected_tools:
        tool_file = ROOT / rel_path
        assert tool_file.exists(), f"Expected tool file {rel_path} must exist"
        assert entrypoint in pyproject_text, f"Entrypoint {entrypoint} must be in pyproject.toml"


def test_llms_txt_and_documentation_parity():
    llms_txt = (ROOT / "llms.txt").read_text(encoding="utf-8")
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert (
        "https://github.com/ellmos-ai/swarm_ai" in llms_txt
        or "https://github.com/ellmos-ai/swarm-ai" in llms_txt
    )
    assert (
        "https://github.com/ellmos-ai/swarm_ai" in readme_en
        or "https://github.com/ellmos-ai/swarm-ai" in readme_en
    )
    assert (
        "https://github.com/ellmos-ai/swarm_ai" in readme_de
        or "https://github.com/ellmos-ai/swarm-ai" in readme_de
    )

    # Verify key patterns documented
    patterns = [
        "tools/consensus_swarm.py",
        "tools/stigmergy_api.py",
        "tools/translate_swarm.py",
        "tools/summarize_chunks.py",
        "tools/runner.py",
    ]
    for pattern in patterns:
        assert pattern in llms_txt, f"Pattern {pattern} must be mentioned in llms.txt"
        assert (ROOT / pattern).exists(), f"File {pattern} must exist"


def test_utf8_integrity_across_markdown():
    md_files = list(ROOT.glob("*.md")) + list((ROOT / "konzepte").glob("*.md"))
    for md_file in md_files:
        content = md_file.read_text(encoding="utf-8")
        assert "\ufffd" not in content, f"Replacement character detected in {md_file}"


def test_pep621_classifiers_and_urls_parity():
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "Programming Language :: Python :: 3" in pyproject_text
    assert "Programming Language :: Python :: 3.10" in pyproject_text
    assert "Programming Language :: Python :: 3.11" in pyproject_text
    assert "Programming Language :: Python :: 3.12" in pyproject_text
    assert "Programming Language :: Python :: 3.13" in pyproject_text
    assert "License :: OSI Approved :: MIT License" in pyproject_text
    assert "Operating System :: OS Independent" in pyproject_text
    assert "Operating System :: POSIX :: Linux" in pyproject_text
    assert "Operating System :: Microsoft :: Windows" in pyproject_text
    assert "Operating System :: MacOS" in pyproject_text
    assert "Topic :: Security" in pyproject_text
    assert "Topic :: System :: Distributed Computing" in pyproject_text
    assert "Documentation = " in pyproject_text
    assert '"Bug Tracker" = ' in pyproject_text
    assert "Changelog = " in pyproject_text
    assert "Security = " in pyproject_text
    assert '"Parent Organization" = "https://github.com/ellmos-ai"' in pyproject_text
    assert '"Umbrella Ecosystem" = "https://github.com/open-bricks"' in pyproject_text


def test_security_policy_bilingual_parity():
    security_md = ROOT / "SECURITY.md"
    assert security_md.exists(), "SECURITY.md must exist"
    content = security_md.read_text(encoding="utf-8")
    assert "# Security Policy / Sicherheitsrichtlinie" in content
    assert "## English" in content
    assert "## Deutsch" in content
    assert "### Supported Versions" in content
    assert "### Unterstützte Versionen" in content
    assert "`0.1.x`" in content
    assert "48 hours" in content
    assert "48 Stunden" in content
    assert "security@ellmos.ai" in content
    assert "security@open-bricks.org" in content
    assert "support@lukasgeiger.com" in content
    assert "lukas@open-bricks.org" in content
    assert "Zero-Egress" in content


def test_ci_workflow_parity():
    ci_path = ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), "ci.yml must exist"
    ci_text = ci_path.read_text(encoding="utf-8")
    assert "ubuntu-latest" in ci_text
    assert "windows-latest" in ci_text
    assert "macos-latest" in ci_text
    assert "3.10" in ci_text
    assert "3.11" in ci_text
    assert "3.12" in ci_text
    assert "3.13" in ci_text
    assert "concurrency:" in ci_text
    assert "cancel-in-progress: true" in ci_text


def test_readme_quick_navigation_and_bilingual_parity():
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "## Quick Navigation" in readme_en
    assert "## Schnellnavigation" in readme_de

    en_anchors = [
        "#system-architecture",
        "#core-capabilities--security-invariants",
        "#discovery-context",
        "#why-swarm-ai",
        "#patterns",
        "#coordination-guardrail-team-locks",
        "#installation",
        "#quick-start",
        "#benchmarks",
        "#repository-layout",
        "#project-status",
        "#sibling-tools--ecosystem",
        "#third-party-licenses--transparency",
        "#security",
        "#contributing",
    ]
    for anchor in en_anchors:
        assert anchor in readme_en, f"Anchor {anchor} must exist in README.md"

    de_anchors = [
        "#systemarchitektur",
        "#kernfähigkeiten--sicherheitsinvarianten",
        "#auffindbarkeitskontext",
        "#warum-swarm-ai",
        "#muster",
        "#koordinations-guardrail-team-locks",
        "#installation",
        "#schnellstart",
        "#benchmarks",
        "#repository-layout",
        "#projektstatus",
        "#geschwister-tools--ökosystem",
        "#drittanbieter-lizenzen--transparenz",
        "#sicherheit",
        "#mitwirken",
    ]
    for anchor in de_anchors:
        assert anchor in readme_de, f"Anchor {anchor} must exist in README_de.md"


def test_core_capabilities_and_security_invariants_table():
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "## Core Capabilities & Security Invariants" in readme_en
    assert "## Kernfähigkeiten & Sicherheitsinvarianten" in readme_de

    capabilities = [
        "100% Local-First & Zero-Egress",
        "Parallel Chunks Pattern",
        "Boss / Worker Hierarchy",
        "Stigmergy & Pheromone Store",
        "Consensus & Majority Vote",
        "Specialist Routing",
        "Team Lock Guardrail",
        "Fail-Closed Budgeting",
        "Unprivileged User Mode",
        "Multi-OS CI Smoke Integrity",
    ]
    for cap in capabilities:
        assert cap in readme_en, f"Capability '{cap}' must be present in README.md"

    german_caps = [
        "100% Local-First & Zero-Egress",
        "Parallel-Chunks-Muster",
        "Boss-/Worker-Hierarchie",
        "Stigmergie & Pheromonspeicher",
        "Konsens & Mehrheitsentscheid",
        "Spezialisten-Routing",
        "Team-Lock-Guardrail",
        "Fail-Closed Budget-Schutz",
        "Unprivilegierter User-Mode",
        "Multi-OS CI-Smoke-Integrität",
    ]
    for cap in german_caps:
        assert cap in readme_de, f"German capability '{cap}' must be present in README_de.md"


def test_governance_invariants_table_parity():
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    invariants = [
        "INV-LOCAL-01",
        "INV-CHUNKS-02",
        "INV-HIERARCH-03",
        "INV-STORE-04",
        "INV-VOTE-05",
        "INV-ROUTER-06",
        "INV-LOCK-07",
        "INV-BUDGET-08",
        "INV-RUNAS-09",
        "INV-SLA-10",
    ]
    for inv in invariants:
        assert inv in readme_en, f"Invariant '{inv}' must be present in README.md"
        assert inv in readme_de, f"Invariant '{inv}' must be present in README_de.md"


def test_sibling_tools_and_ecosystem_matrix():
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    siblings = [
        "coma",
        "clutch",
        "MarbleRun",
        "policy-registry",
        "system-explorer",
        "sqlite-transit-sync",
        "workflowhooker",
        "memoryhooker",
        "ellmos-filecommander-mcp",
        "ellmos-codecommander-mcp",
        "ellmos-controlcenter-mcp",
        "DevCenter",
        "CodeBox",
        "ProFiler",
        "DokuZen",
        "open-bricks",
    ]
    for tool in siblings:
        assert tool in readme_en, f"Sibling '{tool}' must be listed in README.md"
        assert tool in readme_de, f"Sibling '{tool}' must be listed in README_de.md"


def test_third_party_licenses_inventory():
    licenses_file = ROOT / "THIRD_PARTY_LICENSES.md"
    assert licenses_file.exists(), "THIRD_PARTY_LICENSES.md must exist"
    content = licenses_file.read_text(encoding="utf-8")
    assert "anthropic" in content
    assert "coma" in content
    assert "pytest" in content
    assert "ruff" in content
    assert "bandit" in content
    assert "MIT License" in content


def test_marketing_log_exists():
    marketing_log = ROOT / "MARKETING-LOG.txt"
    assert marketing_log.exists(), "MARKETING-LOG.txt must exist"
    content = marketing_log.read_text(encoding="utf-8")
    assert "DISCOVERABILITY & MARKETING LOG" in content
    assert "swarm-ai" in content
    assert "INV-LOCAL-01" in content


def test_pyproject_pytest_ini_and_urls():
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '[tool.pytest.ini_options]' in pyproject_text
    assert 'addopts = "-ra -v"' in pyproject_text
    assert '"Third-Party Licenses" = ' in pyproject_text
    assert '"Marketing Log" = ' in pyproject_text


def test_mermaid_diagrams_parity():
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "flowchart TB" in readme_en
    assert "sequenceDiagram" in readme_en
    assert "flowchart TB" in readme_de
    assert "sequenceDiagram" in readme_de


def test_gitignore_hygiene_patterns():
    gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "*.sync-conflict-*" in gitignore_text
    assert "*.conflict" in gitignore_text
    assert "*-CONFLIT-*" in gitignore_text
    assert "*-conflict-*" in gitignore_text
    assert "LOCK" in gitignore_text
    assert "LOCK.*" in gitignore_text
    assert "*.lock" in gitignore_text
    assert "LOCK*.txt" in gitignore_text
    assert "LOCK.permissions.json" in gitignore_text
    assert ".ruff_cache/" in gitignore_text


def test_ruff_configuration_parity():
    pyproject_text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.ruff]" in pyproject_text
    assert 'target-version = "py310"' in pyproject_text
    assert "select = " in pyproject_text


def test_changelog_hygiene_and_latest_entry():
    changelog_text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "2026-09-11" in changelog_text
    assert "## [0.1.1] - 2026-09-11" in changelog_text
    assert "\ufffd" not in changelog_text


def test_bilingual_readme_navigation_anchor_sections():
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    en_headings = [
        "## System Architecture",
        "## Core Capabilities & Security Invariants",
        "## Discovery Context",
        "## Why swarm-ai",
        "## Patterns",
        "## Coordination Guardrail: Team Locks",
        "## Installation",
        "## Quick Start",
        "## Benchmarks",
        "## Repository Layout",
        "## Project Status",
        "## Sibling Tools & Ecosystem",
        "## Third-Party Licenses & Transparency",
        "## Security",
        "## Contributing",
    ]
    for h in en_headings:
        assert h in readme_en, f"Heading '{h}' must exist in README.md"

    de_headings = [
        "## Systemarchitektur",
        "## Kernfähigkeiten & Sicherheitsinvarianten",
        "## Auffindbarkeitskontext",
        "## Warum swarm-ai",
        "## Muster",
        "## Koordinations-Guardrail: Team-Locks",
        "## Installation",
        "## Schnellstart",
        "## Benchmarks",
        "## Repository-Struktur",
        "## Projektstatus",
        "## Geschwister-Tools & Ökosystem",
        "## Drittanbieter-Lizenzen & Transparenz",
        "## Sicherheit",
        "## Mitwirken",
    ]
    for h in de_headings:
        assert h in readme_de, f"Heading '{h}' must exist in README_de.md"


def test_marketing_log_contract_and_invariants():
    marketing_log = (ROOT / "MARKETING-LOG.txt").read_text(encoding="utf-8")
    assert "Audit Date: 2026-09-11" in marketing_log
    assert "Status: ACTIVE / PFAD B DISCOVERABILITY HARDENED" in marketing_log
    assert "2. TARGET PERSONAS & AUDIENCE MAPPING" in marketing_log
    assert "3. ARCHITECTURAL INVARIANTS & GOVERNANCE" in marketing_log

    invariants = [
        "INV-LOCAL-01",
        "INV-RUNAS-02",
        "INV-BUDGET-03",
        "INV-STORE-04",
        "INV-CHUNKS-05",
        "INV-HIERARCH-06",
        "INV-VOTE-07",
        "INV-ROUTER-08",
        "INV-LOCK-09",
        "INV-SLA-10",
    ]
    for inv in invariants:
        assert inv in marketing_log, f"Invariant {inv} must exist in MARKETING-LOG.txt"


def test_readme_badge_matrix_parity():
    readme_en = (ROOT / "README.md").read_text(encoding="utf-8")
    readme_de = (ROOT / "README_de.md").read_text(encoding="utf-8")

    assert "version-0.1.1-blue" in readme_en
    assert "version-0.1.1-blue" in readme_de

    assert "CI-passing-brightgreen" in readme_en
    assert "CI-passing-brightgreen" in readme_de

    assert "tests-213" in readme_en
    assert "tests-213" in readme_de

    assert "third--party-audited" in readme_en
    assert "drittanbieter-gepr" in readme_de

    assert "marketing--log-active" in readme_en
    assert "marketing--log-aktiv" in readme_de

    assert "last--checked-2026--09--11-blue" in readme_en
    assert "letzte--pr%C3%BCfung-2026--09--11-blue" in readme_de


def test_third_party_licenses_audit_and_non_elevation():
    licenses_text = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    assert "- **Audit Date:** 2026-09-11" in licenses_text
    assert "RunAsInvoker Non-Elevation" in licenses_text
    assert "Fail-Closed Evidence Acceptance" in licenses_text
    assert "No copyleft (GPL / AGPL)" in licenses_text
