from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models

from app.models import TimeStampedModel
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
    is_active = models.BooleanField(default=False)
    profile_image = models.FileField(upload_to="ProfileImages", null=True)

    invited_by = models.ForeignKey(
        "self",
        default=None,
        null=True,
        on_delete=models.PROTECT,
    )

    USERNAME_FIELD = "username"

    objects = UserAccountManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = "user"
        verbose_name = "User"
        verbose_name_plural = "Users"
