from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """Defines a unified interface for all adapters."""

    @abstractmethod
    def invoke(self, **kwargs):
        """Executes the adapter and returns output."""
        pass
