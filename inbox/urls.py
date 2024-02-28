from django.urls import include, path
from rest_framework import routers

from inbox.views import InboxViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("", InboxViewSet, basename="inbox")

urlpatterns = [
    path("", include(router.urls)),
]
