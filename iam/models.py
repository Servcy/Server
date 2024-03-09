import random
import string

import pytz
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models

from app.models import CreatorUpdaterModel, TimeStampedModel
from common.file_field import file_size_validator, upload_path
from common.validators import slug_validator
from iam.managers import UserAccountManager


def get_onboarding_step():
    return {
        "profile_complete": False,
        "workspace_create": False,
        "workspace_invite": False,
        "workspace_join": False,
    }


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(unique=True, null=True, default=None)
    username = models.CharField(max_length=150, unique=True)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$", message="Please enter a valid phone number"
    )
    phone_number = models.CharField(
        validators=[phone_regex], max_length=17, null=True, default=None
    )
    avatar = models.CharField(max_length=255, blank=True)
    cover_image = models.URLField(blank=True, null=True, max_length=800)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_tour_completed = models.BooleanField(default=False)
    is_onboarded = models.BooleanField(default=False)

    invited_by = models.ForeignKey(
        "self",
        default=None,
        null=True,
        on_delete=models.PROTECT,
    )

    USER_TIMEZONE_CHOICES = tuple(zip(pytz.all_timezones, pytz.all_timezones))
    user_timezone = models.CharField(
        max_length=255, default="UTC", choices=USER_TIMEZONE_CHOICES
    )
    theme = models.JSONField(default=dict)
    display_name = models.CharField(max_length=255, default="")
    use_case = models.TextField(blank=True, null=True)
    onboarding_step = models.JSONField(default=get_onboarding_step)
    last_workspace_id = models.IntegerField(null=True, default=None)

    USERNAME_FIELD = "username"

    objects = UserAccountManager()

    def save(self, *args, **kwargs):
        if not self.display_name:
            self.display_name = (
                self.email.split("@")[0]
                if self.email and len(self.email.split("@"))
                else "".join(random.choice(string.ascii_letters) for _ in range(6))
            )
        super(User, self).save(*args, **kwargs)

    class Meta:
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ("-created_at",)


class Workspace(TimeStampedModel, CreatorUpdaterModel):
    name = models.CharField(max_length=150, verbose_name="Workspace Name")
    logo = models.FileField(
        upload_to=upload_path, null=True, default=None, validators=[file_size_validator]
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner")
    slug = models.SlugField(
        max_length=48,
        db_index=True,
        unique=True,
        validators=[
            slug_validator,
        ],
    )

    class Meta:
        db_table = "workspace"
        verbose_name = "Workspace"
        verbose_name_plural = "Workspaces"
        unique_together = ("name", "owner")


class WorkspaceMemberInvite(TimeStampedModel, CreatorUpdaterModel):
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
        default=1,
    )
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE)
    responded_at = models.DateTimeField(null=True)
    accepted = models.BooleanField(default=False)

    class Meta:
        db_table = "workspace_member_invite"
        verbose_name = "Workspace Member Invite"
        verbose_name_plural = "Workspace Member Invites"


class WorkspaceMember(TimeStampedModel, CreatorUpdaterModel):
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="member_workspace",
    )
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="workspace_member",
    )
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


class WorkspaceTheme(TimeStampedModel, CreatorUpdaterModel):
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


class WorkspaceUserProperties(TimeStampedModel, CreatorUpdaterModel):
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


class Team(TimeStampedModel, CreatorUpdaterModel):
    name = models.CharField(max_length=255, verbose_name="Team Name")
    description = models.TextField(verbose_name="Team Description", blank=True)
    members = models.ManyToManyField(
        User,
        blank=True,
        related_name="members",
        through="TeamMember",
        through_fields=("team", "member"),
    )
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="workspace_team"
    )

    class Meta:
        unique_together = ["name", "workspace"]
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        db_table = "team"
        ordering = ("-created_at",)


class TeamMember(TimeStampedModel, CreatorUpdaterModel):
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name="team_member"
    )
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="team_member")
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="team_member",
    )

    class Meta:
        unique_together = ["team", "member"]
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"
        db_table = "team_member"
        ordering = ("-created_at",)
