from django.urls import path

from webhook.asana import asana
from webhook.figma import figma
from webhook.github import github
from webhook.google import google
from webhook.microsoft import microsoft
from webhook.slack import slack
from webhook.trello import trello

urlpatterns = [
    path("microsoft", microsoft, name="Microsoft"),
    path("google", google, name="Google"),
    path("slack", slack, name="Slack"),
    path("figma", figma, name="Figma"),
    path("github", github, name="Github"),
    path("asana/<int:user_integration_id>", asana, name="Asana"),
    path("trello/<int:user_integration_id>", trello, name="Trello"),
]
