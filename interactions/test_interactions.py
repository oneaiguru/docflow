import pytest
from datetime import datetime, timedelta

from .service import (
    InteractionService,
    IN_PROGRESS,
    COMPLETED,
    FAILED,
)


def test_create_and_get():
    svc = InteractionService()
    ia = svc.create(from_service="a", to_service="b", action="x")
    fetched = svc.get(ia.id)
    assert fetched is not None
    assert fetched.id == ia.id
    assert fetched.state == IN_PROGRESS
    assert fetched.next_processing is not None


def test_get_children():
    svc = InteractionService()
    parent = svc.create(from_service="a", to_service="b", action="p")
    first = svc.create(
        from_service="a",
        to_service="b",
        action="c",
        parent_id=parent.id,
        name="child",
    )
    second = svc.create(
        from_service="a",
        to_service="b",
        action="c",
        parent_id=parent.id,
        name="child",
    )
    children = svc.get_children(parent.id, name="child", limit=1)
    assert len(children) == 1
    assert children[0].id == second.id


def test_get_by_message_id():
    svc = InteractionService()
    svc.create(from_service="a", to_service="b", action="x", message_id="m1")
    svc.create(from_service="a", to_service="b", action="x", message_id="m2")
    ia = svc.get_by_message_id("m1")
    assert ia is not None
    assert ia.message_id == "m1"


def test_process_success_and_error():
    svc = InteractionService()
    ok = svc.create(from_service="a", to_service="b", action="x")
    fail = svc.create(from_service="a", to_service="b", action="x")

    def processor(ia):
        if ia.id == fail.id:
            raise RuntimeError("boom")
        ia.options["done"] = True

    errors = []

    def err_handler(exc, ia):
        errors.append((ia.id, str(exc)))

    svc.process(to_service="b", action="x", processor=processor, error_handler=err_handler)

    ok_ia = svc.get(ok.id)
    fail_ia = svc.get(fail.id)
    assert ok_ia.state == COMPLETED
    assert ok_ia.options["done"] is True
    assert fail_ia.state == FAILED
    assert fail_ia.options["error"] == "boom"
    assert errors == [(fail.id, "boom")]


def test_update_and_parent_activation():
    svc = InteractionService()
    parent = svc.create(from_service="a", to_service="b", action="p", wait=True)
    child = svc.create(
        from_service="a",
        to_service="b",
        action="c",
        parent_id=parent.id,
    )

    # schedule child to run later and mark as completed
    svc.update(child, completed=True)

    updated_parent = svc.get(parent.id)
    assert updated_parent.next_processing is not None


def test_transactions_commit_and_rollback():
    svc = InteractionService()

    try:
        with svc.transaction() as tx:
            tx.create(from_service="a", to_service="b", action="x")
            raise RuntimeError("oops")
    except RuntimeError:
        pass

    # nothing committed
    assert svc.get(1) is None

    with svc.transaction() as tx:
        ia = tx.create(from_service="a", to_service="b", action="y")
        tx.update(ia, completed=True)

    fetched = svc.get(ia.id)
    assert fetched.state == COMPLETED
