from datetime import timedelta
from itertools import groupby

from django.db import models
from django.db.models import Case, CharField, Count, F, Sum, Value, When
from django.db.models.functions import (
    Coalesce,
    Concat,
    ExtractMonth,
    ExtractYear,
    TruncDate,
)
from django.utils import timezone

from project.models import Issue


def annotate_with_monthly_dimension(queryset, field_name, attribute):
    """
    Annotate the queryset with a dimension that is the concatenation of the year and the month
    """
    year = ExtractYear(field_name)
    month = ExtractMonth(field_name)
    dimension = Concat(year, Value("-"), month, output_field=CharField())
    return queryset.annotate(**{attribute: dimension})


def extract_axis(queryset, x_axis):
    """
    Extract the x_axis and queryset
    """
    if x_axis in ["created_at", "start_date", "target_date", "completed_at"]:
        queryset = annotate_with_monthly_dimension(queryset, x_axis, "dimension")
        return queryset, "dimension"
    else:
        return queryset.annotate(dimension=F(x_axis)), "dimension"


def sort_data(data, temp_axis):
    """
    Sort the data based on the x_axis
    """
    if temp_axis == "priority":
        order = ["low", "medium", "high", "urgent", "none"]
        return {key: data[key] for key in order if key in data}
    else:
        return dict(sorted(data.items(), key=lambda x: (x[0] == "none", x[0])))


def build_graph_plot(queryset, x_axis, y_axis, segment=None):
    """
    Build the graph plot
    - x_axis: The x-axis of the graph
    - y_axis: The y-axis of the graph
    - segment: The segment of the graph
    """
    temp_axis = x_axis
    queryset, x_axis = extract_axis(queryset, x_axis)
    if x_axis == "dimension":
        queryset = queryset.exclude(dimension__isnull=True)
    if segment in ["created_at", "start_date", "target_date", "completed_at"]:
        queryset = annotate_with_monthly_dimension(queryset, segment, "segmented")
        segment = "segmented"
    queryset = queryset.values(x_axis)
    if y_axis == "issue_count":
        queryset = queryset.annotate(
            is_null=Case(
                When(dimension__isnull=True, then=Value("None")),
                default=Value("not_null"),
                output_field=models.CharField(max_length=8),
            ),
            dimension_ex=Coalesce("dimension", Value("null")),
        ).values("dimension")
        queryset = queryset.annotate(segment=F(segment)) if segment else queryset
        queryset = (
            queryset.values("dimension", "segment")
            if segment
            else queryset.values("dimension")
        )
        queryset = queryset.annotate(count=Count("*")).order_by("dimension")
    else:
        queryset = queryset.annotate(estimate=Sum("estimate_point")).order_by(x_axis)
        queryset = queryset.annotate(segment=F(segment)) if segment else queryset
        queryset = (
            queryset.values("dimension", "segment", "estimate")
            if segment
            else queryset.values("dimension", "estimate")
        )
    result_values = list(queryset)
    grouped_data = {
        str(key): list(items)
        for key, items in groupby(result_values, key=lambda x: x[str("dimension")])
    }
    return sort_data(grouped_data, temp_axis)


def burndown_plot(queryset, slug, project_id, cycle_id=None, module_id=None):
    """
    Build the burndown plot
    - cycle_id: The cycle id
    - module_id: The module id
    """
    total_issues = (
        queryset["total_issues"]
        if isinstance(queryset, dict)
        else queryset.total_issues
    )
    if cycle_id:
        start_date = (
            queryset["start_date"]
            if isinstance(queryset, dict)
            else queryset.start_date
        )
        end_date = (
            queryset["end_date"] if isinstance(queryset, dict) else queryset.end_date
        )
        date_range = [
            start_date + timedelta(days=x)
            for x in range((end_date - start_date).days + 1)
        ]
        chart_data = {str(date): 0 for date in date_range}
        completed_issues_distribution = (
            Issue.issue_objects.filter(
                workspace__slug=slug,
                project_id=project_id,
                issue_cycle__cycle_id=cycle_id,
            )
            .annotate(date=TruncDate("completed_at"))
            .values("date")
            .annotate(total_completed=Count("id"))
            .values("date", "total_completed")
            .order_by("date")
        )
    if module_id:
        date_range = [
            queryset.start_date + timedelta(days=x)
            for x in range((queryset.target_date - queryset.start_date).days + 1)
        ]
        chart_data = {str(date): 0 for date in date_range}
        completed_issues_distribution = (
            Issue.issue_objects.filter(
                workspace__slug=slug,
                project_id=project_id,
                issue_module__module_id=module_id,
            )
            .annotate(date=TruncDate("completed_at"))
            .values("date")
            .annotate(total_completed=Count("id"))
            .values("date", "total_completed")
            .order_by("date")
        )
    for date in date_range:
        cumulative_pending_issues = total_issues
        total_completed = 0
        total_completed = sum(
            item["total_completed"]
            for item in completed_issues_distribution
            if item["date"] is not None and item["date"] <= date
        )
        cumulative_pending_issues -= total_completed
        if date > timezone.now().date():
            chart_data[str(date)] = None
        else:
            chart_data[str(date)] = cumulative_pending_issues
    return chart_data
