import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional


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
    links: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_json(cls, data: Dict) -> 'DocType':
        actions = {a['name']: Action(**a) for a in data.get('actions', [])}
        return cls(
            name=data['name'],
            fields={f['id']: f['type'] for f in data.get('fields', [])},
            actions=actions,
            states=data.get('states', []),
            rights=data.get('rights', {}),
            links=data.get('links', {})
        )


class DocTypesRegistry:
    """Registry storing loaded document type definitions."""

    def __init__(self):
        self.types: Dict[str, DocType] = {}

    def load(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        doc_type = DocType.from_json(data)
        self.types[doc_type.name] = doc_type
        return doc_type

    def get(self, name: str) -> Optional[DocType]:
        return self.types.get(name)
