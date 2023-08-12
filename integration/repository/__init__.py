from cryptography.fernet import Fernet
from django.conf import settings
from django.db import IntegrityError

from integration.models import Integration, IntegrationUser


class IntegrationRepository:
    def create_integration_user(
        self, integration_id: int, user_id: int, meta_data: dict, account_id: str
    ) -> IntegrationUser:
        encrypted_meta_data = Fernet(settings.FERNET_KEY).encrypt(
            str(meta_data).encode()
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

    def get_integration_from_name(self, name: str) -> Integration:
        integration = Integration.objects.get(name=name)
        return integration
