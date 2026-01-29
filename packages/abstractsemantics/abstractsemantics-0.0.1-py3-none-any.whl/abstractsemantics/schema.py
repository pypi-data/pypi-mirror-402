from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .registry import SemanticsRegistry, load_semantics_registry

# Stable reference strings for flow-authored schemas.
#
# Visual flows may reference these via a `json_schema` literal like:
#   {"$ref": "abstractsemantics:kg_assertion_schema_v0"}
# The runtime resolves them into a concrete JSON Schema dict at execution time.
KG_ASSERTION_SCHEMA_REF_V0 = "abstractsemantics:kg_assertion_schema_v0"


# Small, deterministic alias set for predicates that LLMs tend to emit by default.
#
# These are *not* part of the canonical semantics registry. Prefer keeping
# structured-output enums canonical (so the model is forced to pick from the
# agreed semantics). Alias handling belongs at the ingestion boundary.
#
# Keep this list intentionally small to protect model context + reduce confusion.
KG_PREDICATE_ALIASES_V0: Sequence[str] = (
    "schema:description",
    "schema:creator",
    "schema:hasParent",
    "schema:hasMember",
    "schema:recognizedAs",
    "schema:hasMemorySource",
    "schema:hasPart",
    "schema:isPartOf",
    "dcterms:has_part",
    "dcterms:is_part_of",
)


def _dedup_preserve_order(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if not isinstance(v, str):
            continue
        v2 = v.strip()
        if not v2 or v2 in seen:
            continue
        seen.add(v2)
        out.append(v2)
    return out


def build_kg_assertion_schema_v0(
    registry: Optional[SemanticsRegistry] = None,
    *,
    include_predicate_aliases: bool = False,
    max_assertions: int = 12,
    min_assertions_when_nonempty: int = 3,
    max_evidence_quote_len: int = 160,
    max_original_context_len: int = 280,
) -> Dict[str, Any]:
    """Build the structured-output JSON Schema used by the KG extractor workflows.

    This schema is deliberately small and meant to be stable:
    - `predicate` is restricted to the semantics registry (+ optional aliases).
    - `subject_type` / `object_type` are restricted to the registry entity types.
    - Evidence fields are bounded (short verbatim snippets).
    """
    reg = registry or load_semantics_registry()

    predicate_ids: List[str] = [p.id for p in reg.predicates if isinstance(p.id, str) and p.id.strip()]
    if include_predicate_aliases:
        predicate_ids = list(predicate_ids) + list(KG_PREDICATE_ALIASES_V0)
    predicate_ids = _dedup_preserve_order(predicate_ids)

    entity_type_ids: List[str] = [t.id for t in reg.entity_types if isinstance(t.id, str) and t.id.strip()]
    entity_type_ids = _dedup_preserve_order(entity_type_ids)

    if not predicate_ids:
        raise ValueError("Semantics registry provided no predicate ids")
    if not entity_type_ids:
        raise ValueError("Semantics registry provided no entity type ids")

    max_assertions2 = max(0, int(max_assertions))
    min_nonempty2 = max(0, int(min_assertions_when_nonempty))
    if max_assertions2 and min_nonempty2 and min_nonempty2 > max_assertions2:
        min_nonempty2 = max_assertions2

    assertions_schema: Dict[str, Any] = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "predicate": {"type": "string", "enum": predicate_ids},
                "object": {"type": "string"},
                "confidence": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                "valid_from": {"type": ["string", "null"]},
                "valid_until": {"type": ["string", "null"]},
                "provenance": {"type": ["object", "null"]},
                "attributes": {
                    "type": "object",
                    "properties": {
                        "subject_type": {"type": "string", "enum": entity_type_ids},
                        "object_type": {"type": "string", "enum": entity_type_ids},
                        "evidence_quote": {"type": "string", "maxLength": int(max_evidence_quote_len)},
                        "original_context": {"type": "string", "maxLength": int(max_original_context_len)},
                    },
                    "required": ["evidence_quote"],
                },
            },
            "required": ["subject", "predicate", "object", "attributes"],
        },
    }

    if max_assertions2:
        assertions_schema["maxItems"] = max_assertions2
    if min_nonempty2:
        # Either:
        # - empty list (no facts), OR
        # - at least N assertions (avoid low-signal singletons that “technically” validate).
        assertions_schema["anyOf"] = [{"maxItems": 0}, {"minItems": min_nonempty2}]

    return {
        "type": "object",
        "properties": {
            "assertions": assertions_schema
        },
        "required": ["assertions"],
    }


def resolve_schema_ref(schema: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Resolve a schema reference dict to a concrete JSON Schema (if supported)."""
    ref = schema.get("$ref")
    if isinstance(ref, str) and ref.strip():
        if ref.strip() == KG_ASSERTION_SCHEMA_REF_V0:
            return build_kg_assertion_schema_v0()
    return None
