import logging
import zoneinfo

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import IntegrityError
from django.urls import resolve
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from common.paginator import BasePaginator
from common.responses import error_response

logger = logging.getLogger(__name__)


class TimezoneMixin:
    """
    This enables timezone conversion according
    to the user set timezone
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user.is_authenticated:
            timezone.activate(zoneinfo.ZoneInfo(request.user.user_timezone))
        else:
            timezone.deactivate()


class BaseViewSet(TimezoneMixin, ModelViewSet, BasePaginator):
    """
    Base ViewSet for all the viewsets, this will handle:
    -  timezone conversion
    -  pagination
    -  exception
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

    def handle_exception(self, exc):
        """
        Handle any exception that occurs, by returning an appropriate response, or re-raising the error.
        """
        try:
            response = super().handle_exception(exc)
            return response
        except Exception as e:
            if isinstance(e, IntegrityError):
                return error_response(
                    "The payload is not valid",
                    logger=logger,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if isinstance(e, ValidationError):
                return error_response(
                    "Please provide valid detail",
                    logger=logger,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if isinstance(e, ObjectDoesNotExist):
                return error_response(
                    "The required object does not exist.",
                    logger=logger,
                    status=status.HTTP_404_NOT_FOUND,
                )
            if isinstance(e, KeyError):
                return error_response(
                    "The required key does not exist.",
                    logger=logger,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return error_response(
                "Something went wrong please try again later",
                logger=logger,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def dispatch(self, request, *args, **kwargs):
        try:
            response = super().dispatch(request, *args, **kwargs)
            return response
        except Exception as exc:
            response = self.handle_exception(exc)
            return exc

    @property
    def workspace_slug(self):
        return self.kwargs.get("workspace_slug", None)

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


class BaseAPIView(TimezoneMixin, APIView, BasePaginator):
    """
    Base APIView for all the views, this will handle:
    -  timezone conversion
    -  pagination
    -  exception
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

    def handle_exception(self, exc):
        """
        Handle any exception that occurs, by returning an appropriate response, or re-raising the error.
        """
        try:
            response = super().handle_exception(exc)
            return response
        except Exception as e:
            if isinstance(e, IntegrityError):
                return error_response(
                    "The payload is not valid",
                    logger=logger,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if isinstance(e, ValidationError):
                return error_response(
                    "Please provide valid detail",
                    logger=logger,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if isinstance(e, ObjectDoesNotExist):
                return error_response(
                    "The required object does not exist.",
                    logger=logger,
                    status=status.HTTP_404_NOT_FOUND,
                )
            if isinstance(e, KeyError):
                return error_response(
                    "The required key does not exist.",
                    logger=logger,
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return error_response(
                "Something went wrong please try again later",
                logger=logger,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def dispatch(self, request, *args, **kwargs):
        try:
            response = super().dispatch(request, *args, **kwargs)
            return response

        except Exception as exc:
            response = self.handle_exception(exc)
            return exc

    @property
    def workspace_slug(self):
        return self.kwargs.get("workspace_slug", None)

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
