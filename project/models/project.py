from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from app.models import CreatorUpdaterModel, TimeStampedModel
from common.utils.file_field import file_size_validator, upload_path
from project.models.base import ProjectBaseModel


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
    inbox_view = models.BooleanField(default=False)
    access = models.PositiveSmallIntegerField(
        default=1, choices=((0, "Private"), (1, "Public"))
    )
    cover_image = models.FileField(
        upload_to=upload_path,
        default=None,
        null=True,
        validators=[file_size_validator],
    )
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


class ProjectMemberInvite(ProjectBaseModel):
    email = models.CharField(max_length=255)
    accepted = models.BooleanField(default=False)
    token = models.CharField(max_length=255)
    message = models.TextField(null=True)

    class Meta:
        verbose_name = "Project Member Invite"
        verbose_name_plural = "Project Member Invites"
        db_table = "project_member_invite"
        ordering = ("-created_at",)


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
    default_props = models.JSONField(default=dict)
    preferences = models.JSONField(default=dict)

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
