import json
import logging
import traceback
import uuid

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from common.exceptions import (
    ExternalIntegrationException,
    IntegrationAccessRevokedException,
)
from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.repository.events import DisabledUserIntegrationEventRepository
from integration.services.asana import AsanaService
from integration.utils.events import is_event_and_action_disabled

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def asana(request, user_integration_id):
    try:
        body = json.loads(request.body)
        headers = request.headers
        if "X-Hook-Secret" in headers:
            return HttpResponse(
                status=200, headers={"X-Hook-Secret": headers["X-Hook-Secret"]}
            )
        elif "X-Hook-Signature" in headers:
            events = body.get("events")
            user_integration = None
            meta_data = None
            asana_service = None
            inbox_items = []
            revoked_user_integrations = []
            disabled_events = DisabledUserIntegrationEventRepository.get_disabled_user_integration_events(
                user_integration_id=user_integration_id
            )
            for event in events:
                if (
                    event.get("action", "") == "sync_error"
                    or event["user"]["gid"] is None
                ):
                    continue
                if user_integration is None:
                    user_integration = IntegrationRepository.get_user_integration(
                        {
                            "id": user_integration_id,
                            "integration__name": "Asana",
                        }
                    )
                    meta_data = IntegrationRepository.decrypt_meta_data(
                        user_integration.meta_data
                    )
                    try:
                        asana_service = AsanaService(
                            refresh_token=meta_data["token"]["refresh_token"]
                        )
                    except IntegrationAccessRevokedException:
                        revoked_user_integrations.append({user_integration})
                        continue
                causing_user = asana_service.get_user(event["user"]["gid"])
                if event["resource"]["resource_type"] == "project":
                    action = event["action"]
                    project_uid = event["resource"]["gid"]
                    project = asana_service.get_project(project_uid)
                    if not is_event_and_action_disabled(
                        disabled_events, event["resource"]["resource_type"], action
                    ):
                        inbox_items.append(
                            {
                                "uid": str(uuid.uuid4()),
                                "title": f"Project {project['name']} {action}",
                                "body": json.dumps(
                                    {
                                        "project": project,
                                        **event,
                                    }
                                ),
                                "cause": json.dumps(causing_user),
                                "user_integration_id": user_integration_id,
                                "category": "notification",
                            }
                        )
                    if action == "added":
                        asana_service.create_task_monitoring_webhook(
                            project_uid, user_integration_id
                        )
                elif event["resource"]["resource_type"] == "task":
                    action = event["action"]
                    task_uid = event["resource"]["gid"]
                    try:
                        task = asana_service.get_task(task_uid)
                    except ExternalIntegrationException:
                        continue
                    if not is_event_and_action_disabled(
                        disabled_events, event["resource"]["resource_type"], action
                    ):
                        i_am_following = False
                        for follower in task["followers"]:
                            if follower["gid"] == user_integration.account_id:
                                i_am_following = True
                                break
                        inbox_items.append(
                            {
                                "uid": str(uuid.uuid4()),
                                "title": f"Task {task['name']} {action}",
                                "body": json.dumps(
                                    {
                                        "task": task,
                                        **event,
                                    }
                                ),
                                "cause": json.dumps(causing_user),
                                "user_integration_id": user_integration_id,
                                "category": "notification",
                                "i_am_mentioned": i_am_following,
                            }
                        )
                elif (
                    event["resource"]["resource_type"] == "story"
                    and event["resource"]["resource_subtype"] == "comment_added"
                ):
                    action = event.get("action", "")
                    comment = asana_service.get_story(event["resource"]["gid"])
                    task = None
                    if action == "added":
                        try:
                            task = asana_service.get_task(event["parent"]["gid"])
                        except ExternalIntegrationException:
                            continue
                        title = f"Comment added to task: {task['name']}"
                    elif action == "changed":
                        title = "A comment on the task was updated"
                    if not is_event_and_action_disabled(
                        disabled_events, event["resource"]["resource_type"], action
                    ):
                        i_am_mentioned = False
                        for text in comment["text"].split(" "):
                            # is text a mention? i.e. https://app.asana.com/0/1205704174798989/list
                            if text.startswith(
                                "https://app.asana.com/0/"
                            ) and text.endswith("/list"):
                                project_id = text.split("/")[-2]
                                project = asana_service.get_project(project_id)
                                if (
                                    project["owner"]["gid"]
                                    == user_integration.account_id
                                ):
                                    i_am_mentioned = True
                                    break
                        inbox_items.append(
                            {
                                "uid": str(uuid.uuid4()),
                                "title": title,
                                "body": json.dumps(
                                    {
                                        "comment": comment,
                                        **event,
                                    }
                                ),
                                "cause": json.dumps(causing_user),
                                "user_integration_id": user_integration_id,
                                "category": "comment",
                                "i_am_mentioned": i_am_mentioned,
                            }
                        )
                else:
                    logger.warning(
                        f"Received an unknown event from Asana webhook.",
                        extra={
                            "event": event,
                            "user_integration_id": user_integration_id,
                        },
                    )
            for revoked_user_integration in revoked_user_integrations:
                inbox_items.append(
                    {
                        "title": f"An integration has been revoked, please re-authenticate.",
                        "cause": None,
                        "body": f"""<div style="margin-left: 10px; font-family: monospace;"><table><tr><td>Integration Name</td><td style="padding-left: 16px; font-weight: 600;">{revoked_user_integration.integration.name}</td></tr><tr><td>Account</td><td style="padding-left: 16px; font-weight: 600;">{revoked_user_integration.account_display_name}</td></tr></table><div style="margin: 10px 0;"><a style="color: #26542F; text-decoration: underline;" href="{settings.FRONTEND_URL}/integrations?integration={revoked_user_integration.integration.id}">Click here</a> to re-authenticate.</div></div>""",
                        "is_body_html": True,
                        "user_integration_id": revoked_user_integration.id,
                        "uid": str(uuid.uuid4()),
                        "category": "notification",
                        "i_am_mentioned": True,
                    }
                )
            with transaction.atomic():
                IntegrationRepository.revoke_user_integrations(
                    [
                        revoked_user_integration.id
                        for revoked_user_integration in revoked_user_integrations
                    ]
                )
                InboxRepository.add_items(inbox_items)
            return HttpResponse(
                status=200, content="OK", content_type="application/json"
            )
        else:
            logger.warning(
                f"Received an unknown request from Asana webhook.",
                extra={
                    "body": body,
                    "headers": headers,
                    "user_integration_id": user_integration_id,
                },
            )
            return HttpResponse(status=200, content="OK")
    except Exception:
        logger.exception(
            f"An error occurred while processing asana webhook.",
            extra={
                "body": body,
                "headers": headers,
                "traceback": traceback.format_exc(),
                "user_integration_id": user_integration_id,
            },
        )
        return HttpResponse(status=500, content="Internal Server Error")
