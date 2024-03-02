from django.core.exceptions import ValidationError

INVALID_SLUGS = [
    "404",
    "accounts",
    "api",
    "create-workspace",
    "god-mode",
    "installations",
    "invitations",
    "onboarding",
    "profile",
    "spaces",
    "workspace-invitations",
    "password",
]


def slug_validator(value):
    if value in INVALID_SLUGS:
        raise ValidationError("Slug is not valid")
