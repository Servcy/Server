from django.urls import include, path
from rest_framework import routers

from .views import DocumentViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("", DocumentViewSet, basename="document")

urlpatterns = [
    path("", include(router.urls)),
]
