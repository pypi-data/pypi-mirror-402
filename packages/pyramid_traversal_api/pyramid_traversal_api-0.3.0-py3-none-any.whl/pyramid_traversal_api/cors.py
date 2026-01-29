"""Heavily inspired by https://gist.github.com/mmerickel/1afaf64154b335b596e4

Usage:
```
    config.include('pyramid_traversal_api.cors')

     # make sure to add this before other routes to intercept OPTIONS
    config.add_cors_preflight_handler()
```
"""

from pyramid.security import NO_PERMISSION_REQUIRED

CONFIG_CORS_ALLOWED_ORIGINS_KEY = "cors.allowed_origins"  # Comma separated
CONFIG_CORS_ALLOWED_HEADERS_KEY = "cors.allowed_headers"  # Comma separated


def includeme(config):
    if (
        CONFIG_CORS_ALLOWED_HEADERS_KEY not in config.registry.settings
        or CONFIG_CORS_ALLOWED_ORIGINS_KEY not in config.registry.settings
    ):
        raise ValueError(
            f"Please set {CONFIG_CORS_ALLOWED_HEADERS_KEY} and {CONFIG_CORS_ALLOWED_ORIGINS_KEY} in your paste config before enabling cors handling"
        )
    config.add_directive("add_cors_preflight_headers", add_cors_preflight_handler)
    config.add_route_predicate("cors_preflight", CorsPreflightPredicate)

    config.add_subscriber(add_cors_to_response, "pyramid.events.NewResponse")


class CorsPreflightPredicate(object):
    def __init__(self, val, config):
        self.val = val

    def text(self):
        return "cors_preflight = %s" % bool(self.val)

    phash = text

    def __call__(self, context, request):
        if not self.val:
            return False
        return (
            request.method == "OPTIONS"
            and "Origin" in request.headers
            and "Access-Control-Request-Method" in request.headers
        )


def add_cors_preflight_handler(config):
    config.add_route(
        "cors-options-preflight",
        "/{catch_all:.*}",
        cors_preflight=True,
    )
    config.add_view(
        cors_options_view,
        route_name="cors-options-preflight",
        permission=NO_PERMISSION_REQUIRED,
    )


def add_cors_to_response(event):
    request = event.request
    response = event.response
    if "Origin" in request.headers:
        allowed_origins = request.registry.settings[
            CONFIG_CORS_ALLOWED_ORIGINS_KEY
        ].split(",")
        # Only respond with allow-origin if it is on the allowed list.
        if "*" in allowed_origins:
            print("We wildcardin'. Gucci")
            response.headers["Access-Control-Allow-Origin"] = "*"
        elif request.headers["Origin"] in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = request.headers["Origin"]


def cors_options_view(context, request):
    response = request.response

    response.headers["Access-Control-Allow-Methods"] = (
        "OPTIONS,HEAD,GET,POST,PUT,DELETE"
    )

    if CONFIG_CORS_ALLOWED_HEADERS_KEY in request.registry.settings:
        if "Access-Control-Request-Headers" in request.headers:
            response.headers["Access-Control-Allow-Headers"] = (
                request.registry.settings[CONFIG_CORS_ALLOWED_HEADERS_KEY]
            )
    return response
