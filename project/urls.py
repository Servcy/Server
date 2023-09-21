from django.urls import include, path
from rest_framework import routers

from project.views import ProjectViewSet

router = routers.DefaultRouter(trailing_slash=False)
router.register("", ProjectViewSet, basename="project")

urlpatterns = [
    path("", include(router.urls)),
]
