import json
import logging
import traceback
import uuid

from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from inbox.repository import InboxRepository
from integration.repository import IntegrationRepository
from integration.services.asana import AsanaService
from project.repository import ProjectRepository
from task.repository import TaskRepository

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
            projects_to_create = []
            tasks_to_create = []
            tasks_to_delete = []
            tasks_to_undelete = []
            projects_to_delete = []
            projects_to_undelete = []
            asana_service = None
            tasks_to_update = []
            inbox_items = []
            projects_to_update = []
            for event in events:
                if user_integration is None and event["user"]["gid"] is not None:
                    user_integration = IntegrationRepository.get_user_integration(
                        {
                            "id": user_integration_id,
                            "integration__name": "Asana",
                        }
                    )
                    meta_data = IntegrationRepository.decrypt_meta_data(
                        user_integration.meta_data
                    )
                    asana_service = AsanaService(
                        refresh_token=meta_data["token"]["refresh_token"]
                    )
                elif event["user"]["gid"] is None:
                    raise Exception(
                        f"Received an event with no user gid from Asana webhook.",
                        extra={"event": event},
                    )
                if event["resource"]["resource_type"] == "project":
                    action = event["action"]
                    project_uid = event["resource"]["gid"]
                    project = asana_service.get_project(project_uid)
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
                            "cause": event["user"]["name"],
                            "user_integration_id": user_integration_id,
                            "category": "project",
                        }
                    )
                    if action == "added":
                        asana_service.create_task_monitoring_webhook(project_uid)
                        projects_to_create.append(project)
                    if action == "changed":
                        projects_to_update.append(project)
                    if action in ["removed", "deleted"]:
                        projects_to_delete.append(project)
                    if action == "undeleted":
                        projects_to_undelete.append(project)
                elif event["resource"]["resource_type"] == "task":
                    action = event["action"]
                    task_uid = event["resource"]["gid"]
                    task = asana_service.get_task(task_uid)
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
                            "cause": event["user"]["name"],
                            "user_integration_id": user_integration_id,
                            "category": "project",
                        }
                    )
                    if action == "changed":
                        tasks_to_update.append(task)
                    elif action == "added":
                        tasks_to_create.append(task)
                    elif action in ["removed", "deleted"]:
                        tasks_to_delete.append(task)
                    elif action == "undeleted":
                        tasks_to_undelete.append(task)
                elif (
                    event["resource"]["resource_type"] == "story"
                    and event["resource"]["resource_subtype"] == "comment_added"
                ):
                    inbox_items.append(
                        {
                            "uid": str(uuid.uuid4()),
                            "title": f"Comment added to task {event['resource']['name']}",
                            "body": json.dumps(event),
                            "cause": event["user"]["name"],
                            "user_integration_id": user_integration_id,
                            "category": "comment",
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
            with transaction.atomic():
                if tasks_to_delete:
                    TaskRepository.delete_bulk(
                        user_integration.user.id,
                        [
                            task["gid"]
                            for task in tasks_to_delete
                            if task["gid"] is not None
                        ],
                    )
                if tasks_to_update:
                    TaskRepository.update_bulk(
                        [
                            {
                                "uid": task["gid"],
                                "name": task["name"],
                                "description": task["notes"],
                                "meta_data": task,
                            }
                            for task in tasks_to_update
                        ]
                    )
                if tasks_to_undelete:
                    TaskRepository.undelete(
                        [
                            task["gid"]
                            for task in tasks_to_undelete
                            if task["gid"] is not None
                        ]
                    )
                if projects_to_delete:
                    ProjectRepository.delete_bulk(
                        [
                            project["gid"]
                            for project in projects_to_delete
                            if project["gid"] is not None
                        ]
                    )
                if projects_to_undelete:
                    ProjectRepository.undelete(
                        [
                            project["gid"]
                            for project in projects_to_undelete
                            if project["gid"] is not None
                        ]
                    )
                if projects_to_update:
                    ProjectRepository.update_bulk(
                        [
                            {
                                "uid": project["gid"],
                                "name": project["name"],
                                "description": project["notes"],
                                "meta_data": project,
                            }
                            for project in projects_to_update
                        ]
                    )
                for project in projects_to_create:
                    ProjectRepository.create(
                        uid=project["gid"],
                        user_integration_id=user_integration.id,
                        user_id=user_integration.user.id,
                        name=project["name"],
                        description=project["notes"],
                        meta_data=project,
                    )
                for task in tasks_to_create:
                    TaskRepository.create(
                        uid=task["gid"],
                        name=task["name"],
                        description=task["notes"],
                        project_uid=task["projects"][0]["gid"],
                        user_id=user_integration.user.id,
                        meta_data=task,
                    )
                InboxRepository.add_items(inbox_items)
            logger.info(
                "Asana webhook received.",
                extra={
                    "body": request.body,
                    "user_integration_id": user_integration_id,
                },
            )
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
            return HttpResponse(status=400, content="Bad Request")
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
