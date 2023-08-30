from rest_framework.viewsets import GenericViewSet, mixins

from integration.serializers import IntegrationSerializer, UserIntegrationSerializer


class IntegrationViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = IntegrationSerializer
    queryset = IntegrationSerializer.Meta.model.objects.all()
    ordering_fields = ["name"]

    def get_queryset(self):
        return super().get_queryset().prefetch_related("user_integrations")


class UserIntegrationViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
    mixins.UpdateModelMixin,
):
    serializer_class = UserIntegrationSerializer
    queryset = UserIntegrationSerializer.Meta.model.objects.all()

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                user_id=self.request.user.id,
                integration__name=self.request.GET.get("integration_name"),
            )
        )
