class GoogleMailService:
    @staticmethod
    def _get_mail_header(field: str, headers: list):
        for header in headers:
            if header["name"] == field:
                return header["value"]
        return None

    @staticmethod
    def _get_mail_body(payload: dict, message_id: str) -> tuple[str, list[dict]]:
        if "parts" not in payload:
            return payload.get("body", {}).get("data", "-"), []
        html_part = None
        text_part = None
        alternate_part = None
        attachments = []
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/html" and not html_part:
                html_part = part.get("body", {}).get("data", "-")
            elif part.get("mimeType") == "text/plain" and not text_part:
                text_part = part.get("body", {}).get("data", "-")
            elif part.get("mimeType") == "multipart/alternative" and not alternate_part:
                alternate_part = part
            if part.get("filename"):
                attachments.append(
                    {
                        "filename": part["filename"],
                        "attachment_id": part["body"]["attachmentId"],
                        "message_id": message_id,
                    }
                )
        if html_part:
            return html_part, attachments
        if text_part:
            return text_part, attachments
        if alternate_part:
            return (
                GoogleMailService._get_mail_body(alternate_part, message_id),
                attachments,
            )
        return "Could not find message body.", attachments
