from parse import parse
from webob.request import Request

from poridhiweb.common_handlers import CommonHandlers
from poridhiweb.exceptions import MethodNotAllowed
from poridhiweb.models.route_definition import RouteDefinition


class RoutingHelper:
    @staticmethod
    def _normalize_request_url(url):
        if url != "/" and url.endswith("/"):
            return url[:-1]
        return url

    @classmethod
    def _find_handler(cls, routes: dict, request: Request) -> RouteDefinition:
        requested_path = cls._normalize_request_url(request.path)

        if requested_path in routes:
            return routes[requested_path]

        # url that contains path variable
        for path, route_def in routes.items():
            parsed = parse(path, requested_path)
            if parsed:
                route_def.add_kwargs(parsed.named)
                return route_def

        # default fallback handler
        return RouteDefinition(CommonHandlers.url_not_found_handler)

    @classmethod
    def _find_class_based_handler(cls, request: Request, route_def: RouteDefinition) -> RouteDefinition:
        handler_instance = route_def.handler()
        function_name = request.method.lower()
        handler_fn = getattr(handler_instance, function_name, None)

        if not handler_fn:
            raise MethodNotAllowed(request)

        return RouteDefinition(handler_fn, kwargs=route_def.kwargs)

    @classmethod
    def get_route_definition(cls, routes: dict, request: Request) -> RouteDefinition:
        route_def: RouteDefinition = cls._find_handler(routes, request)

        if route_def.is_class_based_handler():
            return cls._find_class_based_handler(
                request, route_def
            )

        if not route_def.is_valid_method(request.method):
            raise MethodNotAllowed(request)

        return route_def
