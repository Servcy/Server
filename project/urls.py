from django.urls import include, path
from rest_framework import routers

from project.urls.cycle import urlpatterns as cycle_urls
from project.urls.estimate import urlpatterns as estimate_urls
from project.urls.external import urlpatterns as external_urls
from project.urls.issue import urlpatterns as issue_urls
from project.urls.module import urlpatterns as module_urls
from project.urls.page import urlpatterns as page_urls
from project.urls.project import urlpatterns as project_urls
from project.urls.search import urlpatterns as search_urls
from project.urls.state import urlpatterns as state_urls
from project.urls.views import urlpatterns as view_urls

urlpatterns = []

router = routers.DefaultRouter(trailing_slash=False)

urlpatterns = [
    path("", include(router.urls)),
    *cycle_urls,
    *estimate_urls,
    *external_urls,
    *issue_urls,
    *module_urls,
    *page_urls,
    *project_urls,
    *search_urls,
    *state_urls,
    *view_urls,
]
