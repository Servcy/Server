import re

from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from common.views import BaseAPIView
from iam.models import Workspace
from project.models import Cycle, Issue, IssueView, Module, Page, Project
from project.utils.search import search_issues


class GlobalSearchEndpoint(BaseAPIView):
    """Endpoint to search across multiple fields in the workspace and
    also show related workspace if found
    """

    def filter_workspaces(self, query, **kwargs):
        fields = ["name"]
        q = Q()
        for field in fields:
            q |= Q(**{f"{field}__icontains": query})
        return (
            Workspace.objects.filter(q, workspace_member__member=self.request.user)
            .distinct()
            .values("name", "id", "slug")
        )

    def filter_projects(self, query, workspace_slug, **kwargs):
        fields = ["name", "identifier"]
        q = Q()
        for field in fields:
            q |= Q(**{f"{field}__icontains": query})
        return (
            Project.objects.filter(
                q,
                project_projectmember__member=self.request.user,
                archived_at__isnull=True,
                project_projectmember__is_active=True,
                workspace__slug=workspace_slug,
            )
            .distinct()
            .values("name", "id", "identifier", "workspace__slug")
        )

    def filter_issues(self, query, workspace_slug, project_id, workspace_search):
        fields = ["name", "sequence_id", "project__identifier"]
        q = Q()
        for field in fields:
            if field == "sequence_id":
                # Match whole integers only (exclude decimal numbers)
                sequences = re.findall(r"\b\d+\b", query)
                for sequence_id in sequences:
                    q |= Q(**{"sequence_id": sequence_id})
            else:
                q |= Q(**{f"{field}__icontains": query})

        issues = Issue.issue_objects.filter(
            q,
            project__project_projectmember__member=self.request.user,
            project__project_projectmember__is_active=True,
            workspace__slug=workspace_slug,
        )

        if workspace_search == "false" and project_id:
            issues = issues.filter(project_id=project_id)

        return issues.distinct().values(
            "name",
            "id",
            "sequence_id",
            "project__identifier",
            "project_id",
            "workspace__slug",
        )

    def filter_cycles(self, query, workspace_slug, project_id, workspace_search):
        fields = ["name"]
        q = Q()
        for field in fields:
            q |= Q(**{f"{field}__icontains": query})

        cycles = Cycle.objects.filter(
            q,
            project__project_projectmember__member=self.request.user,
            project__project_projectmember__is_active=True,
            workspace__slug=workspace_slug,
        )

        if workspace_search == "false" and project_id:
            cycles = cycles.filter(project_id=project_id)

        return cycles.distinct().values(
            "name",
            "id",
            "project_id",
            "project__identifier",
            "workspace__slug",
        )

    def filter_modules(self, query, workspace_slug, project_id, workspace_search):
        fields = ["name"]
        q = Q()
        for field in fields:
            q |= Q(**{f"{field}__icontains": query})

        modules = Module.objects.filter(
            q,
            project__project_projectmember__member=self.request.user,
            project__project_projectmember__is_active=True,
            workspace__slug=workspace_slug,
        )

        if workspace_search == "false" and project_id:
            modules = modules.filter(project_id=project_id)

        return modules.distinct().values(
            "name",
            "id",
            "project_id",
            "project__identifier",
            "workspace__slug",
        )

    def filter_pages(self, query, workspace_slug, project_id, workspace_search):
        fields = ["name"]
        q = Q()
        for field in fields:
            q |= Q(**{f"{field}__icontains": query})

        pages = Page.objects.filter(
            q,
            project__project_projectmember__member=self.request.user,
            project__project_projectmember__is_active=True,
            workspace__slug=workspace_slug,
        )

        if workspace_search == "false" and project_id:
            pages = pages.filter(project_id=project_id)

        return pages.distinct().values(
            "name",
            "id",
            "project_id",
            "project__identifier",
            "workspace__slug",
        )

    def filter_views(self, query, workspace_slug, project_id, workspace_search):
        fields = ["name"]
        q = Q()
        for field in fields:
            q |= Q(**{f"{field}__icontains": query})

        issue_views = IssueView.objects.filter(
            q,
            project__project_projectmember__member=self.request.user,
            project__project_projectmember__is_active=True,
            workspace__slug=workspace_slug,
        )

        if workspace_search == "false" and project_id:
            issue_views = issue_views.filter(project_id=project_id)

        return issue_views.distinct().values(
            "name",
            "id",
            "project_id",
            "project__identifier",
            "workspace__slug",
        )

    def get(self, request, workspace_slug):
        query = request.query_params.get("search", False)
        workspace_search = request.query_params.get("workspace_search", "false")
        project_id = request.query_params.get("project_id", False)

        if not query:
            return Response(
                {
                    "results": {
                        "workspace": [],
                        "project": [],
                        "issue": [],
                        "cycle": [],
                        "module": [],
                        "issue_view": [],
                        "page": [],
                    }
                },
                status=status.HTTP_200_OK,
            )

        MODELS_MAPPER = {
            "workspace": self.filter_workspaces,
            "project": self.filter_projects,
            "issue": self.filter_issues,
            "cycle": self.filter_cycles,
            "module": self.filter_modules,
            "issue_view": self.filter_views,
            "page": self.filter_pages,
        }

        results = {}

        for model in MODELS_MAPPER.keys():
            func = MODELS_MAPPER.get(model, None)
            results[model] = func(
                query,
                workspace_slug=workspace_slug,
                project_id=project_id,
                workspace_search=workspace_search,
            )
        return Response({"results": results}, status=status.HTTP_200_OK)


class IssueSearchEndpoint(BaseAPIView):
    def get(self, request, workspace_slug, project_id):
        query = request.query_params.get("search", False)
        workspace_search = request.query_params.get("workspace_search", "false")
        parent = request.query_params.get("parent", "false")
        issue_relation = request.query_params.get("issue_relation", "false")
        cycle = request.query_params.get("cycle", "false")
        module = request.query_params.get("module", False)
        sub_issue = request.query_params.get("sub_issue", "false")

        issue_id = request.query_params.get("issue_id", False)

        issues = Issue.issue_objects.filter(
            workspace__slug=workspace_slug,
            project__project_projectmember__member=self.request.user,
            project__project_projectmember__is_active=True,
        )

        if workspace_search == "false":
            issues = issues.filter(project_id=project_id)

        if query:
            issues = search_issues(query, issues)

        if parent == "true" and issue_id:
            issue = Issue.issue_objects.get(pk=issue_id)
            issues = issues.filter(
                ~Q(pk=issue_id), ~Q(pk=issue.parent_id), ~Q(parent_id=issue_id)
            )
        if issue_relation == "true" and issue_id:
            issue = Issue.issue_objects.get(pk=issue_id)
            issues = issues.filter(
                ~Q(pk=issue_id),
                ~Q(issue_related__issue=issue),
                ~Q(issue_relation__related_issue=issue),
            )
        if sub_issue == "true" and issue_id:
            issue = Issue.issue_objects.get(pk=issue_id)
            issues = issues.filter(~Q(pk=issue_id), parent__isnull=True)
            if issue.parent:
                issues = issues.filter(~Q(pk=issue.parent_id))

        if cycle == "true":
            issues = issues.exclude(issue_cycle__isnull=False)

        if module:
            issues = issues.exclude(issue_module__module=module)

        return Response(
            issues.values(
                "name",
                "id",
                "sequence_id",
                "project__name",
                "project__identifier",
                "project_id",
                "workspace__slug",
                "state__name",
                "state__group",
                "state__color",
            ),
            status=status.HTTP_200_OK,
        )
