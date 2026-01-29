from werkzeug.wrappers import Request, Response
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.serving import run_simple
import os
import urllib.parse
from threading import Thread
import time

STATIC_DIR = "static"

ROUTES = []
MIDDLEWARES = []
PROTECTED_ROUTES = {}

def route(path, methods=None):
    methods = methods or ["GET"]
    def decorator(func):
        for m in methods:
            ROUTES.append((path, m.upper(), func))
        return func
    return decorator

def protect(path, methods=None, middleware=None):
    methods = methods or ["GET"]
    for m in methods:
        PROTECTED_ROUTES[(path, m.upper())] = middleware

def use(middleware_func):
    MIDDLEWARES.append(middleware_func)

class Boask:
    def __init__(self):
        self.url_map = Map([Rule(r[0], endpoint=r[2], methods=[r[1]]) for r in ROUTES])

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        path = request.path
        method = request.method.upper()

        for mw in MIDDLEWARES:
            try:
                mw(request)
            except StopIteration:
                return Response("Middleware stopped request", status=403)(environ, start_response)

        if path.startswith("/static/"):
            file_path = os.path.join(STATIC_DIR, path[len("/static/"):].lstrip("/"))
            full_path = os.path.abspath(file_path)
            if full_path.startswith(os.path.abspath(STATIC_DIR)) and os.path.isfile(full_path):
                with open(full_path, "rb") as f:
                    return Response(f.read(), content_type="application/octet-stream")(environ, start_response)
            return Response("File not found", status=404)(environ, start_response)

        if (path, method) in PROTECTED_ROUTES:
            try:
                PROTECTED_ROUTES[(path, method)](request)
            except StopIteration:
                return Response("Unauthorized", status=401)(environ, start_response)

        for r_path, r_method, r_func in ROUTES:
            if r_path == path and r_method == method:
                try:
                    response = r_func(request)
                    if isinstance(response, tuple) and len(response) == 2:
                        body, code = response
                        if isinstance(body, str):
                            body = body.encode("utf-8")
                        return Response(body, status=code)(environ, start_response)
                    if isinstance(response, str):
                        response = response.encode("utf-8")
                    return Response(response, status=200, content_type="text/html; charset=utf-8")(environ, start_response)
                except Exception as e:
                    return Response(f"Boask Error: {str(e)}", status=500)(environ, start_response)
        return Response("Not Found", status=404)(environ, start_response)

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

def run_server(port=8080, host="", debug=False):
    os.makedirs(STATIC_DIR, exist_ok=True)

    def serve():
        run_simple(host, port, Boask(), use_reloader=False)

    if debug:
        files_to_watch = []
        for root, dirs, files in os.walk(os.getcwd()):
            for f in files:
                if f.endswith(".py") or root.endswith("templates"):
                    files_to_watch.append(os.path.join(root, f))
        last_mtimes = {f: os.path.getmtime(f) for f in files_to_watch}
        while True:
            serve_thread = Thread(target=serve)
            serve_thread.start()
            try:
                while serve_thread.is_alive():
                    time.sleep(1)
                    reload_needed = False
                    for f in files_to_watch:
                        if os.path.getmtime(f) != last_mtimes[f]:
                            reload_needed = True
                            last_mtimes[f] = os.path.getmtime(f)
                    if reload_needed:
                        os._exit(3)
            except KeyboardInterrupt:
                break
    else:
        serve()
