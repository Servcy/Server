import base64
import io

from django.conf import settings
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Attachment, Mail

SENDGRID_API_KEY = settings.SENDGRID_API_KEY
SEND_EMAIL_ENDPOINT = settings.SEND_EMAIL_ENDPOINT
SENDGRID_WORKSPACE_INVITATION_TEMPLATE_ID = (
    settings.SENDGRID_WORKSPACE_INVITATION_TEMPLATE_ID
)
SENDGRID_NEW_SIGNUP_TEMPLATE_ID = settings.SENDGRID_NEW_SIGNUP_TEMPLATE_ID
SENDGRID_FROM_EMAIL = settings.SENDGRID_FROM_EMAIL
SENDGRID_VERIFICATION_TEMPLATE_ID = settings.SENDGRID_VERIFICATION_TEMPLATE_ID
SENDGRID_ANALYTICS_EXPORT_TEMPLATE_ID = settings.SENDGRID_ANALYTICS_EXPORT_TEMPLATE_ID


class SendGridEmail:
    def __init__(self, to_email):
        self.to_email = to_email
        if to_email in settings.TEST_ACCOUNTS:
            username = to_email.split("@")[0]
            self.to_email = f"contact+{username}@servcy.com"
        self.from_email = SENDGRID_FROM_EMAIL
        self.client = SendGridAPIClient(SENDGRID_API_KEY)

    def send_login_otp(self, otp):
        if settings.DEBUG:
            return 200
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
        )
        message.dynamic_template_data = {
            "otp": otp,
        }
        message.template_id = SENDGRID_VERIFICATION_TEMPLATE_ID
        response = self.client.send(message)
        return response.status_code

    def send_new_signup_notification(self, dynamic_template_data):
        if settings.DEBUG:
            return 200
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
        )
        message.dynamic_template_data = dynamic_template_data
        message.template_id = SENDGRID_NEW_SIGNUP_TEMPLATE_ID
        response = self.client.send(message)
        return response.status_code

    def send_workspace_invitation(self, workspace_name, user_name, invite_link):
        if settings.DEBUG:
            return 200
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
        )
        message.dynamic_template_data = {
            "workspace_name": workspace_name,
            "user_name": user_name,
            "recipient": self.to_email,
            "invite_link": invite_link,
        }
        message.template_id = SENDGRID_WORKSPACE_INVITATION_TEMPLATE_ID
        response = self.client.send(message)
        return response.status_code

    def send_analytics_export(self, slug, csv_buffer: io.StringIO):
        """
        Send an email with the analytics export
        """
        # if settings.DEBUG:
        #     return 200
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
        )
        message.dynamic_template_data = {
            "recipient": self.to_email,
        }
        message.template_id = SENDGRID_ANALYTICS_EXPORT_TEMPLATE_ID
        message.add_attachment(
            Attachment(
                base64.b64encode(csv_buffer.getvalue().encode()).decode(),
                f"{slug}_Analytics.csv",
                "text/csv",
                "attachment",
                None,
            )
        )
        response = self.client.send(message)
        return response.status_code

    def send_issue_activity(self, subject, body):
        """
        Send an email with the issue activity
        """
        if settings.DEBUG:
            return 200
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
            subject=subject,
            html_content=body,
        )
        response = self.client.send(message)
        return response.status_code
