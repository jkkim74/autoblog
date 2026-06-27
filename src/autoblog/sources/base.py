"""Source interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import SourceItem


class Source(ABC):
    """A provider of raw material. Implementations fetch and return SourceItems."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def fetch(self) -> list[SourceItem]:
        """Return the latest items from this source (most recent first)."""
        raise NotImplementedError
