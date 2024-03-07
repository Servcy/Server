import logging
import traceback
from datetime import datetime

from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from app.utils.redis import create_redis_instance
from iam.models import User
from mails import SendGridEmail
from notification.models import EmailNotificationLog
from project.models import Issue

logger = logging.getLogger(__name__)


def acquire_lock(lock_id, expire_time=300):
    redis_client = create_redis_instance()
    """Attempt to acquire a lock with a specified expiration time."""
    return redis_client.set(lock_id, "true", nx=True, ex=expire_time)


def release_lock(lock_id):
    """Release a lock."""
    redis_client = create_redis_instance()
    redis_client.delete(lock_id)


def create_payload(notification_data):
    """
    This function is used to create the payload for the email notification
    :return: payload

    - payload: This is a dictionary that contains the changes made to the issue and the user that made the changes
    - payload contains the following keys:
        - actor_id: This is the user that made the changes
        - key: This is the field that was changed
        - old_value: This is the old value of the field
        - new_value: This is the new value of the field
    """
    data = {}
    for actor_id, changes in notification_data.items():
        for change in changes:
            issue_activity = change.get("issue_activity")
            if issue_activity:  # Ensure issue_activity is not None
                field = issue_activity.get("field")
                old_value = str(issue_activity.get("old_value"))
                new_value = str(issue_activity.get("new_value"))

                # Append old_value if it's not empty and not already in the list
                if old_value:
                    (
                        data.setdefault(actor_id, {})
                        .setdefault(field, {})
                        .setdefault("old_value", [])
                        .append(old_value)
                        if old_value
                        not in data.setdefault(actor_id, {})
                        .setdefault(field, {})
                        .get("old_value", [])
                        else None
                    )

                # Append new_value if it's not empty and not already in the list
                if new_value:
                    (
                        data.setdefault(actor_id, {})
                        .setdefault(field, {})
                        .setdefault("new_value", [])
                        .append(new_value)
                        if new_value
                        not in data.setdefault(actor_id, {})
                        .setdefault(field, {})
                        .get("new_value", [])
                        else None
                    )

                if not data.get("actor_id", {}).get("activity_time", False):
                    data[actor_id]["activity_time"] = str(
                        datetime.fromisoformat(
                            issue_activity.get("activity_time").rstrip("Z")
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    )

    return data


def process_mention(mention_component):
    soup = BeautifulSoup(mention_component, "html.parser")
    mentions = soup.find_all("mention-component")
    for mention in mentions:
        user_id = mention["id"]
        user = User.objects.get(pk=user_id)
        user_name = user.display_name
        highlighted_name = f"@{user_name}"
        mention.replace_with(highlighted_name)
    return str(soup)


def process_html_content(content):
    processed_content_list = []
    for html_content in content:
        processed_content = process_mention(html_content)
        processed_content_list.append(processed_content)
    return processed_content_list


def send_email_notification(
    issue_id, notification_data, receiver_id, email_notification_ids
):
    """
    This function is used to send the email notification to the receiver
    :param issue_id: This is the id of the issue
    :param notification_data: This is the data that contains the changes made to the issue
    :param receiver_id: This is the id of the user that will receive the email notification
    :param email_notification_ids: This is the list of email notification ids
    :return: None
    """
    # Convert UUIDs to a sorted, concatenated string
    sorted_ids = sorted(email_notification_ids)
    ids_str = "_".join(str(id) for id in sorted_ids)
    lock_id = f"send_email_notif_{issue_id}_{receiver_id}_{ids_str}"
    # acquire the lock for sending emails
    try:
        if acquire_lock(lock_id=lock_id):
            # get the redis instance
            redis_instance = create_redis_instance()
            base_api = redis_instance.get(str(issue_id)).decode()
            data = create_payload(notification_data=notification_data)
            receiver = User.objects.get(pk=receiver_id)
            issue = Issue.objects.get(pk=issue_id)
            template_data = []
            total_changes = 0
            comments = []
            actors_involved = []
            for actor_id, changes in data.items():
                actor = User.objects.get(pk=actor_id)
                total_changes = total_changes + len(changes)
                comment = changes.pop("comment", False)
                mention = changes.pop("mention", False)
                actors_involved.append(actor_id)
                if comment:
                    comments.append(
                        {
                            "actor_comments": comment,
                            "actor_detail": {
                                "avatar_url": actor.avatar,
                                "first_name": actor.first_name,
                                "last_name": actor.last_name,
                            },
                        }
                    )
                if mention:
                    mention["new_value"] = process_html_content(
                        mention.get("new_value")
                    )
                    mention["old_value"] = process_html_content(
                        mention.get("old_value")
                    )
                    comments.append(
                        {
                            "actor_comments": mention,
                            "actor_detail": {
                                "avatar_url": actor.avatar,
                                "first_name": actor.first_name,
                                "last_name": actor.last_name,
                            },
                        }
                    )
                activity_time = changes.pop("activity_time")
                # Parse the input string into a datetime object
                formatted_time = datetime.strptime(
                    activity_time, "%Y-%m-%d %H:%M:%S"
                ).strftime("%H:%M %p")

                if changes:
                    template_data.append(
                        {
                            "actor_detail": {
                                "avatar_url": actor.avatar,
                                "first_name": actor.first_name,
                                "last_name": actor.last_name,
                            },
                            "changes": changes,
                            "issue_details": {
                                "name": issue.name,
                                "identifier": f"{issue.project.identifier}-{issue.sequence_id}",
                            },
                            "activity_time": str(formatted_time),
                        }
                    )
            summary = "Updates were made to the issue by"
            # Send the mail
            subject = f"{issue.project.identifier}-{issue.sequence_id} {issue.name}"
            context = {
                "data": template_data,
                "summary": summary,
                "actors_involved": len(set(actors_involved)),
                "issue": {
                    "issue_identifier": f"{str(issue.project.identifier)}-{str(issue.sequence_id)}",
                    "name": issue.name,
                    "issue_url": f"{base_api}/{str(issue.project.workspace.slug)}/projects/{str(issue.project.id)}/issues/{str(issue.id)}",
                },
                "receiver": {
                    "email": receiver.email,
                },
                "issue_url": f"{base_api}/{str(issue.project.workspace.slug)}/projects/{str(issue.project.id)}/issues/{str(issue.id)}",
                "project_url": f"{base_api}/{str(issue.project.workspace.slug)}/projects/{str(issue.project.id)}/issues/",
                "workspace": str(issue.project.workspace.slug),
                "project": str(issue.project.name),
                "user_preference": f"{base_api}/profile/preferences/email",
                "comments": comments,
            }
            html_content = render_to_string("issue-activity-mail.html", context)
            text_content = strip_tags(html_content)
            try:
                SendGridEmail(receiver.email).send_issue_activity(
                    subject=subject,
                    body=text_content,
                    media_type="text/html",
                )
                EmailNotificationLog.objects.filter(
                    pk__in=email_notification_ids
                ).update(sent_at=timezone.now())
                # release the lock
                release_lock(lock_id=lock_id)
            except Exception as e:
                logger.exception(
                    f"An error occurred while sending email notification to {receiver.email}",
                    extra={
                        "receiver_email": receiver.email,
                        "traceback": traceback.format_exc(),
                    },
                    exc_info=True,
                )
                # release the lock
                release_lock(lock_id=lock_id)
        else:
            logger.warning(
                f"Failed to acquire lock for sending email notification to {receiver.email}",
                extra={
                    "issue_id": issue_id,
                    "notification_data": notification_data,
                    "receiver_id": receiver_id,
                    "email_notification_ids": email_notification_ids,
                },
            )
    except (Issue.DoesNotExist, User.DoesNotExist) as e:
        logger.exception(
            f"An error occurred while sending email notification to {receiver.email}",
            extra={
                "issue_id": issue_id,
                "notification_data": notification_data,
                "receiver_id": receiver_id,
                "email_notification_ids": email_notification_ids,
                "traceback": traceback.format_exc(),
            },
            exc_info=True,
        )
        release_lock(lock_id=lock_id)


def main():
    """
    This function is used to stack all the email notifications and send them in a single email
    """
    # get all email notifications
    email_notifications = (
        EmailNotificationLog.objects.filter(processed_at__isnull=True)
        .order_by("receiver")
        .values()
    )
    # Convert to unique receivers list
    receivers = list(
        set(
            [
                str(notification.get("receiver_id"))
                for notification in email_notifications
            ]
        )
    )
    processed_notifications = []
    # Loop through all the issues to create the emails
    for receiver_id in receivers:
        # Notification triggered for the receiver
        receiver_notifications = [
            notification
            for notification in email_notifications
            if str(notification.get("receiver_id")) == receiver_id
        ]
        # create payload for all issues
        payload = {}
        email_notification_ids = []
        for receiver_notification in receiver_notifications:
            payload.setdefault(
                receiver_notification.get("entity_identifier"), {}
            ).setdefault(str(receiver_notification.get("triggered_by_id")), []).append(
                receiver_notification.get("data")
            )
            # append processed notifications
            processed_notifications.append(receiver_notification.get("id"))
            email_notification_ids.append(receiver_notification.get("id"))

        # Create emails for all the issues
        for issue_id, notification_data in payload.items():
            send_email_notification.delay(
                issue_id=issue_id,
                notification_data=notification_data,
                receiver_id=receiver_id,
                email_notification_ids=email_notification_ids,
            )

    # Update the email notification log
    EmailNotificationLog.objects.filter(pk__in=processed_notifications).update(
        processed_at=timezone.now()
    )
