from django.urls import include, path
from rest_framework import routers

from integration.views import IntegrationViewSet
from integration.views.figma import FigmaViewset
from integration.views.oauth import OauthViewset

router = routers.DefaultRouter(trailing_slash=False)
router.register("oauth", OauthViewset, basename="oauth")
router.register("figma", FigmaViewset, basename="figma")
router.register("", IntegrationViewSet, basename="integration")

urlpatterns = [
    path("", include(router.urls)),
]
