from integration.models import DisabledUserIntegrationEvent, IntegrationEvent


class IntegrationEventRepository:
    @staticmethod
    def create(**kwargs):
        return IntegrationEvent.objects.create(**kwargs)

    @staticmethod
    def filter(**kwargs):
        return IntegrationEvent.objects.filter(**kwargs)


class DisabledUserIntegrationEventRepository:
    @staticmethod
    def get_or_create(**kwargs):
        return DisabledUserIntegrationEvent.objects.get_or_create(**kwargs)

    @staticmethod
    def filter(**kwargs):
        return DisabledUserIntegrationEvent.objects.filter(**kwargs)

    @staticmethod
    def create(**kwargs):
        return DisabledUserIntegrationEvent.objects.create(**kwargs)

    @staticmethod
    def get_disabled_user_integration_events(
        user_integration_id: int,
    ) -> dict[str, list[str]]:
        """
        Fetch all disabled user integration events.
        """
        return {
            event["integration_event__name"]: event["actions"]
            for event in DisabledUserIntegrationEvent.objects.filter(
                user_integration_id=user_integration_id
            ).values("integration_event__name", "actions")
        }
