---
name: api-design
description: Design or evolve application interfaces with consistent, backward-compatible contracts.
---

# API Design

Use this skill when adding, changing, or reviewing a public function, module boundary, HTTP endpoint, or data schema.

## Instructions

Identify the callers and consumers before designing. Read the existing interfaces and follow their conventions for naming, errors, pagination, versioning, and authentication.

Define the contract explicitly: inputs, outputs, error cases, edge cases, and invariants.

Prefer additive, backward-compatible changes. Deprecate before removing, and keep old behavior working long enough for callers to migrate.

Validate at the boundary and fail with clear, actionable errors. Do not leak internal stack traces or sensitive values.

Keep naming and semantics consistent across similar operations, including optional and null values, identifiers, timestamps, and units.

Make retry-sensitive operations idempotent or document why they are not.

Document the contract and add or update tests that exercise it, including the error cases.
