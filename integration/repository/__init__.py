import json
from base64 import b64decode, b64encode

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import IntegrityError

from integration.models import Integration, UserIntegration


class IntegrationRepository:
    @classmethod
    def create_user_integration(
        self, integration_id: int, user_id: int, meta_data: dict, account_id: str
    ) -> UserIntegration:
        base_64_encoded_meta_data = {
            key: b64encode(str(value).encode()).decode()
            for key, value in meta_data.items()
        }
        encrypted_meta_data = (
            Fernet(settings.FERNET_KEY)
            .encrypt(str(base_64_encoded_meta_data).encode())
            .decode()
        )
        try:
            user_integration = UserIntegration.objects.create(
                integration_id=integration_id,
                user_id=user_id,
                meta_data=encrypted_meta_data,
                account_id=account_id,
            )
            return user_integration
        except IntegrityError:
            user_integration = UserIntegration.objects.get(
                integration_id=integration_id,
                user_id=user_id,
                account_id=account_id,
            )
            user_integration.meta_data = encrypted_meta_data
            user_integration.save()
            return user_integration
        except Exception as err:
            raise err

    @classmethod
    def get_integration(self, filters: dict) -> Integration:
        integration = Integration.objects.get(**filters)
        return integration

    @classmethod
    def get_user_integrations(self, filters: dict) -> list[UserIntegration]:
        integrations = UserIntegration.objects.filter(**filters).values(
            "id", "meta_data", "account_id", "integration_id", "user_id"
        )
        for integration in integrations:
            integration["meta_data"] = self.decrypt_meta_data(
                meta_data=integration["meta_data"]
            )
        return integrations

    @staticmethod
    def decrypt_meta_data(meta_data):
        fernet = Fernet(settings.FERNET_KEY)
        decrypted_meta_data = fernet.decrypt(token=meta_data).decode()
        decrypted_meta_data = json.loads(decrypted_meta_data.replace("'", '"'))
        meta_data = {
            str(key): b64decode(str(value).encode()).decode()
            for key, value in dict(decrypted_meta_data).items()
        }
        return meta_data
