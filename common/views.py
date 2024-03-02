from django.urls import resolve
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from common.paginator import BasePaginator


class BaseViewSet(ModelViewSet, BasePaginator):
    """
    Base ViewSet for all the viewsets, this will handle:
    -  timezone conversion
    -  pagination
    -  dispatch
    -  queryset
    """

    model = None
    permission_classes = [
        IsAuthenticated,
    ]
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
    )
    filterset_fields = []
    search_fields = []

    def get_queryset(self):
        try:
            return self.model.objects.all()
        except Exception as e:
            raise APIException("Please check the view", status.HTTP_400_BAD_REQUEST)

    def dispatch(self, request, *args, **kwargs):
        try:
            response = super().dispatch(request, *args, **kwargs)
            return response
        except Exception as exc:
            response = self.handle_exception(exc)
            return exc

    @property
    def workspace_id(self):
        return self.kwargs.get("workspace_id", None)

    @property
    def project_id(self):
        project_id = self.kwargs.get("project_id", None)
        if project_id:
            return project_id
        if resolve(self.request.path_info).url_name == "project":
            return self.kwargs.get("pk", None)

    @property
    def fields(self):
        fields = [
            field for field in self.request.GET.get("fields", "").split(",") if field
        ]
        return fields if fields else None

    @property
    def expand(self):
        expand = [
            expand for expand in self.request.GET.get("expand", "").split(",") if expand
        ]
        return expand if expand else None


class BaseAPIView(APIView, BasePaginator):
    """
    Base APIView for all the views, this will handle:
    -  timezone conversion
    -  pagination
    -  dispatch
    -  queryset
    """

    permission_classes = [
        IsAuthenticated,
    ]
    filter_backends = (
        DjangoFilterBackend,
        SearchFilter,
    )
    filterset_fields = []
    search_fields = []

    def filter_queryset(self, queryset):
        for backend in list(self.filter_backends):
            queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def dispatch(self, request, *args, **kwargs):
        try:
            response = super().dispatch(request, *args, **kwargs)
            return response

        except Exception as exc:
            response = self.handle_exception(exc)
            return exc

    @property
    def workspace_id(self):
        return self.kwargs.get("workspace_id", None)

    @property
    def project_id(self):
        project_id = self.kwargs.get("project_id", None)
        if project_id:
            return project_id
        if resolve(self.request.path_info).url_name == "project":
            return self.kwargs.get("pk", None)

    @property
    def fields(self):
        fields = [
            field for field in self.request.GET.get("fields", "").split(",") if field
        ]
        return fields if fields else None

    @property
    def expand(self):
        expand = [
            expand for expand in self.request.GET.get("expand", "").split(",") if expand
        ]
        return expand if expand else None
