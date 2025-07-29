"""Small demo script showing how to use the Python Docflow."""
from py_docflow import DocTypesRegistry, Docflow, User


def main():
    registry = DocTypesRegistry()
    doc_type_a = registry.load('examples/doc_type_a.json')
    doc_type_b = registry.load('examples/doc_type_b.json')
    file_type = registry.load('examples/doc_file.json')

    flow = Docflow(roles=registry.roles)
    admin = User("alice", ["admin"])
    a = flow.create(doc_type_a, {"text": "hello"}, admin)
    b = flow.create(doc_type_b, {"text": "world"}, admin)
    print("Created", a._fullId(), "and", b._fullId())

    flow.action(a, "LINK", admin, {"doc_type": "DocB", "doc_id": b.id})
    print("A links", a.links)

    flow.update(b, {"text": "changed"}, admin)
    print("B rev", b.rev)

    flow.action(a, "TRIGGER_MARK", admin, {"call": {"doc_type": "DocB", "doc_id": b.id, "action": "MARK"}})
    print("B state after mark", flow.storage.get("DocB", b.id)._state_name())

    history_a = flow.storage.history(a._docType().name, a.id)
    print("A history", [(h.action, h.rev) for h in history_a])

    history_b = flow.storage.history(b._docType().name, b.id)
    print("B history", [(h.action, h.rev) for h in history_b])

    file_doc = flow.persist_file(file_type, "note.txt", b"hello", admin)
    print("Saved file", file_doc._fullId())
    print("File content", flow.get_file(file_doc, admin))

    guest = User("bob", ["guest"])
    try:
        flow.delete(a, guest)
    except PermissionError as e:
        print("Guest delete denied:", e)
    flow.delete(a, admin)
    flow.recover(a, admin)
    print("Recovered", a._fullId(), "deleted?", a.deleted)


if __name__ == "__main__":
    main()
