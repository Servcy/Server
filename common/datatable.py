from abc import ABC, abstractmethod

from rest_framework.settings import api_settings as rest_framework_settings

from common.utils import CommonUtils


class DataTableBase(ABC):
    """
    The standard datatable class for all the modules.
    Whenever we use a datatable in any module to show data, we need to subclass this class.
    """

    search_type_mapping = {
        "str": "__icontains",
        "==": "",
        ">=": "__gte",
        "<=": "__lte",
        "<": "__lt",
        ">": "__gt",
    }

    pagination_class = rest_framework_settings.DEFAULT_PAGINATION_CLASS

    def __init__(self):
        self.user_id = None
        self.user = None
        self.user = None
        self.filters = {}
        self.search = {}
        self.sort_by = []
        self.sort_desc = []
        self.page = 1
        self.page_size = 10

    @property
    def default_sort(self):
        return "-created_at"

    @abstractmethod
    def get_queryset(self) -> "DataTableBase":
        """
        The function is used to get the primary queryset for the datatable.
        This function needs to be MANDATORILY IMPLEMENTED in the subclass.
        """

    def apply_sorting(self: "DataTableBase") -> "DataTableBase":
        sort_settings = [
            column if not self.sort_desc[index] else "-" + column
            for index, column in enumerate(self.sort_by)
        ]
        self.queryset = (
            self.queryset.order_by(*sort_settings)
            if sort_settings
            else self.queryset.order_by(self.default_sort)
        )
        return self

    def apply_searching(self: "DataTableBase") -> "DataTableBase":
        self.queryset = self.queryset.filter(
            **{
                f"{column}{self.search_type_mapping[val['type']]}": val["value"].strip()
                for column, val in self.search.items()
                if val["value"].strip()
            }
        )
        return self

    def get_serializer_class(self):
        """class level variable `serializer_class` must be defined"""
        return self.serializer_class

    def get_paginated_items(self):
        """
        The function used to get the final paginated response data for the datatable
        This function has 5 steps
        1) Get the serializer which needs to be used for serializing the data
        2) Get the queryset for the data
        3) Apply the sorting logic on the queryset
        4) Paginate the queryset using the Paginate Common Utility
        5) Use the serializer to serialize the queryset and get the return results
        """

        serializer = self.get_serializer_class()
        self.get_queryset().apply_searching().apply_sorting()
        paginated_queryset, paginator_details = CommonUtils.paginate(
            self.queryset, self.page_size, self.page
        )
        return serializer(paginated_queryset, many=True).data, paginator_details
