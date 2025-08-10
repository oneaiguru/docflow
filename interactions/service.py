"""Simplified interaction service with transactional support.

This module provides an in-memory port of the `interactions` service from the
`AZ_trasko` project.  The original service works with PostgreSQL and publishes
events to a message bus.  Here we keep only the core logic of creating,
updating and sequentially processing interaction records.  In addition the
module implements a very light‑weight transaction mechanism allowing to group
several changes and commit or rollback them atomically.

The goal of the port is to demonstrate behaviour of the original service while
remaining completely self contained and runnable in tests without external
dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from copy import deepcopy

# interaction states ---------------------------------------------------------
IN_PROGRESS = "in_progress"
COMPLETED = "completed"
FAILED = "failed"
CANCELLED = "cancelled"


@dataclass
class Interaction:
    """Dataclass describing a single interaction entry."""

    id: int
    from_service: str
    to_service: str
    action: str
    parent_id: Optional[int] = None
    name: Optional[str] = None
    message_id: Optional[str] = None
    inner_action: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)
    state: str = IN_PROGRESS
    created: datetime = field(default_factory=datetime.utcnow)
    modified: datetime = field(default_factory=datetime.utcnow)
    next_processing: Optional[datetime] = field(default_factory=datetime.utcnow)


# basic service --------------------------------------------------------------
class _BaseService:
    """Internal base class shared by the main service and transactions."""

    def __init__(self) -> None:
        self._interactions: Dict[int, Interaction] = {}
        self._next_id = 1

    # id generation -----------------------------------------------------
    def _generate_id(self) -> int:
        nid = self._next_id
        self._next_id += 1
        return nid

    # CRUD methods ------------------------------------------------------
    def create(
        self,
        *,
        from_service: str,
        to_service: str,
        action: str,
        context: Optional[str] = None,
        parent_id: Optional[int] = None,
        name: Optional[str] = None,
        singleton: bool = False,
        inner_action: Optional[str] = None,
        message_id: Optional[str] = None,
        completed: bool = False,
        error: Any = None,
        cancelled: bool = False,
        process_at: Optional[datetime] = None,
        process_in: Optional[int] = None,
        wait: bool = False,
        **options: Any,
    ) -> Optional[Interaction]:
        """Create new interaction.

        The behaviour mirrors the original JS implementation but operates on an
        in-memory store.  When ``singleton`` is true and there already exists an
        unfinished interaction with the same ``to_service`` and ``action`` a new
        one is not created and ``None`` is returned.
        """

        if singleton:
            for ia in self._interactions.values():
                if (
                    ia.to_service == to_service
                    and ia.action == action
                    and ia.state == IN_PROGRESS
                ):
                    return None

        if cancelled:
            completed = True

        is_error = error is not None
        if is_error:
            completed = True
            options = dict(options)
            options["error"] = str(error)

        now = datetime.utcnow()

        next_processing: Optional[datetime] = None
        if cancelled:
            next_processing = None
        elif process_at is not None:
            next_processing = process_at
        elif process_in is not None:
            next_processing = now + timedelta(milliseconds=process_in)
        elif wait:
            next_processing = None
        elif not completed:
            next_processing = now

        state = IN_PROGRESS
        if completed:
            if cancelled:
                state = CANCELLED
            elif is_error:
                state = FAILED
            else:
                state = COMPLETED

        interaction = Interaction(
            id=self._generate_id(),
            from_service=from_service,
            to_service=to_service,
            action=action,
            parent_id=parent_id,
            name=name,
            message_id=message_id,
            inner_action=inner_action,
            options=dict(options),
            state=state,
            created=now,
            modified=now,
            next_processing=next_processing,
        )

        self._interactions[interaction.id] = interaction

        if completed and parent_id and not cancelled:
            parent = self._interactions.get(parent_id)
            if parent and parent.state == IN_PROGRESS:
                parent.next_processing = now

        return interaction

    def get(self, id: int) -> Optional[Interaction]:
        return self._interactions.get(id)

    def get_children(
        self, parent_id: int, name: Optional[str] = None, limit: Optional[int] = None
    ) -> list[Interaction]:
        children = [
            ia
            for ia in self._interactions.values()
            if ia.parent_id == parent_id and (name is None or ia.name == name)
        ]
        children.sort(key=lambda ia: ia.modified, reverse=True)
        if limit is not None:
            children = children[:limit]
        return children

    def get_by_message_id(self, message_id: str) -> Optional[Interaction]:
        matches = [ia for ia in self._interactions.values() if ia.message_id == message_id]
        if not matches:
            return None
        matches.sort(key=lambda ia: ia.created)
        return matches[0]

    def update(
        self,
        interaction: Interaction,
        *,
        parent_id: Optional[int] = None,
        message_id: Optional[str] = None,
        completed: Optional[bool] = None,
        error: Any = None,
        cancelled: Optional[bool] = None,
        process_at: Optional[datetime] = None,
        process_in: Optional[int] = None,
        wait: Optional[bool] = None,
        **options: Any,
    ) -> Interaction:
        """Update existing interaction.

        Only the provided fields are changed.  Scheduling behaviour follows the
        rules of the original service: unless ``process_at`` or ``process_in`` is
        specified the interaction becomes unscheduled.
        """

        now = datetime.utcnow()

        if parent_id is not None:
            interaction.parent_id = parent_id
        if message_id is not None:
            interaction.message_id = message_id
        if options:
            interaction.options.update(options)

        if cancelled:
            completed = True
        is_error = error is not None
        if is_error:
            completed = True
            interaction.options["error"] = str(error)

        # state handling ------------------------------------------------
        if completed:
            if cancelled:
                interaction.state = CANCELLED
            elif is_error:
                interaction.state = FAILED
            else:
                interaction.state = COMPLETED
        else:
            interaction.state = IN_PROGRESS

        # scheduling ----------------------------------------------------
        if cancelled or completed:
            interaction.next_processing = None
        elif process_at is not None:
            interaction.next_processing = process_at
        elif process_in is not None:
            interaction.next_processing = now + timedelta(milliseconds=process_in)
        elif wait:
            interaction.next_processing = None
        else:
            interaction.next_processing = None

        interaction.modified = now
        self._interactions[interaction.id] = interaction

        if completed and interaction.parent_id and not cancelled:
            parent = self._interactions.get(interaction.parent_id)
            if parent and parent.state == IN_PROGRESS:
                parent.next_processing = now

        return interaction

    # processing -------------------------------------------------------
    def process(
        self,
        *,
        to_service: str,
        action: Optional[str] = None,
        processor: Callable[[Interaction], None],
        error_handler: Optional[Callable[[Exception, Interaction], None]] = None,
    ) -> None:
        """Process all available interactions for the specified service.

        The method iterates over scheduled interactions and sequentially calls
        ``processor`` for each one.  On success the interaction is marked as
        completed, on error the state becomes ``FAILED`` and ``error_handler`` is
        invoked if provided.
        """

        while True:
            now = datetime.utcnow()
            candidate: Optional[Interaction] = None
            for ia in self._interactions.values():
                if ia.to_service != to_service:
                    continue
                if action and ia.action != action:
                    continue
                if ia.state != IN_PROGRESS:
                    continue
                if ia.next_processing and ia.next_processing > now:
                    continue
                candidate = ia
                break

            if candidate is None:
                break

            try:
                processor(candidate)
                if candidate.state == IN_PROGRESS:
                    self.update(candidate, completed=True)
            except Exception as exc:  # pragma: no cover - to keep coverage stable
                self.update(candidate, error=exc)
                if error_handler:
                    error_handler(exc, candidate)


# public service ------------------------------------------------------------
class InteractionService(_BaseService):
    """Public entry point used by tests and external code."""

    def transaction(self) -> "Transaction":
        """Return a transaction object which can be used as context manager."""

        return Transaction(self)


class Transaction(_BaseService):
    """Very light‑weight in-memory transaction.

    All data modifying operations are executed against a copy of the parent
    service storage.  On commit the copy replaces the original storage.  On
    rollback all modifications are discarded.  The class implements context
    manager protocol so it can be used with ``with`` statement.
    """

    def __init__(self, parent: InteractionService) -> None:
        super().__init__()
        self._parent = parent
        self._interactions = deepcopy(parent._interactions)
        self._next_id = parent._next_id

    # context manager --------------------------------------------------
    def __enter__(self) -> "Transaction":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    # commit / rollback ------------------------------------------------
    def commit(self) -> None:
        self._parent._interactions = self._interactions
        self._parent._next_id = self._next_id

    def rollback(self) -> None:
        # simply drop the local changes
        pass


__all__ = [
    "InteractionService",
    "Interaction",
    "IN_PROGRESS",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
]

