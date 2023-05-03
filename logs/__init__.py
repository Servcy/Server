import hashlib
import logging

from crum import get_current_request, get_current_user


class UserIdentifier(logging.Filter):
    def filter(self, record):
        user = get_current_user()
        if user and user.pk:
            record.user_identity = str(user.pk)
        else:
            request = get_current_request()
            if request:
                x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                user_agent = request.META.get("HTTP_USER_AGENT", "")
                if x_forwarded_for:
                    request_identity = f"{x_forwarded_for.split(',')[0]}:{user_agent}"
                else:
                    request_identity = f"{request.META.get('REMOTE_ADDR')}:{user_agent}"
                record.user_identity = hashlib.md5(
                    request_identity.encode()
                ).hexdigest()[:6]
            else:
                record.user_identity = "NULL"
        return True


class RequestIdentifier(logging.Filter):
    def filter(self, record):
        request = get_current_request()
        request_identity = ""
        if request and request.META.get("X-REQUEST-ID"):
            request_identity = request.META.get("X-REQUEST-ID")
        else:
            request_identity = "NULL"
        record.request_identity = f"{request_identity}"
        record.function = record.funcName or "NA"
        return True
