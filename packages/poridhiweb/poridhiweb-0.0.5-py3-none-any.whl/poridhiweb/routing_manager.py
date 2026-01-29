from typing import Optional

from webob import Request

from poridhiweb.utils.routing_helper import RoutingHelper
from poridhiweb.models.route_definition import RouteDefinition


class RouteManager:
    def __init__(self):
        self.routes = {}

    def register(self, path, handler, allowed_methods: Optional[list] = None):
        if allowed_methods:
            allowed_methods = [method.upper() for method in allowed_methods]
        if path in self.routes:
            raise RuntimeError(f"Path: {path} already bind to another handler")
        self.routes[path] = RouteDefinition(handler, allowed_methods)

    def dispatch(self, http_request: Request):
        route_def: RouteDefinition = RoutingHelper.get_route_definition(self.routes, http_request)
        return route_def.handler(http_request, **route_def.kwargs)


