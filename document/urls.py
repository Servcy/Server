from django.urls import include, path
from rest_framework import routers

from .views import DocumentViewSet, UnsplashEndpoint

router = routers.DefaultRouter(trailing_slash=False)
router.register("", DocumentViewSet, basename="document")

urlpatterns = [
    path("", include(router.urls)),
    path("unsplash", UnsplashEndpoint.as_view(), name="unsplash"),
]
