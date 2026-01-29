# Helper for automagically generating CRUD views for a resource
import marshmallow
import typing
import functools
import logging

log = logging.getLogger(__name__)


def crud(
    create: typing.Optional[marshmallow.Schema],
    read: typing.Optional[bool],
    update: typing.Optional[marshmallow.Schema],
    delete: typing.Optional[bool],
):
    """Decorator to attach to a traversal node class. For each kwarg in create, read, update, delete, creates a corresponding view using the schema if a value is provided.
    For `read` and `delete`, you can only enable or disable creation of the view.

    :param create:
        Not yet implemented
    :param read:
        Not yet implemented
    :param update:
        Not yet implemented
    :param delete:
        Not yet implemented
    """

    def inner(f):
        @functools.wraps(f)
        def wrapper(*args, **kwds):
            cls = f(*args, **kwds)

            log.debug(f"Creating crud for {cls}")

            if create is not None:
                log.debug("Creating create")
                raise NotImplementedError("Not yet implemented")

            if read is not None:
                log.debug("Creating read")
                raise NotImplementedError("Not yet implemented")

            if update is not None:
                log.debug("Creating update")
                raise NotImplementedError("Not yet implemented")

            if delete is not None:
                log.debug("Creating delete")
                raise NotImplementedError("Not yet implemented")

            return cls

        return wrapper

    return inner
