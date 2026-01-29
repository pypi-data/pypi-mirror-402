from pyramid_traversal_api.traversal_node import TraversalNode
from typing import Optional


class CollectionTraversalNodeValidatorMeta(type):
    def __new__(cls, clsname, bases, attrs):
        if clsname != "CollectionTraversalNode":
            if "child_resource_class" not in attrs:
                raise ValueError(
                    f"child_resource_class must be set for TraversalNodeClass when creating {clsname}"
                )

        return super().__new__(cls, clsname, bases, attrs)


class CollectionTraversalNode(
    TraversalNode, metaclass=CollectionTraversalNodeValidatorMeta
):
    """A node that wraps a collection of an API resource, usually fetched from a database or similar.
    Override the query_collection function with your own query logic

    The item resolved from query_collection is injected into the variables of the child resource.
    The class name is used by default, but you can override it by setting the `child_var_name` attribute."""

    child_var_name: Optional[str] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        if self._determine_is_reserved_keyname(key):
            raise KeyError("A view exists by this name, so stopping traversal")

        instance = self.query_item(key)

        if not instance:
            raise KeyError("No object found")

        # We inject the queried instance into variables accessable on the new resource,
        # so need to find a suitable name
        ctxvar_name = instance.__class__.__name__.lower()
        if self.child_var_name is not None:
            ctxvar_name = self.child_var_name

        resource = self._mkchild(
            key, self.child_resource_class, **{ctxvar_name: instance}
        )

        return resource

    def query_item(self, key):
        """Function intended to be overloaded with your own query logic"""
        raise NotImplementedError("Remember to implement query_item")

    @classmethod
    def get_dynamic_openapi_info(cls):
        raise NotImplementedError("get_dynamic_openapi_info needs to be implemented")
