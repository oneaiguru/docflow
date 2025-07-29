import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .rights import RolesRegistry, BitSet


@dataclass
class Action:
    name: str
    service: bool = False


@dataclass
class DocType:
    name: str
    fields: Dict[str, str]
    actions: Dict[str, Action] = field(default_factory=dict)
    states: List[str] = field(default_factory=list)
    rights: Dict[str, Dict[str, bool]] = field(default_factory=dict)
    rights_bits: Dict[str, BitSet] = field(default_factory=dict)
    rights_roles: Optional[RolesRegistry] = None
    links: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: Dict, roles: Optional[RolesRegistry] = None) -> 'DocType':
        actions = {a['name']: Action(**a) for a in data.get('actions', [])}
        rights = data.get('rights', {})
        rights_bits: Dict[str, BitSet] = {}
        if roles:
            for action, role_map in rights.items():
                allowed = [r for r, allow in role_map.items() if allow]
                rights_bits[action.lower()] = roles.mask(allowed)
        return cls(
            name=data['name'],
            fields={f['id']: f['type'] for f in data.get('fields', [])},
            actions=actions,
            states=data.get('states', []),
            rights=rights,
            rights_bits=rights_bits,
            rights_roles=roles,
            links=data.get('links', {})
        )


class DocTypesRegistry:
    """Registry storing loaded document type definitions."""

    def __init__(self, roles: Optional[RolesRegistry] = None):
        self.types: Dict[str, DocType] = {}
        self.roles = roles or RolesRegistry()

    def load(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        doc_type = DocType.from_json(data, self.roles)
        self.types[doc_type.name] = doc_type
        return doc_type

    def get(self, name: str) -> Optional[DocType]:
        return self.types.get(name)
