from __future__ import annotations

from abstractsemantics import load_semantics_registry


def test_load_semantics_registry_has_predicates():
    reg = load_semantics_registry()
    ids = reg.predicate_ids()
    assert "rdf:type" in ids
    assert "dcterms:isPartOf" in ids

