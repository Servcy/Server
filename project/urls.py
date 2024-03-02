from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path("", include(router.urls)),
]
