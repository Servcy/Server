import datetime
import json
from base64 import b64decode, b64encode

from cryptography.fernet import Fernet
from django.conf import settings

from integration.models import (
    DisabledUserIntegrationEvent,
    Integration,
    UserIntegration,
)


class IntegrationRepository:
    @classmethod
    def create_user_integration(
        self,
        integration_id: int,
        user_id: int,
        meta_data: dict,
        account_id: str,
        account_display_name: str = "",
        configuration: list | dict = None,
    ) -> UserIntegration:
        defaults = {
            "meta_data": IntegrationRepository.encrypt_meta_data(meta_data),
            "account_display_name": account_display_name,
            "is_revoked": False,
        }
        if configuration is not None:
            defaults["configuration"] = configuration
        user_integration, _ = UserIntegration.objects.update_or_create(
            integration_id=integration_id,
            user_id=user_id,
            account_id=account_id,
            defaults=defaults,
        )
        return user_integration

    @classmethod
    def get_integration(self, filters: dict) -> Integration:
        integration = Integration.objects.get(**filters)
        return integration

    @classmethod
    def get_user_integration(self, filters: dict) -> UserIntegration:
        user_integration = UserIntegration.objects.get(**filters, is_revoked=False)
        return user_integration

    @classmethod
    def get_user_integrations(
        self, filters: dict, first=False
    ) -> list[UserIntegration] | UserIntegration:
        integrations = UserIntegration.objects.filter(
            **filters, is_revoked=False
        ).values(
            "id",
            "meta_data",
            "account_id",
            "integration_id",
            "integration__name",
            "user_id",
            "configuration",
        )
        for integration in integrations:
            integration["meta_data"] = self.decrypt_meta_data(
                meta_data=integration["meta_data"]
            )
        if not first:
            return integrations
        return integrations[0] if integrations else None

    @staticmethod
    def decrypt_meta_data(meta_data: str) -> dict:
        fernet = Fernet(settings.FERNET_KEY)
        decrypted_meta_data = fernet.decrypt(token=meta_data).decode()
        base_64_decoded_meta_data = {
            key: json.loads(b64decode(value).decode())
            for key, value in json.loads(decrypted_meta_data).items()
        }
        return base_64_decoded_meta_data

    @staticmethod
    def encrypt_meta_data(meta_data: dict) -> str:
        base_64_encoded_meta_data = {
            key: b64encode(str(json.dumps(value)).encode()).decode()
            for key, value in meta_data.items()
        }
        encrypted_meta_data = (
            Fernet(settings.FERNET_KEY)
            .encrypt(str(json.dumps(base_64_encoded_meta_data)).encode())
            .decode()
        )
        return encrypted_meta_data

    @staticmethod
    def update_integraion_meta_data(user_integration_id: int, meta_data: dict):
        UserIntegration.objects.filter(id=user_integration_id, is_revoked=False).update(
            meta_data=IntegrationRepository.encrypt_meta_data(meta_data=meta_data),
            updated_at=datetime.datetime.now(),
        )

    @staticmethod
    def update_integraion_configuration(user_integration_id: int, configuration: dict):
        UserIntegration.objects.filter(id=user_integration_id, is_revoked=False).update(
            updated_at=datetime.datetime.now(), configuration=configuration
        )

    @staticmethod
    def fetch_all_user_integrations() -> list[UserIntegration]:
        """
        Fetch all user integrations.
        """
        return UserIntegration.objects.filter(is_revoked=False).all()

    @staticmethod
    def revoke_user_integrations(user_integrations: list[int] | int):
        """
        Revoke user integrations.
        """
        if isinstance(user_integrations, list):
            UserIntegration.objects.filter(id__in=user_integrations).update(
                updated_at=datetime.datetime.now(), is_revoked=True
            )
        elif isinstance(user_integrations, int):
            UserIntegration.objects.filter(id=user_integrations).update(
                is_revoked=True,
                updated_at=datetime.datetime.now(),
            )
