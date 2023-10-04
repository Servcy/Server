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
            html_part = next(
                (part for part in payload["parts"] if part["mimeType"] == "text/html"),
                None,
            )
            if html_part is not None:
                return html_part["body"]["data"], html_part["mimeType"]
            else:
                return payload["parts"][0]["body"]["data"]
