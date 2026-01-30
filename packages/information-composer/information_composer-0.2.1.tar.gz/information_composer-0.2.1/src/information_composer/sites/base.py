"""Base site information collector implementation.
This module provides the base class for site-specific information collectors,
defining the common interface and shared functionality.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseSiteCollector(ABC):
    """Base class for site-specific information collectors.
    This abstract base class defines the common interface that all site-specific
    collectors must implement. It provides a foundation for consistent behavior
    across different information collection modules.
    Attributes:
        name: The name of the collector (derived from class name)
        config: Optional configuration dictionary for the collector
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the base site collector.
        Args:
            config: Optional configuration dictionary for the collector
        """
        self.name = self.__class__.__name__
        self.config = config or {}

    @abstractmethod
    def collect(self) -> Any:
        """Implement the information collection logic.
        This method should be implemented by subclasses to define the specific
        information collection process for the target site.
        Returns:
            The collected information in a format specific to the implementation
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement collect method"
        )

    @abstractmethod
    def compose(self, data: Any) -> Any:
        """Implement the information composition logic.
        This method should be implemented by subclasses to define how collected
        information is processed and composed into the final output format.
        Args:
            data: The raw collected data to be composed
        Returns:
            The composed information in the desired output format
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement compose method"
        )

    def validate_config(self, required_keys: list[str]) -> bool:
        """Validate that the configuration contains required keys.
        Args:
            required_keys: List of required configuration keys
        Returns:
            True if all required keys are present, False otherwise
        """
        return all(key in self.config for key in required_keys)

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with optional default.
        Args:
            key: The configuration key to retrieve
            default: Default value if key is not found
        Returns:
            The configuration value or default
        """
        return self.config.get(key, default)
