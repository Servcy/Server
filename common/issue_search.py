from django.db.models import Q


def search_issues(query, queryset):
    fields = ["name", "project__identifier"]
    q = Q()
    for field in fields:
        q |= Q(**{f"{field}__icontains": query})
    return queryset.filter(
        q,
    ).distinct()
