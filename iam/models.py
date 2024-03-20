from enum import unique
import random
import string

import pytz
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from app.models import CreatorUpdaterModel, TimeStampedModel
from common.validators import slug_validator
from iam.managers import UserAccountManager
from mails import SendGridEmail


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
    logo = models.URLField(blank=False, null=True, default=None)
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
            (2, "Admin"),
            (1, "Member"),
            (0, "Guest"),
        ),
        default=1,
    )
    view_props = models.JSONField(default=dict)
    default_props = models.JSONField(default=dict)
    issue_props = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "workspace_member"
        unique_together = ("member", "workspace")
        verbose_name = "Workspace Member"
        verbose_name_plural = "Workspace Members"


@receiver(post_save, sender=WorkspaceMemberInvite)
def create_issue_sequence(sender, instance, created, **kwargs):
    if created:
        workspace = instance.workspace
        invited_by = instance.invited_by
        if not workspace or not invited_by:
            return
        SendGridEmail(to_email=instance.email).send_workspace_invitation(
            workspace_name=workspace.name,
            user_name=invited_by.first_name or invited_by.email,
            invite_link=f"{settings.FRONTEND_URL}/workspace/invite/?invitation_id={instance.id}&email={instance.email}&slug={workspace.slug}",
        )
    return
