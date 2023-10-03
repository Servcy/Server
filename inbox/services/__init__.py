from django.db.models import Q

from common.datatable import DataTableBase
from iam.models import User
from inbox.models import Inbox
from inbox.repository import InboxRepository
from inbox.serializers import InboxSerializer


class InboxService(DataTableBase):
    serializer_class = InboxSerializer

    def __init__(self, user: User, user_id: int) -> None:
        self.user_id = user_id
        self.user = user
        self.queryset = None
        self.filters = {}
        self.search = {}
        self.sort_by = []
        self.sort_desc = []
        self.page = 1
        self.page_size = 10

    def source_filter(self, source: str):
        if self.filters.get("source"):
            return Q(user_integration__integration__name=source)
        return Q()

    def category_filter(self, category: str):
        if self.filters.get("category"):
            return Q(category=category)
        return Q()

    def is_archived_filter(self, is_archived: bool):
        if self.filters.get("is_archived"):
            return Q(is_archived=is_archived)
        return Q(is_archived=False)

    def is_deleted_filter(self, is_deleted: bool):
        if self.filters.get("is_deleted"):
            return Q(is_deleted=is_deleted)
        return Q(is_deleted=False)

    def get_queryset(self) -> "InboxService":
        q = Q(user_integration__user=self.user)
        for key, val in self.filters.items():
            if not val:
                continue
            func = getattr(self, f"{key}_filter", None)
            assert callable(func), f"Filter {key} not implemented"
            q &= func(val)
        self.queryset = Inbox.objects.filter(q).select_related(
            "user_integration__integration"
        )
        return self

    def get_paginated_items(
        self,
        filters: dict = {},
        search: dict = {},
        sort_by: list = [],
        sort_desc: list = [],
        page: int = 1,
        page_size: int = 10,
    ):
        self.filters = filters
        self.search = search
        self.sort_by = sort_by
        self.sort_desc = sort_desc
        self.page = page
        self.page_size = page_size
        return super().get_paginated_items()

    def read_item(self, item_ids: list[int]) -> Inbox:
        """
        Read an item.
        """
        return InboxRepository.read_item(item_ids=item_ids)

    def archive_item(self, item_ids: list[int]) -> Inbox:
        """
        Archive an item.
        """
        return InboxRepository.archive_item(item_ids=item_ids)

    def delete_item(self, item_ids: list[int]) -> Inbox:
        """
        Delete an item.
        """
        return InboxRepository.delete_item(item_ids=item_ids)
