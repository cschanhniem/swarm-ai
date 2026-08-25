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
    assert pyproject_version == "0.1.0"


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

    assert "https://github.com/ellmos-ai/swarm-ai" in llms_txt
    assert "https://github.com/ellmos-ai/swarm-ai" in readme_en
    assert "https://github.com/ellmos-ai/swarm-ai" in readme_de

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


def test_gitignore_hygiene_patterns():
    gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "*.sync-conflict-*" in gitignore_text
    assert "*.conflict" in gitignore_text
    assert "LOCK*.txt" in gitignore_text
    assert ".ruff_cache/" in gitignore_text
