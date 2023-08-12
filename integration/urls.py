from django.urls import include, path
from rest_framework import routers

from integration.views import IntegrationViewSet, google

router = routers.DefaultRouter(trailing_slash=False)
router.register("google", google.GoogleViewSet, basename="google")
router.register("", IntegrationViewSet, basename="integration")

urlpatterns = [
    path("", include(router.urls)),
]
