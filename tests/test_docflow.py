import pytest
from py_docflow import DocTypesRegistry, Docflow, User, DocumentVersioned


def load_types():
    registry = DocTypesRegistry()
    doc_a = registry.load('examples/doc_type_a.json')
    doc_b = registry.load('examples/doc_type_b.json')
    sample = registry.load('examples/sample_doctype.json')
    return registry, doc_a, doc_b, sample


def test_create_and_history():
    registry, doc_a, _, _ = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    doc = flow.create(doc_a, {'text': 'hello'}, admin)
    assert doc.id == 1
    assert doc._state_name() == 'NEW'
    hist = flow.storage.history(doc_a.name, doc.id)
    assert len(hist) == 1
    assert hist[0].action == 'CREATE'
    assert hist[0].rev == 0


def test_update_and_revision():
    registry, _, _, sample = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    doc = flow.create(sample, {'text': 'hello', 'filename': 'a.txt'}, admin)
    flow.update(doc, {'text': 'changed'}, admin)
    assert doc.rev == 1
    assert doc._state_name() == 'UPDATED'
    hist = flow.storage.history(sample.name, doc.id)
    assert [h.action for h in hist] == ['CREATE', 'UPDATE']


def test_link_action_and_state():
    registry, doc_a, doc_b, _ = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    a = flow.create(doc_a, {'text': 'a'}, admin)
    b = flow.create(doc_b, {'text': 'b'}, admin)
    flow.action(a, 'LINK', admin, {'doc_type': 'DocB', 'doc_id': b.id})
    assert a.links['DocB'] == b.id
    assert a._state_name() == 'LINKED'
    hist = flow.storage.history(doc_a.name, a.id)
    assert [h.action for h in hist] == ['CREATE', 'LINK']


def test_rights_enforced_delete():
    registry, doc_a, _, _ = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    guest = User('bob', ['guest'])
    a = flow.create(doc_a, {'text': 'hello'}, admin)
    with pytest.raises(PermissionError):
        flow.delete(a, guest)
    flow.delete(a, admin)
    assert a.deleted is True
    hist = flow.storage.history(doc_a.name, a.id)
    assert hist[-1].action == 'DELETE'
