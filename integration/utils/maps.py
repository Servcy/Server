from integration.services import (
    AsanaService,
    FigmaService,
    GithubService,
    GoogleService,
    MicrosoftService,
    NotionService,
    SlackService,
    TrelloService,
)

integration_service_map = {
    "Gmail": GoogleService,
    "GitHub": GithubService,
    "Slack": SlackService,
    "Notion": NotionService,
    "Figma": FigmaService,
    "Outlook": MicrosoftService,
    "Asana": AsanaService,
    "Trello": TrelloService,
}