from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models

from app.models import TimeStampedModel
from common.utils.file_field import file_size_validator, upload_path
from iam.managers import UserAccountManager


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(unique=True, null=True, default=None)
    username = models.CharField(max_length=150, unique=True)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$", message="Please enter a valid phone number"
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, null=True, default=None
    )
    is_staff = models.BooleanField(default=False)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=False)
    profile_image = models.FileField(
        upload_to=upload_path, null=True, default=None, validators=[file_size_validator]
    )
    invited_by = models.ForeignKey(
        "self",
        default=None,
        null=True,
        on_delete=models.PROTECT,
    )

    USERNAME_FIELD = "username"
    objects = UserAccountManager()

    class Meta:
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"


class Workspace(TimeStampedModel):
    name = models.CharField(max_length=150, verbose_name="Workspace Name")
    logo = models.FileField(
        upload_to=upload_path, null=True, default=None, validators=[file_size_validator]
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner")

    class Meta:
        db_table = "workspace"
        verbose_name = "Workspace"
        verbose_name_plural = "Workspaces"
        unique_together = ("name", "owner")


class WorkspaceInvite(TimeStampedModel):
    email = models.EmailField()
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    message = models.TextField(null=True)
    token = models.CharField(max_length=255)
    role = models.PositiveSmallIntegerField(
        choices=(
            (3, "Owner"),
            (2, "Admin"),
            (1, "Member"),
            (0, "Guest"),
        ),
        default=10,
    )
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)

    class Meta:
        db_table = "workspace_invite"
        verbose_name = "Workspace Invite"
        verbose_name_plural = "Workspace Invites"


class WorkspaceMember(TimeStampedModel):
    member = models.ForeignKey(User, on_delete=models.CASCADE)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    invite = models.ForeignKey(WorkspaceInvite, on_delete=models.CASCADE)
    role = models.PositiveSmallIntegerField(
        choices=(
            (3, "Owner"),
            (2, "Admin"),
            (1, "Member"),
            (0, "Guest"),
        ),
        default=1,
    )
    company_role = models.TextField(null=True, blank=True)
    view_props = models.JSONField(default=dict)
    default_props = models.JSONField(default=dict)
    issue_props = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "workspace_member"
        verbose_name = "Workspace Member"
        verbose_name_plural = "Workspace Members"


class WorkspaceTheme(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="themes"
    )
    name = models.CharField(max_length=300)
    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="themes",
    )
    colors = models.JSONField(default=dict)

    class Meta:
        unique_together = ["workspace", "name"]
        verbose_name = "Workspace Theme"
        verbose_name_plural = "Workspace Themes"
        db_table = "workspace_theme"
        ordering = ("-created_at",)


class WorkspaceUserProperties(TimeStampedModel):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="workspace_user_properties",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="workspace_user_properties",
    )
    filters = models.JSONField(default=dict)
    display_filters = models.JSONField(default=dict)
    display_properties = models.JSONField(default=dict)

    class Meta:
        unique_together = ["workspace", "user"]
        verbose_name = "Workspace User Property"
        verbose_name_plural = "Workspace User Property"
        db_table = "workspace_user_property"
        ordering = ("-created_at",)
