from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Type, Any
from copy import deepcopy
from .document import DocumentPersistent, DocumentVersioned, DocumentHistoryEntry


class InMemoryStorage:
    """Simple in-memory storage for documents."""

    def __init__(self):
        self._data: Dict[str, Dict[int, DocumentPersistent]] = {}
        self._counter: Dict[str, int] = {}
        self._history: Dict[str, Dict[int, List[DocumentHistoryEntry]]] = {}

    def insert(self, doc_type: str, doc: DocumentPersistent) -> DocumentPersistent:
        docs = self._data.setdefault(doc_type, {})
        idx = self._counter.get(doc_type, 0) + 1
        self._counter[doc_type] = idx
        doc.id = idx
        docs[idx] = doc
        self._history.setdefault(doc_type, {})[idx] = []
        return doc

    def get(self, doc_type: str, doc_id: int) -> DocumentPersistent:
        return self._data.get(doc_type, {}).get(doc_id)

    def update(self, doc_type: str, doc: DocumentPersistent):
        docs = self._data.setdefault(doc_type, {})
        docs[doc.id] = doc

    def add_history(self, doc_type: str, doc: DocumentVersioned, action: str):
        entry = DocumentHistoryEntry(
            rev=doc.rev,
            timestamp=datetime.utcnow(),
            data={k: v for k, v in asdict(doc).items() if k != "_doc_type"},
            action=action,
        )
        self._history.setdefault(doc_type, {}).setdefault(doc.id, []).append(entry)

    def history(self, doc_type: str, doc_id: int) -> List[DocumentHistoryEntry]:
        return self._history.get(doc_type, {}).get(doc_id, [])

    def all(self, doc_type: str):
        return list(self._data.get(doc_type, {}).values())


class Transaction:
    """Context manager providing basic rollback for InMemoryStorage."""

    def __init__(self, storage: InMemoryStorage):
        self.storage = storage

    def __enter__(self):
        self._snapshot_data = deepcopy(self.storage._data)
        self._snapshot_history = deepcopy(self.storage._history)
        self._snapshot_counter = self.storage._counter.copy()
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self.storage._data = self._snapshot_data
            self.storage._history = self._snapshot_history
            self.storage._counter = self._snapshot_counter
        return False
