"""Helpers for OpenAPI generation
Mostly copied verbatim or slightly modified from https://github.com/luhn/pyramid-marshmallow/blob/main/pyramid_marshmallow
"""

from marshmallow import Schema
from apispec import utils as apispec_utils
from apispec.ext.marshmallow.common import (
    resolve_schema_cls,
    resolve_schema_instance,
)


def _schema(schema):
    if isinstance(schema, dict):
        return Schema.from_dict(schema)
    else:
        return schema


def schema_name_resolver(schema):
    cls = resolve_schema_cls(schema)
    instance = resolve_schema_instance(schema)
    name = cls.__name__
    if not cls.opts.register:
        # Unregistered schemas are put inline.
        return False
    if instance.only or instance.exclude:
        # If schema includes only select fields, treat it as nonce
        return False
    if name.endswith("Schema"):
        name = name[:-6] or name
    if instance.partial:
        name = "Partial" + name
    return name


def set_request_body(spec, op, view):
    op["requestBody"] = {
        "content": {
            "application/json": {
                "schema": _schema(view["validate"]),
            },
        },
    }


def set_query_params(spec, op, view):
    op["parameters"].append(
        {
            "in": "query",
            "schema": _schema(view["validate"]),
        }
    )


def set_tag(spec, op, view):
    context = view["context"]
    if not context:
        return
    tag = getattr(context, "__tag__", None)
    if not tag:
        return
    if isinstance(tag, dict):
        # Cheating and using the private variable spec._tags
        if not any(x["name"] == tag["name"] for x in spec._tags):
            spec.tag(tag)
        tag_name = tag["name"]
    else:
        tag_name = tag
    op.setdefault("tags", []).append(tag_name)


def split_docstring(docstring):
    """
    Split a docstring in half, delineated with a "---".  The first half is
    returned verbatim, the second half is parsed as YAML.

    """
    split_lines = apispec_utils.trim_docstring(docstring).split("\n")

    # Cut YAML from rest of docstring
    for index, line in enumerate(split_lines):
        line = line.strip()
        if line.startswith("---"):
            cut_from = index
            break
    else:
        cut_from = len(split_lines)

    summary = split_lines[0].strip() or None
    docs = "\n".join(split_lines[1:cut_from]).strip() or None
    yaml_string = "\n".join(split_lines[cut_from:])
    if yaml_string:
        parsed = yaml.safe_load(yaml_string)
    else:
        parsed = dict()
    return summary, docs, parsed


def set_response_body(spec, op, view):
    for response_code, schema in view["marshal_responses"].items():
        op["responses"][response_code] = {
            "description": "",
            "content": {
                "application/json": {"schema": schema},
            },
        }


def get_operation_id(view):
    return view["callable"].__name__
