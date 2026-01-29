"""This module implements a workflow engine for multistep form data.

1) Each step is defined as a class (FormStep subclass) with a BaseConfigurableData schema.
2) Sessions are in-memory only.
3) All mutable state is stored in a FactStore as versioned stacks keyed by fact name.
4) Each successful submit creates a checkpoint (also stored as reserved fact stacks).
5) Back: rolls back exactly one checkpoint and reverts the leaving step before popping facts.
"""
