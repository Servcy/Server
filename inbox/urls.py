from django.urls import include, path
from rest_framework import routers

from inbox.views import InboxViewSet
from inbox.views.assisstant import AssisstantViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("", InboxViewSet, basename="inbox")
router.register("assisstant", AssisstantViewSet, basename="assisstant")

urlpatterns = [
    path("", include(router.urls)),
]
