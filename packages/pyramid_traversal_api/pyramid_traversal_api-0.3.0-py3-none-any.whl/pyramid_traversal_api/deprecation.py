"""Implements a decorator that allows you to warn API users of deprecation using RFC9745"""

import functools
import typing
import pyramid.httpexceptions as exc
from email.utils import formatdate

from datetime import datetime
from time import mktime


def deprecation(deprecation_datetime: str, link: typing.Optional[str]):
    """Implements the deprecation HTTP header (RFC9745) for a view. The view will continue to work after the deprecation datetime, but should be considered not wanted. The deprecation header will be injected both before and after deprecation time.

    ::param date:
        The date (and time) of the endpoint being deprecated in ISO 8601 format.
    ::param link:
        An optional link to information about the deprecation, provided to the user in the Link header
    """
    parsed_deprecation_datetime = datetime.fromisoformat(deprecation_datetime)
    headers = {
        "Deprecation": formatdate(
            timeval=mktime(parsed_deprecation_datetime.timetuple()),
            localtime=False,
            usegmt=True,
        )
    }
    if link is not None:
        headers["Link"] = f'<{link}>;rel="deprecation";type="text/html"'

    def inner(f):
        @functools.wraps(f)
        def wrapper(context, request):
            for header in headers.keys():
                request.response.headers[header] = headers[header]

            return f(context, request)

        return wrapper

    return inner
