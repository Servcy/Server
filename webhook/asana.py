import json
import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from integration.repository import IntegrationRepository
from integration.services.asana import AsanaService

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def asana(request):
    try:
        if "X-Hook-Secret" in request.headers:
            return HttpResponse(
                status=200, headers={"X-Hook-Secret": request.headers["X-Hook-Secret"]}
            )
        elif "X-Hook-Signature" in request.headers:
            events = json.loads(request.body)
            for event in events:
                if (
                    event["resource"]["resource_type"] == "project"
                    and event["action"] == "added"
                ):
                    user_integration = IntegrationRepository.get_user_integration(
                        {
                            "account_id": event["user"]["gid"],
                            "integration__name": "Asana",
                        }
                    )
                    meta_data = IntegrationRepository.decrypt_meta_data(
                        user_integration.meta_data
                    )
                    AsanaService(
                        refresh_token=meta_data["token"]["refresh_token"]
                    ).create_project_webhook(event["resource"]["gid"])
                if event["resource"]["resource_type"] == "task":
                    user_integration = IntegrationRepository.get_user_integration(
                        {
                            "account_id": event["user"]["gid"],
                            "integration__name": "Asana",
                        }
                    )
                    meta_data = IntegrationRepository.decrypt_meta_data(
                        user_integration.meta_data
                    )
                    action = event["action"]
                    task_id = event["resource"]["gid"]
                    change = None
                    if action == "changed":
                        changes = event["change"]
                        for change in changes:
                            logger.info(
                                f"{change['field']} {change['action']} for task: {task_id}"
                            )
                    else:
                        logger.info(f"Task {action}: {task_id}")
            logger.info("Asana webhook received.", extra={"body": request.body})
            return HttpResponse(
                status=200, content="OK", content_type="application/json"
            )
        else:
            logger.warning(
                f"Received an unknown request from Asana webhook.",
                extra={"body": request.body, "headers": request.headers},
            )
            return HttpResponse(status=400, content="Bad Request")
    except Exception as err:
        logger.exception(
            f"An error occurred while processing asana webhook.",
            exc_info=True,
            extra={"body": request.body, "headers": request.headers},
        )
        return HttpResponse(status=500, content="Internal Server Error")
