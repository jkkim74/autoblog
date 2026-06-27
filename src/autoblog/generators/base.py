"""Generator interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Post, SourceItem


class Generator(ABC):
    """Turns one or more source items into a finished Post."""

    @abstractmethod
    def generate(self, items: list[SourceItem]) -> Post:
        """Produce a single Post from the given source items."""
        raise NotImplementedError
