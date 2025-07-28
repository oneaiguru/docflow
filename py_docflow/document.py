from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Document:
    """Base document with minimal state handling."""
    id: Optional[int] = None
    _doc_type: Any = field(init=False, repr=False, default=None)
    _state: str = field(init=False, default="NEW")
    links: Dict[str, int] = field(default_factory=dict)

    def _docType(self):
        return self._doc_type

    def _state_name(self) -> str:
        return self._state

    def _fullId(self) -> str:
        return f"{self._docType().name}:{self.id}" if self.id is not None else f"{self._docType().name}:NEW"

    def _isPersisted(self) -> bool:
        return self.id is not None

    def _updateState(self, new_state: str):
        self._state = new_state

    def calculate(self, fields: Optional[Dict[str, Any]] = None):
        # Placeholder for calculated fields logic
        pass


@dataclass
class DocumentPersistent(Document):
    """Document that can be reloaded from storage."""

    def _attached(self, storage: Dict[int, 'DocumentPersistent']):
        if not self._isPersisted():
            return self
        return storage.get(self.id)


@dataclass
class DocumentSimple(DocumentPersistent):
    """Document with creator and created timestamp."""

    creator: str = "system"
    created: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DocumentVersioned(DocumentPersistent):
    """Versioned document with revision tracking."""

    rev: int = 0
    created: datetime = field(default_factory=datetime.utcnow)
    modified: datetime = field(default_factory=datetime.utcnow)
    deleted: bool = False

    def touch(self):
        self.modified = datetime.utcnow()
        self.rev += 1


@dataclass
class DocumentHistoryEntry:
    """Snapshot of a document revision."""

    rev: int
    timestamp: datetime
    data: Dict[str, Any]
    action: str


@dataclass
class DocumentFile(DocumentSimple):
    """Simple file document storing raw bytes."""

    filename: str = ""
    data: bytes = b""
    text: str = ""

