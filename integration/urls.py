from django.urls import include, path
from rest_framework import routers

from integration.views import (
    IntegrationViewSet,
    UserIntegrationViewSet,
    IntegrationEventViewSet,
)
from integration.views.oauth import OauthViewset

router = routers.DefaultRouter(trailing_slash=False)
router.register("oauth", OauthViewset, basename="oauth")
router.register("user_integration", UserIntegrationViewSet, basename="user_integration")
router.register(
    "integration_event", IntegrationEventViewSet, basename="integration_event"
)
router.register("", IntegrationViewSet, basename="integration")

urlpatterns = [
    path("", include(router.urls)),
]
