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
SENDGRID_ANALYTICS_EXPORT_TEMPLATE_ID = settings.SENDGRID_ANALYTICS_EXPORT_TEMPLATE_ID


class SendGridEmail:
    def __init__(self, to_email):
        self.to_email = to_email
        self.from_email = SENDGRID_FROM_EMAIL
        self.client = SendGridAPIClient(SENDGRID_API_KEY)

    def send_new_signup_notification(self, dynamic_template_data):
        message = Mail(
            from_email=self.from_email,
            to_emails=self.to_email,
        )
        message.dynamic_template_data = dynamic_template_data
        message.template_id = SENDGRID_NEW_SIGNUP_TEMPLATE_ID
        response = self.client.send(message)
        return response.status_code

    def send_workspace_invitation(self, workspace_name, user_name, invite_link):
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

    def send_analytics_export(self, slug, csv_buffer):
        """
        Send an email with the analytics export
        """
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
                FileContent=csv_buffer.getvalue(),
                FileName=f"{slug}_Analytics.csv",
                FileType="text/csv",
                Disposition="attachment",
            )
        )
        response = self.client.send(message)
        return response.status_code
