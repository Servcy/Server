import uuid


class RequestUUIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())[:8]
        request.META["X-REQUEST-ID"] = request_id
        response = self.get_response(request)
        return response
