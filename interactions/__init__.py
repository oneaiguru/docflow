"""Пакет с упрощённой реализацией сервиса взаимодействий."""

from .service import (
    InteractionService,
    Interaction,
    IN_PROGRESS,
    COMPLETED,
    FAILED,
    CANCELLED,
)

__all__ = [
    "InteractionService",
    "Interaction",
    "IN_PROGRESS",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
]
