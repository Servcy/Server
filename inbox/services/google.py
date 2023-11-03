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
        if "parts" not in payload:
            return payload.get("body", {}).get("data", "-")
        # Attempt to get HTML message
        try:
            for part in payload.get("parts", []):
                if part.get("mimeType", "") == "text/html":
                    return part["body"]["data"]
        except KeyError:
            pass
        # If HTML is not available, get plain text message
        try:
            for part in payload.get("parts", []):
                if part["mimeType"] == "text/plain":
                    return part["body"]["data"]
        except KeyError:
            pass
        return "Could not find message body."
