"""High level document flow API inspired by AZ_DSCommon."""

from typing import Any, Dict, Optional, Set, Tuple, Callable
from copy import deepcopy
from .document import DocumentPersistent, DocumentVersioned, DocumentFile
from .doctypes import DocType
from .rights import RolesRegistry
from .storage import InMemoryStorage, Transaction
from .user import User


class Docflow:
    """Simplified document flow engine.

    This class mimics the behavior of the Java `Docflow` facade from
    **AZ_DSCommon**. Documents are stored in an in-memory storage and each
    operation returns the updated document instance.
    """

    def __init__(self, storage: Optional[InMemoryStorage] = None, roles: Optional[RolesRegistry] = None):
        self.storage = storage or InMemoryStorage()
        self.actions: Dict[str, Callable[[DocumentPersistent, Dict[str, Any], User], None]] = {}
        self.roles = roles or RolesRegistry()

    def register_action(
        self, name: str, func: Callable[[DocumentPersistent, Dict[str, Any], User], None]
    ):
        """Register a custom action callable."""
        self.actions[name] = func

    def _snapshot(self, doc: DocumentPersistent) -> Dict[str, Any]:
        return {k: deepcopy(v) for k, v in doc.__dict__.items() if k != "_doc_type"}

    def _diff(self, before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Tuple[Any, Any]]:
        changes = {}
        for key in before.keys() | after.keys():
            if before.get(key) != after.get(key):
                changes[key] = (before.get(key), after.get(key))
        return changes

    def _check_rights(self, doc_type: DocType, action: str, user: User):
        """Validate that ``user`` may perform ``action`` on ``doc_type``."""
        mask = doc_type.rights_bits.get(action.lower())
        if mask is not None and doc_type.rights_roles is self.roles:
            user_mask = self.roles.mask(user.roles)
            if mask.and_(user_mask).is_empty():
                raise PermissionError(
                    f"User {user.name} lacks rights for {action} on {doc_type.name}"
                )
            return

        rights = doc_type.rights.get(action.lower())
        if rights and not any(rights.get(role) for role in user.roles):
            raise PermissionError(
                f"User {user.name} lacks rights for {action} on {doc_type.name}"
            )

    def create(self, doc_type: DocType, data: Dict[str, Any], user: User) -> DocumentPersistent:
        """Create a new document instance and store it."""
        self._check_rights(doc_type, "create", user)
        doc = DocumentVersioned()  # keep revision history similar to Java code
        doc._doc_type = doc_type
        if doc_type.states:
            doc._state = doc_type.states[0]
        before = self._snapshot(doc)
        for field, value in data.items():
            setattr(doc, field, value)
        self.storage.insert(doc_type.name, doc)
        if isinstance(doc, DocumentVersioned):
            changes = self._diff(before, self._snapshot(doc))
            self.storage.add_history(doc_type.name, doc, action="CREATE", params=data, changes=changes)
        return doc

    def persist_file(
        self,
        doc_type: DocType,
        filename: str,
        data: bytes,
        user: User,
        text: str = "",
    ) -> DocumentFile:
        """Save a file document with raw bytes."""
        self._check_rights(doc_type, "create", user)
        doc = DocumentFile(filename=filename, data=data, text=text)
        doc._doc_type = doc_type
        if doc_type.states:
            doc._state = doc_type.states[0]
        self.storage.insert(doc_type.name, doc)
        return doc

    def get_file(self, doc: DocumentFile, user: User) -> bytes:
        """Retrieve file contents from storage."""
        self._check_rights(doc._docType(), "read", user)
        return doc.data

    def update(self, doc: DocumentPersistent, data: Dict[str, Any], user: User) -> DocumentPersistent:
        """Apply field updates to an existing document."""
        self._check_rights(doc._docType(), "update", user)
        before = self._snapshot(doc)
        for field, value in data.items():
            setattr(doc, field, value)
        if isinstance(doc, DocumentVersioned):
            doc.touch()
            if "UPDATED" in doc._docType().states:
                doc._state = "UPDATED"
        self.storage.update(doc._docType().name, doc)
        if isinstance(doc, DocumentVersioned):
            changes = self._diff(before, self._snapshot(doc))
            self.storage.add_history(doc._docType().name, doc, action="UPDATE", params=data, changes=changes)
        return doc

    def delete(self, doc: DocumentVersioned, user: User, delete: bool = True) -> DocumentVersioned:
        """Mark a versioned document as deleted or recovered."""
        self._check_rights(doc._docType(), "delete", user)
        before = self._snapshot(doc)
        doc.deleted = delete
        if delete:
            doc.touch()
        self.storage.update(doc._docType().name, doc)
        changes = self._diff(before, self._snapshot(doc))
        self.storage.add_history(
            doc._docType().name,
            doc,
            action="DELETE" if delete else "RECOVER",
            params={"delete": delete},
            changes=changes,
        )
        return doc

    def recover(self, doc: DocumentVersioned, user: User) -> DocumentVersioned:
        """Recover a previously deleted document."""
        return self.delete(doc, user, delete=False)

    def action(
        self,
        doc: DocumentPersistent,
        action_name: str,
        user: User,
        params: Optional[Dict[str, Any]] = None,
        _chain: Optional[Set[Tuple[str, int, str]]] = None,
    ):
        """Execute a custom action possibly spanning multiple documents.

        Actions may trigger other actions on related documents by passing a
        ``call`` dictionary inside ``params``. All actions invoked as part of the
        same request are executed atomically using a basic in-memory transaction.
        Repeated execution of the same action on the same document within one
        chain raises ``RuntimeError``.
        """

        params = params or {}
        if _chain is None:
            _chain = set()
            with Transaction(self.storage):
                return self.action(doc, action_name, user, params, _chain)

        key = (doc._docType().name, doc.id, action_name)
        if key in _chain:
            raise RuntimeError("Action already executed in this chain")
        _chain.add(key)

        self._check_rights(doc._docType(), action_name, user)

        before = self._snapshot(doc)
        if action_name == "LINK" and isinstance(doc, DocumentVersioned):
            target_type = params.get("doc_type")
            target_id = params.get("doc_id")
            if target_type and target_id is not None:
                doc.links[target_type] = target_id
                if "LINKED" in doc._docType().states:
                    doc._state = "LINKED"
        elif action_name == "MARK" and isinstance(doc, DocumentVersioned):
            if "MARKED" in doc._docType().states:
                doc._state = "MARKED"
        elif action_name in self.actions:
            self.actions[action_name](doc, params, user)

        if isinstance(doc, DocumentVersioned):
            doc.touch()
        self.storage.update(doc._docType().name, doc)
        if isinstance(doc, DocumentVersioned):
            changes = self._diff(before, self._snapshot(doc))
            self.storage.add_history(
                doc._docType().name,
                doc,
                action=action_name,
                params=params,
                changes=changes,
            )

        if "call" in params:
            info = params["call"]
            target = self.storage.get(info["doc_type"], info["doc_id"])
            if not target:
                raise ValueError("Target document not found")
            self.action(target, info["action"], user, info.get("params"), _chain)

        return {
            "doc": doc._fullId(),
            "action": action_name,
            "params": params,
        }
