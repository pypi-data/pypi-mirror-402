from werkzeug.wrappers import Response

def auth_middleware(token: str, header: str = "Authorization", prefix: str = "Bearer "):
    def middleware(request):
        value = request.headers.get(header)

        if not value or not value.startswith(prefix):
            return Response("Unauthorized", status=401, content_type="text/plain")

        received = value[len(prefix):].strip()
        if received != token:
            return Response("Forbidden", status=403, content_type="text/plain")

        return None

    return middleware