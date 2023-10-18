import json
import logging
import traceback

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from slack_sdk import WebClient

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository

logger = logging.getLogger(__name__)

EVENT_MAP = {
    "app_home_opened": "User clicked into your App Home",
    "app_mention": "Subscribe to only the message events that mention your app or bot",
    "app_rate_limited": "Indicates your app's event subscriptions are being rate limited",
    "app_requested": "User requested an app",
    "app_uninstalled": "Your Slack app was uninstalled.",
    "call_rejected": "A Call was rejected",
    "channel_archive": "A channel was archived",
    "channel_created": "A channel was created",
    "channel_deleted": "A channel was deleted",
    "channel_history_changed": "Bulk updates were made to a channel's history",
    "channel_id_changed": "A channel ID changed",
    "channel_left": "You left a channel",
    "channel_rename": "A channel was renamed",
    "channel_shared": "A channel has been shared with an external workspace",
    "channel_unarchive": "A channel was unarchived",
    "channel_unshared": "A channel has been unshared with an external workspace",
    "dnd_updated": "Do not Disturb settings changed for the current user",
    "dnd_updated_user": "Do not Disturb settings changed for a member",
    "email_domain_changed": "The workspace email domain has changed",
    "emoji_changed": "A custom emoji has been added or changed",
    "file_change": "A file was changed",
    "file_comment_added": "A file comment was added",
    "file_comment_deleted": "A file comment was deleted",
    "file_comment_edited": "A file comment was edited",
    "file_created": "A file was created",
    "file_deleted": "A file was deleted",
    "file_public": "A file was made public",
    "file_shared": "A file was shared",
    "file_unshared": "A file was unshared",
    "grid_migration_finished": "An enterprise grid migration has finished on this workspace.",
    "grid_migration_started": "An enterprise grid migration has started on this workspace.",
    "group_archive": "A private channel was archived",
    "group_close": "You closed a private channel",
    "group_deleted": "A private channel was deleted",
    "group_history_changed": "Bulk updates were made to a private channel's history",
    "group_left": "You left a private channel",
    "group_open": "You created a group DM",
    "group_rename": "A private channel was renamed",
    "group_unarchive": "A private channel was unarchived",
    "im_close": "You closed a DM",
    "im_created": "A DM was created",
    "im_history_changed": "Bulk updates were made to a DM's history",
    "im_open": "You opened a DM",
    "invite_requested": "User requested an invite",
    "link_shared": "A message was posted containing one or more links relevant to your application",
    "member_joined_channel": "A user joined a public channel, private channel or MPDM.",
    "member_left_channel": "A user left a public or private channel",
    "message": "A message was sent to a channel",
    "message.app_home": "A user sent a message to your Slack app",
    "message.channels": "A message was posted to a channel",
    "message.groups": "A message was posted to a private channel",
    "message.im": "A message was posted in a direct message channel",
    "message.mpim": "A message was posted in a multiparty direct message channel",
    "message_metadata_deleted": "Message metadata was deleted",
    "message_metadata_posted": "Message metadata was posted",
    "message_metadata_updated": "Message metadata was updated",
    "pin_added": "A pin was added to a channel",
    "pin_removed": "A pin was removed from a channel",
    "reaction_added": "A member has added an emoji reaction to an item",
    "reaction_removed": "A member removed an emoji reaction",
    "scope_denied": "OAuth scopes were denied to your app",
    "scope_granted": "OAuth scopes were granted to your app",
    "shared_channel_invite_accepted": "A shared channel invite was accepted",
    "shared_channel_invite_approved": "A shared channel invite was approved",
    "shared_channel_invite_declined": "A shared channel invite was declined",
    "shared_channel_invite_received": "A shared channel invite was sent to a Slack user",
    "star_added": "A member has saved an item for later or starred an item",
    "star_removed": "A member has removed an item saved for later or starred an item",
    "subteam_created": "A User Group has been added to the workspace",
    "subteam_members_changed": "The membership of an existing User Group has changed",
    "subteam_self_added": "You have been added to a User Group",
    "subteam_self_removed": "You have been removed from a User Group",
    "subteam_updated": "An existing User Group has been updated or its members changed",
    "team_access_granted": "Access to a set of teams was granted to your org app",
    "team_access_revoked": "Access to a set of teams was revoked from your org app",
    "team_domain_change": "The workspace domain has changed",
    "team_join": "A new member has joined",
    "team_rename": "The workspace name has changed",
    "tokens_revoked": "API tokens for your app were revoked.",
    "url_verification": "Verifies ownership of an  Request URL",
    "user_change": "A member's data has changed",
    "user_huddle_changed": "A user's huddle status has changed",
    "user_profile_changed": "A user's profile data has changed",
    "user_resource_denied": "User resource was denied to your app",
    "user_resource_granted": "User resource was granted to your app",
    "user_resource_removed": "User resource was removed from your app",
    "user_status_changed": "A user's status has changed",
    "workflow_deleted": "A workflow that contains a step supported by your app was deleted",
    "workflow_published": "A workflow that contains a step supported by your app was published",
    "workflow_step_deleted": "A workflow step supported by your app was removed from a workflow",
    "workflow_step_execute": "A workflow step supported by your app should execute",
    "workflow_unpublished": "A workflow that contains a step supported by your app was unpublished",
}


@csrf_exempt
@require_POST
def slack(request):
    try:
        body = json.loads(request.body)
        headers = request.headers
        if body["type"] == "url_verification":
            return HttpResponse(body["challenge"])
        if body["token"] != settings.SLACK_APP_VERIFICATION_TOKEN:
            return HttpResponse(status=400)
        event_authorizations = WebClient(
            settings.SLACK_APP_TOKEN
        ).apps_event_authorizations_list(event_context=body["event_context"])
        if event_authorizations["ok"] != True:
            return HttpResponse(status=400)
        uid = body["event_id"]
        user_integrations = IntegrationRepository.get_user_integrations(
            {
                "account_id__in": [
                    account["user_id"]
                    for account in event_authorizations["authorizations"]
                ],
                "integration__name": "Slack",
            }
        )
        inbox_items = []
        members = user_integrations[0]["configuration"] or []
        cause = "-"
        for member in members:
            if member.get("id", None) == body["event"]["user"]:
                cause = member["profile"]
        for user_integration in user_integrations:
            workspace_members = user_integration["configuration"] or []
            event_body = body["event"]
            try:
                mentions = [
                    mention[2:-1]
                    for mention in event_body.get("text", "").split()
                    if mention.startswith("<@") and mention.endswith(">")
                ]
            except:
                mentions = []
            event_body["x-servcy-mentions"] = [
                member
                for member in workspace_members
                if member.get("id", None) in mentions
            ]
            inbox_items.append(
                {
                    "title": EVENT_MAP[body["event"]["type"]],
                    "cause": json.dumps(cause),
                    "body": json.dumps(event_body),
                    "is_body_html": False,
                    "user_integration_id": user_integration["id"],
                    "uid": f"{uid}-{user_integration['id']}",
                    "category": "message"
                    if body["event"].get("type", "").startswith("message")
                    else "notification",
                }
            )
        InboxRepository.add_items(inbox_items)
        return HttpResponse(status=200)
    except Exception:
        logger.exception(
            f"An error occurred while processing slack webhook.",
            extra={
                "body": body,
                "headers": headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500)
