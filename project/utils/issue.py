from iam.enums import ERole
from project.models import Issue, IssueLink, ProjectMember


def get_issue_link_details_from_github_event(event: dict, commit_map: dict):
    """
    Get the issue link from the github event.
    """
    link = ""
    title = ""
    if event.get("action") == "synchronize":
        commit_sha = event.get("after")
        commit_message = commit_map.get(commit_sha)
        title = f"Commit: {commit_message}"
        link = f"{event.get('repository', {}).get('html_url')}/commit/{commit_sha}"
    else:
        pr_title = event.get("pull_request", {}).get("title")
        title = f"PR: {pr_title}"
        link = event.get("pull_request", {}).get("html_url")
    return title, link


def parse_github_events_into_issue_links(
    event: dict, possible_issue_identifiers: set, user_id: int, commit_map: dict
):
    """
    Parse the github events into issue links.
    Note: User should be a member of the project
    """
    valid_issue_identifiers = []
    for identifier in possible_issue_identifiers:
        try:
            if identifier in valid_issue_identifiers:
                continue
            project_identifier = identifier.split("-")[0]
            issue_sequence_id = identifier.split("-")[1]
            if (
                Issue.objects.filter(
                    project__identifier=project_identifier,
                    project__archived_at__isnull=True,
                    sequence_id=int(issue_sequence_id),
                    is_draft=False,
                    archived_at__isnull=True,
                ).exists()
                and ProjectMember.objects.filter(
                    project__archived_at__isnull=True,
                    project__identifier=project_identifier,
                    member_id=user_id,
                    is_active=True,
                    role__lt=ERole.MEMBER.value,
                ).exists()
            ):
                valid_issue_identifiers.append(identifier)
        except IndexError:
            continue
        except ValueError:
            continue
    issue_links = []
    for identifier in valid_issue_identifiers:
        project_identifier = identifier.split("-")[0]
        issue_sequence_id = int(identifier.split("-")[1])
        link_title, link_url = get_issue_link_details_from_github_event(
            event, commit_map
        )
        if IssueLink.objects.filter(
            project__identifier=project_identifier,
            issue__sequence_id=issue_sequence_id,
            url=link_url,
        ).exists():
            continue
        issue = Issue.objects.get(
            project__identifier=project_identifier, sequence_id=issue_sequence_id
        )
        project = issue.project
        workspace = issue.workspace
        issue_links.append(
            IssueLink(
                project_id=project.id,
                workspace_id=workspace.id,
                issue_id=issue.id,
                url=link_url,
                title=link_title,
                created_by_id=user_id,
                updated_by_id=user_id,
            )
        )
    IssueLink.objects.bulk_create(issue_links)
