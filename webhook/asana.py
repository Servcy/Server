import json
import logging
import traceback

from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from integration.repository import IntegrationRepository
from integration.services.asana import AsanaService
from project.models import Project
from project.repository import ProjectRepository
from task.models import Task
from task.repository import TaskRepository

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def asana(request):
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
            asana_service = None
            tasks_to_update = []
            for event in events:
                if user_integration is None and event["user"]["gid"] is not None:
                    user_integration = IntegrationRepository.get_user_integration(
                        {
                            "account_id": event["user"]["gid"],
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
                if (
                    event["resource"]["resource_type"] == "project"
                    and event["action"] == "added"
                ):
                    asana_service.create_task_monitoring_webhook(
                        event["resource"]["gid"]
                    )
                    projects_to_create.append(
                        asana_service.get_project(event["resource"]["gid"])
                    )
                elif event["resource"]["resource_type"] == "task":
                    action = event["action"]
                    task_id = event["resource"]["gid"]
                    change = None
                    task = asana_service.get_task(task_id)
                    if action == "changed":
                        changes = event["change"]
                        tasks_to_update.append(task)
                        for change in changes:
                            logger.info(
                                f"{change['field']} {change['action']} for task: {task_id}"
                            )
                    if action == "added":
                        tasks_to_create.append(task)
                    if action in ["removed", "deleted"]:
                        tasks_to_delete.append(task)
                    if action == "undeleted":
                        tasks_to_undelete.append(task)
                else:
                    logger.warning(
                        f"Received an unknown event from Asana webhook.",
                        extra={"event": event},
                    )
            with transaction.atomic():
                if tasks_to_delete:
                    TaskRepository.delete_bulk(
                        [
                            task["gid"]
                            for task in tasks_to_delete
                            if task["gid"] is not None
                        ]
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
                if projects_to_create and user_integration:
                    ProjectRepository.create_bulk(
                        [
                            Project(
                                name=project["name"],
                                description=project["notes"],
                                uid=project["gid"],
                                user=user_integration.user,
                                user_integration=user_integration,
                                meta_data=project,
                            )
                            for project in projects_to_create
                        ]
                    )
                if tasks_to_create and user_integration:
                    TaskRepository.create_bulk(
                        [
                            Task(
                                uid=task["gid"],
                                name=task["name"],
                                description=task["notes"],
                                project_uid=task["projects"][0]["gid"],
                                user=user_integration.user,
                                meta_data=task,
                            )
                            for task in tasks_to_create
                        ],
                    )
            logger.info("Asana webhook received.", extra={"body": request.body})
            return HttpResponse(
                status=200, content="OK", content_type="application/json"
            )
        else:
            logger.warning(
                f"Received an unknown request from Asana webhook.",
                extra={"body": body, "headers": headers},
            )
            return HttpResponse(status=400, content="Bad Request")
    except Exception:
        logger.exception(
            f"An error occurred while processing asana webhook.",
            extra={
                "body": body,
                "headers": headers,
                "traceback": traceback.format_exc(),
            },
        )
        return HttpResponse(status=500, content="Internal Server Error")
