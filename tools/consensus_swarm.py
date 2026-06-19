#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
consensus_swarm.py - Consensus swarm pattern with Claude API
==============================================================

Run multiple LLM instances on the same question in parallel,
then compare results and take a majority decision.

Use cases:
- Fact validation (is a statement true?)
- Classification (which category?)
- Extraction (which entities?)
- Quality control (is a summary correct?)

Usage:
    python consensus_swarm.py "What is the capital of France?"
    python consensus_swarm.py --agents 5 --question "Is Python typed?"
    python consensus_swarm.py --mode classify --categories "positive,negative,neutral" --question "The movie was okay."
    python consensus_swarm.py --dry-run --question "Test question"

Author: Lukas Geiger (ellmos-ai)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import anthropic

try:
    import anthropic  # noqa: F811
except ImportError:
    anthropic = None  # noqa: F811

# --- Constants ---

MODEL = "claude-haiku-4-5-20251001"
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0
DEFAULT_AGENTS = 5
DEFAULT_WORKERS = 5

COST_PER_1M = {"input": 1.00, "output": 5.00}  # Haiku-Preise

# --- API Key ---


def get_api_key() -> str:
    """API-Key aus Env-Variable ANTHROPIC_API_KEY laden."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        return api_key

    raise ValueError(
        "ANTHROPIC_API_KEY nicht konfiguriert!\n"
        "  export ANTHROPIC_API_KEY=sk-ant-api03-..."
    )


# --- Swarm Agents ---


def query_agent(client: anthropic.Anthropic, agent_id: int,
                system_prompt: str, user_prompt: str) -> Dict:
    """
    Einzelner Agent beantwortet die Frage.

    Returns:
        Dict mit answer, agent_id, input_tokens, output_tokens, error
    """
    for attempt in range(MAX_RETRIES):
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=256,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.7,  # Some variance for diversity
            )

            answer = message.content[0].text.strip()

            return {
                "agent_id": agent_id,
                "answer": answer,
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
                "error": None,
            }

        except Exception as e:
            error_str = str(e)

            if "rate" in error_str.lower() or "429" in error_str:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
                continue

            if "overloaded" in error_str.lower() or "529" in error_str:
                time.sleep(RETRY_BASE_DELAY * (attempt + 1))
                continue

            if attempt >= MAX_RETRIES - 1:
                return {
                    "agent_id": agent_id,
                    "answer": None,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "error": error_str[:200],
                }

            time.sleep(RETRY_BASE_DELAY)

    return {
        "agent_id": agent_id,
        "answer": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "error": f"Max Retries ({MAX_RETRIES}) erreicht",
    }


def build_prompts(question: str, mode: str = "answer",
                  categories: Optional[List[str]] = None) -> Tuple[str, str]:
    """
    Baut System- und User-Prompt je nach Modus.

    Returns:
        (system_prompt, user_prompt)
    """
    if mode == "classify" and categories:
        cat_str = ", ".join(categories)
        system_prompt = (
            "Du bist ein Klassifikations-Agent. "
            f"Kategorisiere die Eingabe in GENAU EINE der folgenden Kategorien: {cat_str}\n\n"
            "REGELN:\n"
            "- Antworte NUR mit dem Kategorienamen\n"
            "- Keine Erklaerung, kein Satz, nur das eine Wort\n"
            "- Wenn keine Kategorie passt, waehle die naechstliegende"
        )
        user_prompt = question

    elif mode == "boolean":
        system_prompt = (
            "Du bist ein Fakten-Pruefungs-Agent. "
            "Beantworte die Frage mit JA oder NEIN.\n\n"
            "REGELN:\n"
            "- Antworte NUR mit 'JA' oder 'NEIN'\n"
            "- Keine Erklaerung, nur ein Wort"
        )
        user_prompt = question

    else:  # mode == "answer"
        system_prompt = (
            "Du bist ein Wissens-Agent in einem Schwarm-System. "
            "Beantworte die Frage praezise und kurz (1-2 Saetze).\n\n"
            "REGELN:\n"
            "- Kurz und praezise antworten\n"
            "- Faktenbasiert\n"
            "- Keine Einleitungen wie 'Die Antwort ist...'"
        )
        user_prompt = question

    return system_prompt, user_prompt


def compute_consensus(results: List[Dict], mode: str = "answer") -> Dict:
    """
    Berechnet Konsensus aus mehreren Agent-Antworten.

    Returns:
        Dict mit consensus_answer, confidence, agreement_ratio, votes
    """
    valid_answers = [r["answer"] for r in results if r["answer"] is not None]

    if not valid_answers:
        return {
            "consensus_answer": None,
            "confidence": 0.0,
            "agreement_ratio": 0.0,
            "votes": {},
            "total_agents": len(results),
            "valid_responses": 0,
        }

    # Normalisierung je nach Modus
    if mode in ("classify", "boolean"):
        # Exakter Vergleich (case-insensitive)
        normalized = [a.strip().upper() for a in valid_answers]
    else:
        # Fuer freie Antworten: lowercase, Satzzeichen entfernen
        normalized = [a.strip().lower().rstrip('.!?') for a in valid_answers]

    vote_counts = Counter(normalized)
    winner, winner_count = vote_counts.most_common(1)[0]

    # Confidence = Anteil der Stimmen fuer den Gewinner
    confidence = winner_count / len(valid_answers)

    # Originale Antwort fuer den Gewinner finden
    for answer, norm in zip(valid_answers, normalized):
        if norm == winner:
            consensus_answer = answer
            break

    return {
        "consensus_answer": consensus_answer,
        "confidence": confidence,
        "agreement_ratio": confidence,
        "votes": dict(vote_counts),
        "total_agents": len(results),
        "valid_responses": len(valid_answers),
    }


# --- Main Orchestration ---


def run_consensus(question: str, num_agents: int = DEFAULT_AGENTS,
                  workers: int = DEFAULT_WORKERS, mode: str = "answer",
                  categories: Optional[List[str]] = None,
                  dry_run: bool = False) -> Dict:
    """
    Fuehrt Konsensus-Schwarm aus.

    Returns:
        Dict mit consensus, individual_results, stats
    """
    system_prompt, user_prompt = build_prompts(question, mode, categories)

    print(f"[KONSENSUS] Frage: {question}")
    print(f"[KONSENSUS] Modus: {mode}")
    print(f"[KONSENSUS] Agenten: {num_agents}, Worker: {workers}\n")

    if dry_run:
        est_input = num_agents * (len(system_prompt) + len(question)) // 4
        est_output = num_agents * 50
        est_cost = (est_input * COST_PER_1M["input"] + est_output * COST_PER_1M["output"]) / 1_000_000
        print(f"[DRY-RUN] Geschaetzte Kosten: ${est_cost:.6f}")
        print(f"           Input-Tokens:  ~{est_input}")
        print(f"           Output-Tokens: ~{est_output}")
        print(f"           API-Calls: {num_agents}")
        return {"dry_run": True}

    api_key = get_api_key()
    client = anthropic.Anthropic(api_key=api_key)

    # Execute in parallel
    results = []
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(query_agent, client, i, system_prompt, user_prompt): i
            for i in range(num_agents)
        }

        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            agent_id = result["agent_id"]

            if result["error"]:
                print(f"  Agent {agent_id}: FEHLER - {result['error'][:80]}")
            else:
                preview = result["answer"][:80] if result["answer"] else "?"
                print(f"  Agent {agent_id}: {preview}")

    elapsed = time.time() - start_time

    # Konsensus berechnen
    consensus = compute_consensus(results, mode)

    # Token statistics
    total_input = sum(r["input_tokens"] for r in results)
    total_output = sum(r["output_tokens"] for r in results)
    total_cost = (total_input * COST_PER_1M["input"] + total_output * COST_PER_1M["output"]) / 1_000_000

    # Output
    print(f"\n{'=' * 60}")
    print(f"  KONSENSUS-ERGEBNIS")
    print(f"{'=' * 60}")
    print(f"  Antwort:         {consensus['consensus_answer']}")
    print(f"  Confidence:      {consensus['confidence']:.0%}")
    print(f"  Uebereinstimmung: {consensus['valid_responses']}/{consensus['total_agents']} Agenten")
    print(f"  Stimmen:         {consensus['votes']}")
    print(f"{'=' * 60}")
    print(f"  Dauer:           {elapsed:.1f}s")
    print(f"  Input-Tokens:    {total_input}")
    print(f"  Output-Tokens:   {total_output}")
    print(f"  Kosten:          ${total_cost:.6f}")
    print(f"{'=' * 60}")

    return {
        "consensus": consensus,
        "individual_results": results,
        "stats": {
            "elapsed_s": elapsed,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost_usd": total_cost,
        },
    }


# --- CLI ---


def main():
    parser = argparse.ArgumentParser(
        description="Konsensus-Schwarm: Mehrere LLM-Agenten beantworten dieselbe Frage"
    )
    parser.add_argument(
        "question", nargs="?", default=None,
        help="The question (alternative: --question)"
    )
    parser.add_argument(
        "--question", "-q", dest="question_flag",
        help="The question (alternative as flag)"
    )
    parser.add_argument(
        "--agents", "-a", type=int, default=DEFAULT_AGENTS,
        help=f"Number of agents (default: {DEFAULT_AGENTS})"
    )
    parser.add_argument(
        "--workers", "-w", type=int, default=DEFAULT_WORKERS,
        help=f"Parallel threads (default: {DEFAULT_WORKERS})"
    )
    parser.add_argument(
        "--mode", "-m", choices=["answer", "classify", "boolean"],
        default="answer",
        help="Mode: answer (free), classify (categories), boolean (yes/no)"
    )
    parser.add_argument(
        "--categories", "-c",
        help="Comma-separated categories for classify mode"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Cost estimation only, no API call"
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Ausgabe als JSON"
    )

    args = parser.parse_args()

    question = args.question or args.question_flag
    if not question:
        parser.error("Question required (as argument or --question)")

    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    result = run_consensus(
        question=question,
        num_agents=args.agents,
        workers=args.workers,
        mode=args.mode,
        categories=categories,
        dry_run=args.dry_run,
    )

    if args.json_output and not args.dry_run:
        # JSON-Ausgabe (ohne individuelle Details fuer Kompaktheit)
        output = {
            "question": question,
            "mode": args.mode,
            "consensus_answer": result["consensus"]["consensus_answer"],
            "confidence": result["consensus"]["confidence"],
            "votes": result["consensus"]["votes"],
            "agents": result["consensus"]["total_agents"],
            "stats": result["stats"],
        }
        print(f"\n{json.dumps(output, ensure_ascii=False, indent=2)}")

    # Exit-Code: 0 wenn Confidence >= 60%, sonst 1
    if not args.dry_run:
        confidence = result.get("consensus", {}).get("confidence", 0)
        sys.exit(0 if confidence >= 0.6 else 1)


if __name__ == "__main__":
    main()
