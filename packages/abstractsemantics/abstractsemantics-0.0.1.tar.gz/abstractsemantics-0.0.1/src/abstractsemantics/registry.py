from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import yaml


@dataclass(frozen=True)
class PredicateDef:
    id: str
    label: Optional[str] = None
    inverse: Optional[str] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class EntityTypeDef:
    id: str
    label: Optional[str] = None
    parent: Optional[str] = None
    description: Optional[str] = None


@dataclass(frozen=True)
class SemanticsRegistry:
    version: int
    prefixes: Dict[str, str]
    predicates: List[PredicateDef]
    entity_types: List[EntityTypeDef]

    def predicate_ids(self) -> set[str]:
        return {p.id for p in self.predicates if isinstance(p.id, str) and p.id.strip()}

    def entity_type_ids(self) -> set[str]:
        return {t.id for t in self.entity_types if isinstance(t.id, str) and t.id.strip()}


def resolve_semantics_registry_path() -> Path:
    """Resolve the registry YAML path.

    Env override:
    - ABSTRACTSEMANTICS_REGISTRY_PATH
    """
    raw = os.getenv("ABSTRACTSEMANTICS_REGISTRY_PATH")
    if isinstance(raw, str) and raw.strip():
        p = Path(raw).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"ABSTRACTSEMANTICS_REGISTRY_PATH does not exist: {p}")
        return p
    return Path(__file__).with_name("semantics.yaml")


def _as_list(value: Any) -> list:
    return list(value) if isinstance(value, list) else []


def _load_yaml(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    return data if isinstance(data, dict) else {}


def load_semantics_registry(path: Path | None = None) -> SemanticsRegistry:
    p = path or resolve_semantics_registry_path()
    data = _load_yaml(p)

    version_raw = data.get("version", 0)
    try:
        version = int(version_raw)
    except Exception:
        version = 0

    prefixes_raw = data.get("prefixes")
    prefixes: Dict[str, str] = {}
    if isinstance(prefixes_raw, dict):
        for k, v in prefixes_raw.items():
            if isinstance(k, str) and isinstance(v, str) and k.strip() and v.strip():
                prefixes[k.strip()] = v.strip()

    predicates: list[PredicateDef] = []
    for item in _as_list(data.get("predicates")):
        if not isinstance(item, dict):
            continue
        pid = item.get("id")
        if not isinstance(pid, str) or not pid.strip():
            continue
        predicates.append(
            PredicateDef(
                id=pid.strip(),
                label=item.get("label") if isinstance(item.get("label"), str) else None,
                inverse=item.get("inverse") if isinstance(item.get("inverse"), str) else None,
                description=item.get("description") if isinstance(item.get("description"), str) else None,
            )
        )

    entity_types: list[EntityTypeDef] = []
    for item in _as_list(data.get("entity_types")):
        if not isinstance(item, dict):
            continue
        tid = item.get("id")
        if not isinstance(tid, str) or not tid.strip():
            continue
        entity_types.append(
            EntityTypeDef(
                id=tid.strip(),
                label=item.get("label") if isinstance(item.get("label"), str) else None,
                parent=item.get("parent") if isinstance(item.get("parent"), str) else None,
                description=item.get("description") if isinstance(item.get("description"), str) else None,
            )
        )

    if not predicates:
        raise ValueError(f"Semantics registry has no predicates: {p}")

    return SemanticsRegistry(
        version=version,
        prefixes=prefixes,
        predicates=predicates,
        entity_types=entity_types,
    )


