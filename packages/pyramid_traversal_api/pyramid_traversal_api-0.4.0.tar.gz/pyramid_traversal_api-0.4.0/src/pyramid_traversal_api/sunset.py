"""Implements a decorator that allows you to warn of and enforce using RFC8594"""

import functools
import typing
import pyramid.httpexceptions as exc
from email.utils import formatdate

from datetime import datetime
from time import mktime


def sunset(sunset_datetime: str, link: typing.Optional[str]):
    """Implements the sunset HTTP header (RFC8594) for a view. The view will automatically stop working entirely once the date is passed.
    This decorator can be used for automatically enforcing grade periods for deprecated views.

    ::param date:
        The date (and time) of the endpoint being sunset in ISO 8601 format. The endpoint will automatically stop working after this date.
    ::param link:
        An optional link to information about the sunsetting, provided to the suer in the Link header.
    """
    parsed_sunset_datetime = datetime.fromisoformat(sunset_datetime)
    headers = {
        "Sunset": formatdate(
            timeval=mktime(parsed_sunset_datetime.timetuple()),
            localtime=False,
            usegmt=True,
        )
    }
    if link is not None:
        headers["Link"] = f'<{link}>;rel="sunset";type="text/html"'

    def inner(f):
        @functools.wraps(f)
        def wrapper(context, request):
            if datetime.now() > parsed_sunset_datetime:
                raise exc.HTTPBadRequest(
                    "This endpoint has been sunset", headers=headers
                )
            else:
                for header in headers.keys():
                    request.response.headers[header] = headers[header]

            return f(context, request)

        return wrapper

    return inner
