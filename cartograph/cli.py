"""Command-line interface for the offline Cartograph prototype."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .contracts import ContractError, load_contract
from .planner import plan_scenarios
from .providers import FixtureProvider, UnsupportedScenario


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cartograph")
    commands = parser.add_subparsers(dest="command", required=True)

    plan = commands.add_parser("plan", help="list scenarios declared by a contract")
    plan.add_argument("contract", type=Path)

    generate = commands.add_parser("generate", help="render one test using an offline provider")
    generate.add_argument("contract", type=Path)
    generate.add_argument("--scenario", required=True)
    generate.add_argument("--provider", choices=("fixture",), default="fixture")
    generate.add_argument("--output", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        contract = load_contract(args.contract)
        scenarios = plan_scenarios(contract)
        if args.command == "plan":
            for behavior in scenarios:
                print(f"{behavior.scenario_id}: {behavior.given}; {behavior.when}; {behavior.then}")
            return 0

        selected = next(
            (behavior for behavior in scenarios if behavior.scenario_id == args.scenario), None
        )
        if selected is None:
            available = ", ".join(behavior.scenario_id for behavior in scenarios)
            raise ContractError(f"unknown scenario {args.scenario!r}; available: {available}")
        generated = FixtureProvider().generate(contract, selected)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(generated, encoding="utf-8", newline="\n")
        print(f"wrote {args.output}")
        return 0
    except (ContractError, UnsupportedScenario, OSError) as exc:
        print(f"cartograph: error: {exc}", file=sys.stderr)
        return 2
