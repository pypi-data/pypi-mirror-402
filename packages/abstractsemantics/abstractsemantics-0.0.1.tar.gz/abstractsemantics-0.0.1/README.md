# AbstractSemantics

Central, editable semantics registry for AbstractFramework.

This package intentionally contains **definitions**, not storage:
- prefix mappings (CURIE namespaces)
- predicate allowlists (and optional inverses/constraints)
- entity-type allowlists (optional in v0)

It is designed to be consumed by:
- AbstractRuntime (validation at ingestion boundary)
- AbstractFlow (UI dropdowns + authoring support)
- AbstractMemory (storage/query on top of validated semantics)

