from django.urls import include, path
from rest_framework import routers

from inbox.views import InboxViewSet
from inbox.views.webhook import WebHookViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("", InboxViewSet, basename="inbox")
router.register("webhook", WebHookViewSet, basename="webhook")

urlpatterns = [
    path("", include(router.urls)),
]
