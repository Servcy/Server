from django.urls import path

from webhook.figma import figma
from webhook.github import github
from webhook.google import google
from webhook.microsoft import microsoft
from webhook.slack import slack

urlpatterns = [
    path("microsoft", microsoft, name="Microsoft"),
    path("google", google, name="Google"),
    path("slack", slack, name="Slack"),
    path("figma", figma, name="Figma"),
    path("github", github, name="Github"),
]
