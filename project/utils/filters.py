import re
from datetime import timedelta

from django.utils import timezone


def filter_valid_ids(id_list):
    """
    Filter valid uuids from a list of strings
    """
    valid_ids = []
    for id in id_list:
        try:
            valid_ids.append(int(id))
        except ValueError:
            pass
    return valid_ids


def string_date_filter(filter, duration, subsequent, term, date_filter, offset):
    """
    Handle all string date filters
    """
    now = timezone.now().date()
    if term == "months":
        if subsequent == "after":
            if offset == "fromnow":
                filter[f"{date_filter}__gte"] = now + timedelta(days=duration * 30)
            else:
                filter[f"{date_filter}__gte"] = now - timedelta(days=duration * 30)
        else:
            if offset == "fromnow":
                filter[f"{date_filter}__lte"] = now + timedelta(days=duration * 30)
            else:
                filter[f"{date_filter}__lte"] = now - timedelta(days=duration * 30)
    if term == "weeks":
        if subsequent == "after":
            if offset == "fromnow":
                filter[f"{date_filter}__gte"] = now + timedelta(weeks=duration)
            else:
                filter[f"{date_filter}__gte"] = now - timedelta(weeks=duration)
        else:
            if offset == "fromnow":
                filter[f"{date_filter}__lte"] = now + timedelta(days=duration)
            else:
                filter[f"{date_filter}__lte"] = now - timedelta(days=duration)


def date_filter(filter, date_term, queries):
    """
    Handle all date filters
    """
    for query in queries:
        date_query = query.split(";")
        if len(date_query) >= 2:
            match = re.compile(r"\d+_(weeks|months)$").match(date_query[0])
            if match:
                if len(date_query) == 3:
                    digit, term = date_query[0].split("_")
                    string_date_filter(
                        filter=filter,
                        duration=int(digit),
                        subsequent=date_query[1],
                        term=term,
                        date_filter=date_term,
                        offset=date_query[2],
                    )
            else:
                if "after" in date_query:
                    filter[f"{date_term}__gte"] = date_query[0]
                else:
                    filter[f"{date_term}__lte"] = date_query[0]


def filter_state(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by state
    """
    if method == "GET":
        states = [item for item in params.get("state").split(",") if item != "null"]
        states = filter_valid_ids(states)
        if len(states) and "" not in states:
            filter["state__in"] = states
    else:
        if (
            params.get("state", None)
            and len(params.get("state"))
            and params.get("state") != "null"
        ):
            filter["state__in"] = params.get("state")
    return filter


def filter_state_group(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by state group
    """
    if method == "GET":
        state_group = [
            item for item in params.get("state_group").split(",") if item != "null"
        ]
        if len(state_group) and "" not in state_group:
            filter["state__group__in"] = state_group
    else:
        if (
            params.get("state_group", None)
            and len(params.get("state_group"))
            and params.get("state_group") != "null"
        ):
            filter["state__group__in"] = params.get("state_group")
    return filter


def filter_estimate_point(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by estimate point
    """
    if method == "GET":
        estimate_points = [
            item for item in params.get("estimate_point").split(",") if item != "null"
        ]
        if len(estimate_points) and "" not in estimate_points:
            filter["estimate_point__in"] = estimate_points
    else:
        if (
            params.get("estimate_point", None)
            and len(params.get("estimate_point"))
            and params.get("estimate_point") != "null"
        ):
            filter["estimate_point__in"] = params.get("estimate_point")
    return filter


def filter_priority(params: dict, filter: dict, method: str) -> dict:
    if method == "GET":
        priorities = [
            item for item in params.get("priority").split(",") if item != "null"
        ]
        if len(priorities) and "" not in priorities:
            filter["priority__in"] = priorities
    return filter


def filter_parent(params: dict, filter: dict, method: str) -> dict:
    if method == "GET":
        parents = [item for item in params.get("parent").split(",") if item != "null"]
        parents = filter_valid_ids(parents)
        if len(parents) and "" not in parents:
            filter["parent__in"] = parents
    else:
        if (
            params.get("parent", None)
            and len(params.get("parent"))
            and params.get("parent") != "null"
        ):
            filter["parent__in"] = params.get("parent")
    return filter


def filter_labels(params: dict, filter: dict, method: str) -> dict:
    if method == "GET":
        labels = [item for item in params.get("labels").split(",") if item != "null"]
        labels = filter_valid_ids(labels)
        if len(labels) and "" not in labels:
            filter["labels__in"] = labels
    else:
        if (
            params.get("labels", None)
            and len(params.get("labels"))
            and params.get("labels") != "null"
        ):
            filter["labels__in"] = params.get("labels")
    return filter


def filter_assignees(params: dict, filter: dict, method: str) -> dict:
    if method == "GET":
        assignees = [
            item for item in params.get("assignees").split(",") if item != "null"
        ]
        assignees = filter_valid_ids(assignees)
        if len(assignees) and "" not in assignees:
            filter["assignees__in"] = assignees
    else:
        if (
            params.get("assignees", None)
            and len(params.get("assignees"))
            and params.get("assignees") != "null"
        ):
            filter["assignees__in"] = params.get("assignees")
    return filter


def filter_mentions(params: dict, filter: dict, method: str) -> dict:
    """Filter issues by mentions"""
    if method == "GET":
        mentions = [
            item for item in params.get("mentions").split(",") if item != "null"
        ]
        mentions = filter_valid_ids(mentions)
        if len(mentions) and "" not in mentions:
            filter["issue_mention__mention__id__in"] = mentions
    else:
        if (
            params.get("mentions", None)
            and len(params.get("mentions"))
            and params.get("mentions") != "null"
        ):
            filter["issue_mention__mention__id__in"] = params.get("mentions")
    return filter


def filter_created_by(params: dict, filter: dict, method: str) -> dict:
    """Filter issues by created by"""
    if method == "GET":
        created_bys = [
            item for item in params.get("created_by").split(",") if item != "null"
        ]
        created_bys = filter_valid_ids(created_bys)
        if len(created_bys) and "" not in created_bys:
            filter["created_by__in"] = created_bys
    else:
        if (
            params.get("created_by", None)
            and len(params.get("created_by"))
            and params.get("created_by") != "null"
        ):
            filter["created_by__in"] = params.get("created_by")
    return filter


def filter_name(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by name
    """
    if params.get("name", "") != "":
        filter["name__icontains"] = params.get("name")
    return filter


def filter_created_at(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by created at date
    """

    if method == "GET":
        created_ats = params.get("created_at").split(",")
        if len(created_ats) and "" not in created_ats:
            date_filter(
                filter=filter,
                date_term="created_at__date",
                queries=created_ats,
            )
    else:
        if params.get("created_at", None) and len(params.get("created_at")):
            date_filter(
                filter=filter,
                date_term="created_at__date",
                queries=params.get("created_at", []),
            )
    return filter


def filter_updated_at(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by updated at date
    """
    if method == "GET":
        updated_ats = params.get("updated_at").split(",")
        if len(updated_ats) and "" not in updated_ats:
            date_filter(
                filter=filter,
                date_term="created_at__date",
                queries=updated_ats,
            )
    else:
        if params.get("updated_at", None) and len(params.get("updated_at")):
            date_filter(
                filter=filter,
                date_term="created_at__date",
                queries=params.get("updated_at", []),
            )
    return filter


def filter_start_date(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by start date
    """
    if method == "GET":
        start_dates = params.get("start_date").split(",")
        if len(start_dates) and "" not in start_dates:
            date_filter(filter=filter, date_term="start_date", queries=start_dates)
    else:
        if params.get("start_date", None) and len(params.get("start_date")):
            filter["start_date"] = params.get("start_date")
    return filter


def filter_target_date(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by target date
    """
    if method == "GET":
        target_dates = params.get("target_date").split(",")
        if len(target_dates) and "" not in target_dates:
            date_filter(filter=filter, date_term="target_date", queries=target_dates)
    else:
        if params.get("target_date", None) and len(params.get("target_date")):
            filter["target_date"] = params.get("target_date")
    return filter


def filter_completed_at(params: dict, filter: dict, method: str) -> dict:
    """Filter issues by completed at date"""
    if method == "GET":
        completed_ats = params.get("completed_at").split(",")
        if len(completed_ats) and "" not in completed_ats:
            date_filter(
                filter=filter,
                date_term="completed_at__date",
                queries=completed_ats,
            )
    else:
        if params.get("completed_at", None) and len(params.get("completed_at")):
            date_filter(
                filter=filter,
                date_term="completed_at__date",
                queries=params.get("completed_at", []),
            )
    return filter


def filter_issue_state_type(params: dict, filter: dict, method: str) -> dict:
    """Filter issues by state type"""
    type = params.get("type", "all")
    group = ["backlog", "unstarted", "started", "completed", "cancelled"]
    if type == "backlog":
        group = ["backlog"]
    if type == "active":
        group = ["unstarted", "started"]

    filter["state__group__in"] = group
    return filter


def filter_project(params: dict, filter: dict, method: str) -> dict:
    """Filter issues by project"""
    if method == "GET":
        projects = [item for item in params.get("project").split(",") if item != "null"]
        projects = filter_valid_ids(projects)
        if len(projects) and "" not in projects:
            filter["project__in"] = projects
    else:
        if (
            params.get("project", None)
            and len(params.get("project"))
            and params.get("project") != "null"
        ):
            filter["project__in"] = params.get("project")
    return filter


def filter_cycle(params: dict, filter: dict, method: str) -> dict:
    """Filter issues by cycle"""
    if method == "GET":
        cycles = [item for item in params.get("cycle").split(",") if item != "null"]
        cycles = filter_valid_ids(cycles)
        if len(cycles) and "" not in cycles:
            filter["issue_cycle__cycle_id__in"] = cycles
    else:
        if (
            params.get("cycle", None)
            and len(params.get("cycle"))
            and params.get("cycle") != "null"
        ):
            filter["issue_cycle__cycle_id__in"] = params.get("cycle")
    return filter


def filter_module(params: dict, filter: dict, method: str) -> dict:
    """Filter issues by module"""
    if method == "GET":
        modules = [item for item in params.get("module").split(",") if item != "null"]
        modules = filter_valid_ids(modules)
        if len(modules) and "" not in modules:
            filter["issue_module__module_id__in"] = modules
    else:
        if (
            params.get("module", None)
            and len(params.get("module"))
            and params.get("module") != "null"
        ):
            filter["issue_module__module_id__in"] = params.get("module")
    return filter


def filter_inbox_status(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by inbox status
    """
    if method == "GET":
        status = [
            item for item in params.get("inbox_status").split(",") if item != "null"
        ]
        if len(status) and "" not in status:
            filter["issue_inbox__status__in"] = status
    else:
        if (
            params.get("inbox_status", None)
            and len(params.get("inbox_status"))
            and params.get("inbox_status") != "null"
        ):
            filter["issue_inbox__status__in"] = params.get("inbox_status")
    return filter


def filter_sub_issue_toggle(params: dict, filter: dict, method: str) -> dict:
    """
    Filter sub issues
    - params: The query parameters
    - filter: The filter dictionary
    - method: The request method
    """
    if method == "GET":
        sub_issue = params.get("sub_issue", "false")
        if sub_issue == "false":
            filter["parent__isnull"] = True
    else:
        sub_issue = params.get("sub_issue", "false")
        if sub_issue == "false":
            filter["parent__isnull"] = True
    return filter


def filter_subscribed_issues(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by subscribers
    - params: The query parameters
    - filter: The filter dictionary
    - method: The request method
    """
    if method == "GET":
        subscribers = [
            item for item in params.get("subscriber").split(",") if item != "null"
        ]
        subscribers = filter_valid_ids(subscribers)
        if len(subscribers) and "" not in subscribers:
            filter["issue_subscribers__subscriber_id__in"] = subscribers
    else:
        if (
            params.get("subscriber", None)
            and len(params.get("subscriber"))
            and params.get("subscriber") != "null"
        ):
            filter["issue_subscribers__subscriber_id__in"] = params.get("subscriber")
    return filter


def filter_start_target_date_issues(params: dict, filter: dict, method: str) -> dict:
    """
    Filter issues by start and target date
    - params: The query parameters
    - filter: The filter dictionary
    - method: The request method
    """
    start_target_date = params.get("start_target_date", "false")
    if start_target_date == "true":
        filter["target_date__isnull"] = False
        filter["start_date__isnull"] = False
    return filter


def issue_filters(query_params, method: str):
    """
    Filter issues
    - query_params: The query parameters
    - method: The request method
    """
    filter = {}

    ISSUE_FILTER = {
        "state": filter_state,
        "state_group": filter_state_group,
        "estimate_point": filter_estimate_point,
        "priority": filter_priority,
        "parent": filter_parent,
        "labels": filter_labels,
        "assignees": filter_assignees,
        "mentions": filter_mentions,
        "created_by": filter_created_by,
        "name": filter_name,
        "created_at": filter_created_at,
        "updated_at": filter_updated_at,
        "start_date": filter_start_date,
        "target_date": filter_target_date,
        "completed_at": filter_completed_at,
        "type": filter_issue_state_type,
        "project": filter_project,
        "cycle": filter_cycle,
        "module": filter_module,
        "inbox_status": filter_inbox_status,
        "sub_issue": filter_sub_issue_toggle,
        "subscriber": filter_subscribed_issues,
        "start_target_date": filter_start_target_date_issues,
    }

    for key, value in ISSUE_FILTER.items():
        if key in query_params:
            func = value
            func(query_params, filter, method)

    return filter
