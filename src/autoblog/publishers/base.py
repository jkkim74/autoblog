"""Publisher interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Post


class Publisher(ABC):
    """Delivers a Post to some destination, returning a human-readable location."""

    @abstractmethod
    def publish(self, post: Post) -> str:
        """Publish the post; return a string describing where it landed."""
        raise NotImplementedError
