"""Deterministic scenario planning from explicit contract behaviors."""

from .contracts import Behavior, Contract


def plan_scenarios(contract: Contract) -> tuple[Behavior, ...]:
    """Return declared cases in stable order; this version does not invent cases."""
    return contract.behaviors
