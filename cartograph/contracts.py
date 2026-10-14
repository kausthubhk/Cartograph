"""Loading and validation for Cartograph's small behavior-contract format."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Raised when a contract is malformed or incomplete."""


@dataclass(frozen=True)
class Behavior:
    scenario_id: str
    given: str
    when: str
    then: str
    fixture: str


@dataclass(frozen=True)
class Contract:
    service: str
    method: str
    input_type: str
    field_names: tuple[str, ...]
    behaviors: tuple[Behavior, ...]

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Contract":
        required = ("service", "method", "input_type", "fields", "behaviors")
        missing = [key for key in required if key not in raw]
        if missing:
            raise ContractError(f"missing required contract keys: {', '.join(missing)}")

        for key in ("service", "method", "input_type"):
            if not isinstance(raw[key], str) or not raw[key].strip():
                raise ContractError(f"{key} must be a non-empty string")

        fields = raw["fields"]
        if not isinstance(fields, list) or not all(
            isinstance(field, str) and field.strip() for field in fields
        ):
            raise ContractError("fields must be a list of non-empty strings")
        if len(fields) != len(set(fields)):
            raise ContractError("fields must not contain duplicates")

        behaviors: list[Behavior] = []
        if not isinstance(raw["behaviors"], list) or not raw["behaviors"]:
            raise ContractError("behaviors must be a non-empty list")
        for index, item in enumerate(raw["behaviors"]):
            if not isinstance(item, dict):
                raise ContractError(f"behaviors[{index}] must be an object")
            keys = ("scenario_id", "given", "when", "then", "fixture")
            absent = [key for key in keys if key not in item]
            if absent:
                raise ContractError(
                    f"behaviors[{index}] is missing: {', '.join(absent)}"
                )
            if any(not isinstance(item[key], str) or not item[key].strip() for key in keys):
                raise ContractError(f"behaviors[{index}] values must be non-empty strings")
            behaviors.append(Behavior(**{key: item[key] for key in keys}))

        ids = [behavior.scenario_id for behavior in behaviors]
        if len(ids) != len(set(ids)):
            raise ContractError("scenario_id values must be unique")
        return cls(
            service=raw["service"],
            method=raw["method"],
            input_type=raw["input_type"],
            field_names=tuple(fields),
            behaviors=tuple(behaviors),
        )


def load_contract(path: Path) -> Contract:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"contract file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON at line {exc.lineno}: {exc.msg}") from exc
    if not isinstance(raw, dict):
        raise ContractError("contract root must be a JSON object")
    return Contract.from_dict(raw)
