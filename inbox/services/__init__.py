from django.db.models import Q

from common.datatable import DataTableBase
from inbox.models import Inbox
from inbox.repository import InboxRepository
from inbox.serializers import InboxSerializer


class InboxService(DataTableBase):
    serializer_class = InboxSerializer

    def __init__(self, user, user_id: int) -> None:
        self.user_id = user_id
        self.user = user
        self.queryset = None
        self.filters = {}
        self.search = ""
        self.sort_by = []
        self.sort_desc = []
        self.page = 1
        self.page_size = 10

    def source_filter(self, source: str):
        if self.filters.get("source"):
            return Q(user_integration__integration__name=source)
        return Q()

    def category_filter(self, category: str):
        if self.filters.get("category") == "archived":
            return Q(is_archived=True)
        if self.filters.get("category"):
            return Q(category=category, is_archived=False)
        return Q(is_archived=False)

    def i_am_mentioned_filter(self, i_am_mentioned: bool):
        return Q(i_am_mentioned=i_am_mentioned)

    def get_queryset(self) -> "InboxService":
        q = Q(user_integration__user=self.user)
        for key, val in self.filters.items():
            if not val:
                continue
            func = getattr(self, f"{key}_filter", None)
            assert callable(func), f"Filter {key} not implemented"
            q &= func(val)
        self.queryset = InboxRepository.filter(q).select_related(
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

    def archive_item(self, item_ids: list[int]) -> Inbox:
        """
        Archive an item.
        """
        return InboxRepository.archive_item(item_ids=item_ids)

    def read_item(self, item_id: int) -> Inbox:
        """
        Archive an item.
        """
        return InboxRepository.read_item(item_id=item_id)

    def delete_items(self, item_ids: list[int]) -> Inbox:
        """
        Archive an item.
        """
        return InboxRepository.delete_items(item_ids=item_ids)

    def apply_searching(self: "DataTableBase") -> "DataTableBase":
        self.queryset = self.queryset.filter(
            Q(title__icontains=self.search) | Q(body__icontains=self.search)
        )
        return self
