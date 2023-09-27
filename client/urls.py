from django.urls import include, path
from rest_framework import routers

from client.views import ClientViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("", ClientViewSet, basename="client")

urlpatterns = [
    path("", include(router.urls)),
]
