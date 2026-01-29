from __future__ import annotations

import difflib
from typing import List, Optional, Type

__all__ = [
    "RecordCatalog",
    "record_id",
    "close_matches",
]


class RecordCatalog:
    """Registry for mapping friendly record names to NetSuite record type IDs.
    
    Ships with built-in mappings for common record types:
    - projects -> job
    - contacts -> contact  
    - customers -> customer
    - partners -> partner
    - employees -> employee
    """
    _map: dict[str, str] = {
        "projects": "job",
        "contacts": "contact",
        "customers": "customer",
        "partners": "partner",
        "employees": "employee",
    }

    @classmethod
    def register(cls, original_name: str, field_id: str):
        """Register a mapping from friendly name to NetSuite record type ID."""
        cls._map[original_name.lower()] = field_id.lower()

    @classmethod
    def get(cls, original_name: str) -> Optional[str]:
        """Get the NetSuite record type ID for a friendly name."""
        return cls._map.get(original_name.lower())

    @classmethod
    def registered_names(cls) -> List[str]:
        """Get all registered friendly names."""
        return list(cls._map.keys())


def record_id(original_name: str, catalog_cls: Type[RecordCatalog]) -> str:
    id_ = catalog_cls.get(original_name)
    if id_:
        return id_

    matches = close_matches(original_name, catalog_cls.registered_names())
    if matches:
        raise ValueError(
            f"Invalid record name: {original_name}. Did you mean {matches[0]}?"
        )
    raise ValueError(
        f"Invalid record name: {original_name}. Did you forget to register it?"
    )


def close_matches(word: str, possibilities: List[str]) -> List[str]:
    return difflib.get_close_matches(word, possibilities)
