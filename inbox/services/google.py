import base64


class GoogleMailService:
    @staticmethod
    def _get_mail_header(field: str, headers: list):
        for header in headers:
            if header["name"] == field:
                return header["value"]
        return None

    @staticmethod
    def _get_mail_body(payload: dict):
        # Attempt to get plain text message
        try:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    text = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
                    return text
        except KeyError:
            pass
        # If plain text is not available, get HTML message
        try:
            for part in payload["parts"]:
                if part["mimeType"] == "text/html":
                    text = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        "utf-8"
                    )
                    return text
        except KeyError:
            pass
        return "Could not find message body."
