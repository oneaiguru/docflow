"""High level document flow API inspired by AZ_DSCommon."""

from typing import Any, Dict, Optional
from .document import DocumentPersistent, DocumentVersioned
from .doctypes import DocType
from .storage import InMemoryStorage
from .user import User


class Docflow:
    """Simplified document flow engine.

    This class mimics the behavior of the Java `Docflow` facade from
    **AZ_DSCommon**. Documents are stored in an in-memory storage and each
    operation returns the updated document instance.
    """

    def __init__(self, storage: Optional[InMemoryStorage] = None):
        self.storage = storage or InMemoryStorage()

    def _check_rights(self, doc_type: DocType, action: str, user: User):
        rights = doc_type.rights.get(action.lower())
        if not rights:
            return
        if not any(rights.get(role) for role in user.roles):
            raise PermissionError(f"User {user.name} lacks rights for {action} on {doc_type.name}")

    def create(self, doc_type: DocType, data: Dict[str, Any], user: User) -> DocumentPersistent:
        """Create a new document instance and store it."""
        self._check_rights(doc_type, "create", user)
        doc = DocumentVersioned()  # keep revision history similar to Java code
        doc._doc_type = doc_type
        for field, value in data.items():
            setattr(doc, field, value)
        if doc_type.states:
            doc._state = doc_type.states[0]
        self.storage.insert(doc_type.name, doc)
        if isinstance(doc, DocumentVersioned):
            self.storage.add_history(doc_type.name, doc, action="CREATE")
        return doc

    def update(self, doc: DocumentPersistent, data: Dict[str, Any], user: User) -> DocumentPersistent:
        """Apply field updates to an existing document."""
        self._check_rights(doc._docType(), "update", user)
        for field, value in data.items():
            setattr(doc, field, value)
        if isinstance(doc, DocumentVersioned):
            doc.touch()
            if "UPDATED" in doc._docType().states:
                doc._state = "UPDATED"
        self.storage.update(doc._docType().name, doc)
        if isinstance(doc, DocumentVersioned):
            self.storage.add_history(doc._docType().name, doc, action="UPDATE")
        return doc

    def delete(self, doc: DocumentVersioned, user: User, delete: bool = True) -> DocumentVersioned:
        """Mark a versioned document as deleted or recovered."""
        self._check_rights(doc._docType(), "delete", user)
        doc.deleted = delete
        if delete:
            doc.touch()
        self.storage.update(doc._docType().name, doc)
        self.storage.add_history(doc._docType().name, doc, action="DELETE" if delete else "RECOVER")
        return doc

    def action(self, doc: DocumentPersistent, action_name: str, user: User, params: Optional[Dict[str, Any]] = None):
        """Execute a custom action on a document.

        In a full implementation this would trigger state transitions and
        permission checks defined by the DocType. Here we simply return a
        description of what would have been executed.
        """
        params = params or {}
        self._check_rights(doc._docType(), action_name, user)
        if action_name == "LINK" and isinstance(doc, DocumentVersioned):
            target_type = params.get("doc_type")
            target_id = params.get("doc_id")
            if target_type and target_id is not None:
                doc.links[target_type] = target_id
                doc.touch()
                if "LINKED" in doc._docType().states:
                    doc._state = "LINKED"
                self.storage.update(doc._docType().name, doc)
                self.storage.add_history(doc._docType().name, doc, action="LINK")
                return {"linked": f"{target_type}:{target_id}"}
        return {
            "doc": doc._fullId(),
            "action": action_name,
            "params": params,
        }
