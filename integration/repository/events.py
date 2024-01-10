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
