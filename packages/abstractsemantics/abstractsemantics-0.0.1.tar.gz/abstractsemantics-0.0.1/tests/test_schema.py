from __future__ import annotations

from abstractsemantics import (
    KG_ASSERTION_SCHEMA_REF_V0,
    build_kg_assertion_schema_v0,
    load_semantics_registry,
    resolve_schema_ref,
)


def test_build_kg_assertion_schema_v0_tracks_registry_predicates_and_types() -> None:
    reg = load_semantics_registry()
    schema = build_kg_assertion_schema_v0(registry=reg, include_predicate_aliases=True)

    pred_enum = schema["properties"]["assertions"]["items"]["properties"]["predicate"]["enum"]
    assert isinstance(pred_enum, list) and pred_enum
    for pid in reg.predicate_ids():
        assert pid in pred_enum

    type_enum = schema["properties"]["assertions"]["items"]["properties"]["attributes"]["properties"]["subject_type"]["enum"]
    assert isinstance(type_enum, list) and type_enum
    for tid in reg.entity_type_ids():
        assert tid in type_enum


def test_build_kg_assertion_schema_v0_can_disable_aliases() -> None:
    reg = load_semantics_registry()
    schema = build_kg_assertion_schema_v0(registry=reg, include_predicate_aliases=False)
    pred_enum = schema["properties"]["assertions"]["items"]["properties"]["predicate"]["enum"]
    assert "schema:creator" not in pred_enum
    assert "schema:description" not in pred_enum


def test_resolve_schema_ref_returns_concrete_schema() -> None:
    resolved = resolve_schema_ref({"$ref": KG_ASSERTION_SCHEMA_REF_V0})
    assert isinstance(resolved, dict)
    assert resolved.get("type") == "object"
    assert "assertions" in resolved.get("properties", {})

