from uuid import uuid4

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from app.models import CreatorUpdaterModel, TimeStampedModel

from .base import ProjectBaseModel


def get_anchor():
    return uuid4().hex


class Project(TimeStampedModel, CreatorUpdaterModel):
    name = models.CharField(max_length=255, verbose_name="Project Name")
    description = models.TextField(verbose_name="Project Description", blank=True)
    description_text = models.JSONField(
        verbose_name="Project Description Rich Text", blank=True, null=True
    )
    description_html = models.JSONField(
        verbose_name="Project Description HTML", blank=True, null=True
    )
    workspace = models.ForeignKey(
        "iam.WorkSpace",
        on_delete=models.CASCADE,
        related_name="workspace_project",
    )
    identifier = models.CharField(
        max_length=12,
        verbose_name="Project Identifier",
    )
    default_assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="default_assignee",
        null=True,
        default=None,
    )
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lead",
        null=True,
        default=None,
    )
    emoji = models.CharField(max_length=255, null=True, blank=True)
    icon_prop = models.JSONField(null=True)
    module_view = models.BooleanField(default=True)
    cycle_view = models.BooleanField(default=True)
    issue_views_view = models.BooleanField(default=True)
    page_view = models.BooleanField(default=True)
    access = models.PositiveSmallIntegerField(
        default=0, choices=((1, "Private"), (0, "Public"))
    )
    cover_image = models.URLField(null=True, default=None)
    estimate = models.ForeignKey(
        "project.Estimate",
        on_delete=models.SET_NULL,
        related_name="projects",
        null=True,
    )
    archive_in = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(12)]
    )
    close_in = models.IntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(12)]
    )
    default_state = models.ForeignKey(
        "project.State",
        on_delete=models.SET_NULL,
        null=True,
        related_name="default_state",
    )

    class Meta:
        unique_together = [["identifier", "workspace"], ["name", "workspace"]]
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        db_table = "project"
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        self.identifier = self.identifier.strip().upper()
        return super().save(*args, **kwargs)


class ProjectBaseModel(CreatorUpdaterModel, TimeStampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="project_%(class)s"
    )
    workspace = models.ForeignKey(
        "iam.Workspace", models.CASCADE, related_name="workspace_%(class)s"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.project:
            self.workspace = self.project.workspace
        super(ProjectBaseModel, self).save(*args, **kwargs)


class ProjectMember(ProjectBaseModel):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="member_project",
    )
    comment = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    view_props = models.JSONField(default=dict)
    role = models.PositiveSmallIntegerField(
        choices=(
            (2, "Admin"),
            (1, "Member"),
            (0, "Guest"),
        ),
        default=1,
    )
    default_props = models.JSONField(default=dict)
    preferences = models.JSONField(default=dict)
    sort_order = models.FloatField(default=65535)

    def save(self, *args, **kwargs):
        if self._state.adding:
            smallest_sort_order = ProjectMember.objects.filter(
                workspace_id=self.project.workspace_id, member=self.member
            ).aggregate(smallest=models.Min("sort_order"))["smallest"]
            # Project ordering
            if smallest_sort_order is not None:
                self.sort_order = smallest_sort_order - 10000
        super(ProjectMember, self).save(*args, **kwargs)

    class Meta:
        unique_together = ["project", "member"]
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"
        db_table = "project_member"
        ordering = ("-created_at",)


class ProjectFavorite(ProjectBaseModel):
    """
    Indicates that a user has favorited a project
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_favorites",
    )

    class Meta:
        unique_together = ["project", "user"]
        verbose_name = "Project Favorite"
        verbose_name_plural = "Project Favorites"
        db_table = "project_favorite"
        ordering = ("-created_at",)


class ProjectIdentifier(CreatorUpdaterModel, TimeStampedModel):
    workspace = models.ForeignKey(
        "iam.Workspace",
        models.CASCADE,
        related_name="project_identifiers",
        null=True,
    )
    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name="project_identifier"
    )
    name = models.CharField(max_length=12)

    class Meta:
        unique_together = ["name", "workspace"]
        verbose_name = "Project Identifier"
        verbose_name_plural = "Project Identifiers"
        db_table = "project_identifier"
        ordering = ("-created_at",)


class ProjectDeployBoard(ProjectBaseModel):
    anchor = models.CharField(
        max_length=255, unique=True, db_index=True, default=get_anchor
    )
    comments = models.BooleanField(default=False)
    reactions = models.BooleanField(default=False)
    votes = models.BooleanField(default=False)
    views = models.JSONField(default=dict)

    class Meta:
        unique_together = ["project", "anchor"]
        verbose_name = "Project Deploy Board"
        verbose_name_plural = "Project Deploy Boards"
        db_table = "project_deploy_board"
        ordering = ("-created_at",)


class ProjectPublicMember(ProjectBaseModel):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="public_project_members",
    )

    class Meta:
        unique_together = ["project", "member"]
        verbose_name = "Project Public Member"
        verbose_name_plural = "Project Public Members"
        db_table = "project_public_member"
        ordering = ("-created_at",)


def get_default_labels():
    return [
        {
            "name": "Bug",
            "color": "#d73a4a",
            "sort_order": 65535,
        },
        {
            "name": "Feature Request",
            "color": "#a2eeef",
            "sort_order": 75535,
        },
        {
            "name": "Enhancement",
            "color": "#84b6eb",
            "sort_order": 85535,
        },
        {
            "name": "Documentation",
            "color": "#bfdadc",
            "sort_order": 95535,
        },
        {
            "name": "Design",
            "color": "#f9c513",
            "sort_order": 105535,
        },
        {
            "name": "Performance",
            "color": "#5752d9",
            "sort_order": 115535,
        },
        {
            "name": "Security",
            "color": "#e99695",
            "sort_order": 125535,
        },
        {
            "name": "Testing",
            "color": "#f9d0c4",
            "sort_order": 135535,
        },
        {
            "name": "Refactor",
            "color": "#fad8c7",
            "sort_order": 145535,
        },
        {
            "name": "Critical",
            "color": "#e12d2d",
            "sort_order": 155535,
        },
        {
            "name": "Wontfix",
            "color": "#ffffff",
            "sort_order": 165535,
        },
        {
            "name": "Question",
            "color": "#cc317c",
            "sort_order": 175535,
        },
        {
            "name": "Help Wanted",
            "color": "#128A0C",
            "sort_order": 185535,
        },
        {
            "name": "Good First Issue",
            "color": "#7057ff",
            "sort_order": 195535,
        },
        {
            "name": "Backend",
            "color": "#d4c5f9",
            "sort_order": 205535,
        },
        {
            "name": "Frontend",
            "color": "#bfd4f2",
            "sort_order": 215535,
        },
        {
            "name": "API",
            "color": "#b2b7ff",
            "sort_order": 225535,
        },
        {
            "name": "DevOps",
            "color": "#1d76db",
            "sort_order": 235535,
        },
    ]


def get_default_estimates():
    return {
        "points": [
            {
                "key": 0,
                "description": "",
                "value": "1",
                "estimate": 4,
            },
            {
                "key": 5,
                "description": "",
                "value": "13",
                "estimate": 4,
            },
            {
                "key": 1,
                "description": "",
                "value": "2",
                "estimate": 4,
            },
            {
                "key": 2,
                "description": "",
                "value": "3",
                "estimate": 4,
            },
            {
                "key": 3,
                "description": "",
                "value": "5",
                "estimate": 4,
            },
            {
                "key": 4,
                "description": "",
                "value": "8",
                "estimate": 4,
            },
        ],
        "name": "Effort Estimate",
        "description": "An estimate model using Fibonacci sequence for measuring development effort.",
    }


class ProjectTemplate(TimeStampedModel, CreatorUpdaterModel):
    workspace = models.OneToOneField(
        "iam.Workspace",
        on_delete=models.CASCADE,
        related_name="workspace_default_props",
    )
    labels = models.JSONField(default=get_default_labels)
    estimates = models.JSONField(default=get_default_estimates)

    class Meta:
        db_table = "project_template"
        verbose_name = "Project Template"
        verbose_name_plural = "Project Templates"
