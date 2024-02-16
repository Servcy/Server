from integration.services import (
    AsanaService,
    FigmaService,
    GithubService,
    GoogleService,
    MicrosoftService,
    NotionService,
    SlackService,
    TrelloService,
    JiraService,
)

integration_service_map = {
    "Gmail": GoogleService,
    "Github": GithubService,
    "Slack": SlackService,
    "Notion": NotionService,
    "Figma": FigmaService,
    "Outlook": MicrosoftService,
    "Asana": AsanaService,
    "Jira": JiraService,
    "Trello": TrelloService,
}
