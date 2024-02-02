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
        html_part = None
        text_part = None
        alternate_part = None
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/html" and not html_part:
                html_part = part.get("body", {}).get("data", "-")
            elif part.get("mimeType") == "text/plain" and not text_part:
                text_part = part.get("body", {}).get("data", "-")
            elif part.get("mimeType") == "multipart/alternative" and not alternate_part:
                alternate_part = part
        if html_part:
            return html_part
        if text_part:
            return text_part
        if alternate_part:
            return GoogleMailService._get_mail_body(alternate_part)
        return "Could not find message body."
