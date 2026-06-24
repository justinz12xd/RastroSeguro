"""Entity extraction for relationship-based risk analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

ENTITY_FIELDS = {
    "asegurado": ["id_asegurado"],
    "proveedor": ["id_proveedor", "proveedor", "clinica", "proveedor_reparacion"],
    "beneficiario": ["beneficiario"],
    "vehiculo": ["id_vehiculo", "placa_hash"],
    "taller": ["taller"],
    "conductor": ["id_conductor", "conductor", "conductor_hash"],
    "ciudad": ["ciudad"],
    "ramo": ["ramo"],
    "cobertura": ["cobertura"],
    "intermediario": ["id_intermediario", "intermediario"],
}

RISK_ENTITY_TYPES = {"proveedor", "beneficiario", "vehiculo", "taller", "conductor", "intermediario"}


@dataclass(frozen=True)
class EntityRef:
    entity_type: str
    value: str
    field: str

    @property
    def key(self) -> str:
        return f"{self.entity_type}:{self.value}"

    def to_dict(self) -> dict[str, str]:
        return {"type": self.entity_type, "value": self.value, "field": self.field, "key": self.key}


def is_present(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(text) and text.lower() not in {"nan", "none", "null", "na", "n/a"}


def extract_entities(claim: dict[str, Any]) -> list[EntityRef]:
    entities: list[EntityRef] = []
    for entity_type, fields in ENTITY_FIELDS.items():
        for field in fields:
            value = claim.get(field)
            if is_present(value):
                entities.append(EntityRef(entity_type=entity_type, value=str(value).strip(), field=field))
                break
    return entities


def graph_connections(claim: dict[str, Any]) -> list[dict[str, str]]:
    return [entity.to_dict() for entity in extract_entities(claim)]
