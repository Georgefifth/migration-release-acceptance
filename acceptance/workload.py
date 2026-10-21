"""Reviewed code-level workload configuration; no dynamic uploaded plugins."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Workload:
    name: str = 'customer-reference'
    fixtures: Path = Path(__file__).resolve().parent.parent / 'fixtures'
    entity: str = 'customer'
    initialize: Callable | None = None
    initial: str = 'initial@example.test'
    created: str = 'created@example.test'
    old_write: str = 'old-write@example.test'
    new_write: str = 'new-write@example.test'
    new_update: str = 'new-update@example.test'
    old_update: str = 'old-update@example.test'
    provenance: dict = field(default_factory=dict)
    application_scope: str = 'Two synthetic HTTP app processes using separate per-request database connections.'
