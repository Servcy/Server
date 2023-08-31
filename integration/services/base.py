from abc import ABC, abstractmethod

from integration.models import UserIntegration


class BaseService(ABC):
    """
    Base class for integration services.
    """

    @abstractmethod
    def is_active(self, meta_data: dict) -> bool:
        """
        Check if the user's integration is active.

        Args:
        - meta_data: The user integration meta data.

        Returns:
        - bool: True if integration is active, False otherwise.
        """
        pass

    @abstractmethod
    def create_integration(self, user_id: int) -> UserIntegration:
        """
        Create integration for user.

        Args:
        - user_id: The user id.

        Returns:
        - UserIntegration: The user integration record.
        """
        pass

    @abstractmethod
    def _fetch_token(self, code: str):
        """
        Fetch access and/or refresh token from service.
        """
        pass
