from uuid import uuid4

from django.core.exceptions import ValidationError

from django.conf import settings


def upload_path(instance, filename):
    """
    Note: instance must have a workspace attribute.
    """
    base = "Production" if settings.DEBUG is False else "Development"
    return (
        f"{base}/Documents/workspace/{instance.workspace.id}/{uuid4().hex}-{filename}"
        if instance.workspace
        else f"{base}/Documents/user/{instance.created_by.id}/{uuid4().hex}-{filename}"
    )


def file_size_validator(value):
    """
    Note: value is the file itself.
    """
    if value.size > 5 * 1024 * 1024:
        raise ValidationError("File too large. Size should not exceed 5 MB.")
