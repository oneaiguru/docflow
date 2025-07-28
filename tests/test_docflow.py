import pytest
from py_docflow import DocTypesRegistry, Docflow, User, DocumentVersioned


def load_types():
    registry = DocTypesRegistry()
    doc_a = registry.load('examples/doc_type_a.json')
    doc_b = registry.load('examples/doc_type_b.json')
    sample = registry.load('examples/sample_doctype.json')
    doc_file = registry.load('examples/doc_file.json')
    return registry, doc_a, doc_b, sample, doc_file


def test_create_and_history():
    registry, doc_a, _, _, _ = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    doc = flow.create(doc_a, {'text': 'hello'}, admin)
    assert doc.id == 1
    assert doc._state_name() == 'NEW'
    hist = flow.storage.history(doc_a.name, doc.id)
    assert len(hist) == 1
    assert hist[0].action == 'CREATE'
    assert hist[0].rev == 0
    assert hist[0].params == {'text': 'hello'}
    assert hist[0].changes['text'] == (None, 'hello')


def test_update_and_revision():
    registry, _, _, sample, _ = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    doc = flow.create(sample, {'text': 'hello', 'filename': 'a.txt'}, admin)
    flow.update(doc, {'text': 'changed'}, admin)
    assert doc.rev == 1
    assert doc._state_name() == 'UPDATED'
    hist = flow.storage.history(sample.name, doc.id)
    assert [h.action for h in hist] == ['CREATE', 'UPDATE']
    assert hist[1].params == {'text': 'changed'}
    assert hist[1].changes['text'] == ('hello', 'changed')


def test_link_action_and_state():
    registry, doc_a, doc_b, _, _ = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    a = flow.create(doc_a, {'text': 'a'}, admin)
    b = flow.create(doc_b, {'text': 'b'}, admin)
    flow.action(a, 'LINK', admin, {'doc_type': 'DocB', 'doc_id': b.id})
    assert a.links['DocB'] == b.id
    assert a._state_name() == 'LINKED'
    hist = flow.storage.history(doc_a.name, a.id)
    assert [h.action for h in hist] == ['CREATE', 'LINK']
    assert hist[1].params == {'doc_type': 'DocB', 'doc_id': b.id}
    assert 'links' in hist[1].changes


def test_rights_enforced_delete():
    registry, doc_a, _, _, _ = load_types()
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
    assert hist[-1].params == {'delete': True}


def test_action_chain_success():
    registry, doc_a, doc_b, _, _ = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    a = flow.create(doc_a, {'text': 'a'}, admin)
    b = flow.create(doc_b, {'text': 'b'}, admin)
    flow.action(a, 'TRIGGER_MARK', admin, {
        'call': {'doc_type': 'DocB', 'doc_id': b.id, 'action': 'MARK'}
    })
    stored_b = flow.storage.get(doc_b.name, b.id)
    assert stored_b._state_name() == 'MARKED'
    hist = flow.storage.history(doc_b.name, b.id)
    assert hist[-1].action == 'MARK'
    assert hist[-1].params == {}
    assert hist[-1].changes['_state'][1] == 'MARKED'


def test_action_chain_rollback_on_repeat():
    registry, doc_a, doc_b, _, _ = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    a = flow.create(doc_a, {'text': 'a'}, admin)
    b = flow.create(doc_b, {'text': 'b'}, admin)
    with pytest.raises(RuntimeError):
        flow.action(a, 'TRIGGER_MARK', admin, {
            'call': {
                'doc_type': 'DocB',
                'doc_id': b.id,
                'action': 'MARK',
                'params': {
                    'call': {
                        'doc_type': 'DocA',
                        'doc_id': a.id,
                        'action': 'TRIGGER_MARK'
                    }
                }
            }
        })
    stored_a = flow.storage.get(doc_a.name, a.id)
    stored_b = flow.storage.get(doc_b.name, b.id)
    assert stored_a._state_name() == 'NEW'
    assert stored_b._state_name() == 'NEW'
    assert len(flow.storage.history(doc_b.name, b.id)) == 1


def test_persist_and_fetch_file():
    registry, _, _, _, doc_file = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    f = flow.persist_file(doc_file, 'note.txt', b'hey', admin, text='desc')
    assert f.id == 1
    assert flow.get_file(f, admin) == b'hey'


def test_recover_document():
    registry, doc_a, _, _, _ = load_types()
    flow = Docflow()
    admin = User('alice', ['admin'])
    a = flow.create(doc_a, {'text': 'hi'}, admin)
    flow.delete(a, admin)
    assert a.deleted is True
    flow.recover(a, admin)
    assert a.deleted is False
    hist = flow.storage.history(doc_a.name, a.id)
    assert hist[-1].action == 'RECOVER'
    assert hist[-1].params == {'delete': False}
