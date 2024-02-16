from integration.services import (
    AsanaService,
    FigmaService,
    GithubService,
    GoogleService,
    MicrosoftService,
    NotionService,
    SlackService,
    TrelloService,
    AtlassianService,
)

integration_service_map = {
    "Gmail": GoogleService,
    "Github": GithubService,
    "Slack": SlackService,
    "Notion": NotionService,
    "Figma": FigmaService,
    "Outlook": MicrosoftService,
    "Asana": AsanaService,
    "Atlassian": AtlassianService,
    "Trello": TrelloService,
}
