"""Base classifier interface."""

from abc import ABC, abstractmethod
from typing import Optional

from lacuna.models.classification import Classification, ClassificationContext


class Classifier(ABC):
    """Abstract base class for all classifiers."""

    def __init__(self, priority: int = 50):
        """Initialize classifier.

        Args:
            priority: Priority for pipeline execution (lower = earlier)
        """
        self.priority = priority

    @abstractmethod
    def classify(
        self, query: str, context: Optional[ClassificationContext] = None
    ) -> Optional[Classification]:
        """Classify a query.

        Args:
            query: The query text to classify
            context: Optional context information

        Returns:
            Classification result if applicable, None if cannot classify
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get classifier name."""
        pass

    def can_classify(
        self, query: str, context: Optional[ClassificationContext] = None
    ) -> bool:
        """Check if this classifier can classify the given query.

        Args:
            query: The query text
            context: Optional context information

        Returns:
            True if classifier can handle this query
        """
        # Default: try to classify
        return True
