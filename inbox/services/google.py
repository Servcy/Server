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
            return payload["body"]["data"]
        else:
            return GoogleMailService._get_mail_body(payload["parts"][0])

    @staticmethod
    def _is_body_html(payload: dict):
        if "parts" not in payload:
            return payload["mimeType"] == "text/html"
        else:
            return GoogleMailService._is_body_html(payload["parts"][0])
