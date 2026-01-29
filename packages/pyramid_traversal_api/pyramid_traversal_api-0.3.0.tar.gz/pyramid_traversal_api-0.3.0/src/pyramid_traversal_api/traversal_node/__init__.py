import time
import logging

from typing import Type

log = logging.getLogger(__name__)


class TraversalNode:
    # Static children are child nodes that can be reached by a static name without needing any backend lookup.
    static_children: dict[str, Type["Resource"]] = {}

    # Store known views (in class namespace, or "class static", so it is remembered)
    # Key is the view name, and the value is a list of request methods
    _known_views: dict[str, list[str]] = {}

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.variables = kwargs or {}

    def __getitem__(self, key: str) -> "Resource":
        if self._determine_is_reserved_keyname(key):
            raise KeyError("A view exists by this name, so stopping traversal")

        if key not in self.static_children:
            raise KeyError("no item")
        item = self.static_children[key]

        return self._mkchild(key, item)

    def __getattr__(self, key):
        if key in self.variables:
            return self.variables[key]

        # Attribute doesn't exist, provide some debug info for the developer
        available_keys = ", ".join(self.variables.keys())
        raise AttributeError(
            f'Attribute "{key}" not found in {type(self).__name__} (class {self.__class__.__name__}). Available: {available_keys}'
        )

    def _mkchild(self, key: str, resource, *args, **kwargs):
        """Helper that sets necessary fields for Pyramid traversal"""
        child = resource(self.request, **{**self.variables, **kwargs})
        child.__parent__ = self
        child.__name__ = key

        return child

    @classmethod
    def get_dynamic_openapi_info(cls):
        """Returns information about a child resoure and the url parameters required for it.
        Implement it if your resource does some kind of lookup for its children"""
        return None

    def _determine_is_reserved_keyname(self, key):
        """Uses pyramid introspection (https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/introspector.html)
        to determine if there is a view registered to this resource with the given key name. If so, we probably don't want to look it up in SQL,
        so this function is a helper for used in __getitem__ implementations.
        """
        log.debug(f"Checking if {key} is reserved")
        if key in self._known_views.keys() and (
            self._known_views[key] is None
            or self.request.method in self._known_views[key]
        ):
            # Note that we cannot store if a key is NOT a view as it would lead to a DOS vulnerability
            log.debug(f"{self.request.method} {key} is known to be a view")
            return True
        # Performance tests on my local machine shows this function costs ~0.04ms. Debug logging is orders of magnitude more expensive.
        # In the future we could try wrapping all the resource classes in factories that can perform the introspection at config-time?
        t = time.perf_counter_ns()

        introspector = self.request.registry.introspector
        view_intr = introspector.get_category("views")
        for view in view_intr:
            context = view["introspectable"]["context"]
            if context == self.__class__:
                name = view["introspectable"]["name"]
                request_methods = view["introspectable"]["request_methods"]
                if name == key and (
                    request_methods is None or self.request.method in request_methods
                ):
                    t_e = time.perf_counter_ns()
                    # We want to be aware of traversal time for now.
                    log.debug(
                        f"Stopping traversal, done in {(t_e - t) / 1000 / 1000}ms"
                    )
                    self._known_views[key] = request_methods
                    return True
        return False
