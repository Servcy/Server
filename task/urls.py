from django.urls import include, path
from rest_framework import routers

from task.views import TaskViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("", TaskViewSet, basename="task")

urlpatterns = [
    path("", include(router.urls)),
]
