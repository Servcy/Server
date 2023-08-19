import json
from base64 import b64decode, b64encode

from cryptography.fernet import Fernet
from django.conf import settings
from django.db import IntegrityError

from integration.models import Integration, IntegrationUser


class IntegrationRepository:
    @classmethod
    def create_integration_user(
        self, integration_id: int, user_id: int, meta_data: dict, account_id: str
    ) -> IntegrationUser:
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
            integration_user = IntegrationUser.objects.create(
                integration_id=integration_id,
                user_id=user_id,
                meta_data=encrypted_meta_data,
                account_id=account_id,
            )
            return integration_user
        except IntegrityError:
            integration_user = IntegrationUser.objects.get(
                integration_id=integration_id,
                user_id=user_id,
                account_id=account_id,
            )
            integration_user.meta_data = encrypted_meta_data
            integration_user.save()
            return integration_user
        except Exception as err:
            raise err

    @classmethod
    def get_integration(self, filters: dict) -> Integration:
        integration = Integration.objects.get(**filters)
        return integration

    @classmethod
    def get_integration_user(self, filters: dict) -> list[IntegrationUser]:
        integrations = IntegrationUser.objects.filter(**filters).values(
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
