from marshmallow import Schema
from pyramid.response import Response
from pyramid.viewderivers import VIEW
import pyramid.httpexceptions as exc

import logging

log = logging.getLogger(__name__)


def includeme(config):
    # Forward some work to pyramid_marshmallow for now
    config.add_view_deriver(view_validator)
    config.add_view_deriver(view_marshaller, under="rendered_view", over=VIEW)
    config.add_view_deriver(view_api_spec)


def process_schema(schema: dict):
    """Normalizes a schema. If it is a dict, convert it to Schema. If not, return as-is."""
    if isinstance(schema, Schema):
        return schema
    elif isinstance(schema, dict):
        return Schema.from_dict(schema)()
    else:
        raise TypeError(f"Schema {schema} is invalid type")


def process_schemas(schemas):
    """Handle a schemas passed in as a view deriver, creating a nonce schema if a
    dictionary.
    """
    if schemas is None:
        return {}
    new_schemas = {}
    for response, schema in schemas.items():
        new_schemas[response] = process_schema(schema)
    return new_schemas


def view_validator(view, info):
    # https://github.com/luhn/pyramid-marshmallow/blob/main/pyramid_marshmallow/__init__.py
    schema = info.options.get("validate")
    if schema is None:
        return view
    schema = process_schema(schema)

    def wrapped(context, request):
        if request.method == "GET":
            data = dict()
            for k, v in request.GET.items():
                field = schema.fields.get(k)
                if isinstance(field, fields.List):
                    data.setdefault(k, []).append(v)
                else:
                    data[k] = v
        else:
            data = request.json_body
        request.data = schema.load(data)
        return view(context, request)

    return wrapped


view_validator.options = ("validate",)


def view_marshaller(view, info):
    """If there is a schema for the response code being returned, we marshal it
    TODO: Maybe ignore the marshalling altogether and only use it for schema?"""
    schemas = process_schemas(info.options.get("marshal_responses"))
    if not any([schema is not None for schema in schemas.values()]):
        return view

    def wrapped(context, request):
        output = view(context, request)

        status = str(request.response.status_int)

        if isinstance(output, Response) or status not in schemas:
            return output
        else:
            dumped = schemas[status].dump(output)

            errors = schemas[status].validate(dumped)
            if len(errors) != 0:
                log.info(f"Validation errors: {errors}")
                raise exc.HTTPInternalServerError(
                    "Unable to generate correct response. This is on us. Sorry"
                )
            return dumped

    return wrapped


# Ignore type as we are doing some Python dark magic here
view_marshaller.options = ("marshal_responses",)  # type: ignore[attr-defined]


# TODO: consolidate view options
def view_api_spec(view, info):
    return view


view_api_spec.options = "api_spec"  # type: ignore[attr-defined]
