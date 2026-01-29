from sqlalchemy.sql.schema import Column
from sqlalchemy.orm.decl_api import DeclarativeBase
from pyramid_traversal_api.traversal_node.collection import (
    CollectionTraversalNode,
    CollectionTraversalNodeValidatorMeta,
)
from pyramid_traversal_api.traversal_node import TraversalNode
from sqlalchemy import select
import sqlalchemy
import pyramid.httpexceptions as exc

from collections.abc import Callable
from typing import Optional, Type, Any

from uuid import UUID


# Key normalizers automatically translate the key (which is a string) to whatever type is required for the column type
def uuid_normalizer(self, key):
    # Due to SQLite, if the colum type is UUID, we have to convert the key to uuid first
    try:
        return UUID(key)
    except ValueError:
        raise exc.HTTPBadRequest("Bad UUID")


def noop_normalizer(self, key):
    return key


class SqlaCollectionValidatorMeta(CollectionTraversalNodeValidatorMeta):
    """Validates a SqlaCollectionTraversalNode and performs other setup tasks at class creation time, so no runtime validation is necessary"""

    def __new__(cls, clsname, bases, attrs):
        if clsname != "SqlaCollectionTraversalNode":
            if "sql_class" not in attrs:
                raise ValueError(
                    f"sql_class must be set for a SqlaCollectionTraversalNode when creating {clsname}"
                )
            if "child_traversal_node" not in attrs:
                raise ValueError(
                    f"child_traversal_node must be set for a SqlaCollectionTraversalNode when creating {clsname}"
                )

            # Optional
            if "query_field" not in attrs:
                attrs["query_field"] = cls._determine_sql_field(
                    clsname, attrs["sql_class"]
                )

            # Some key types may need to be normalized before querying, determine that now
            match type(attrs["query_field"].type):
                case sqlalchemy.sql.sqltypes.Uuid:
                    attrs["key_normalizer"] = uuid_normalizer
                case _:
                    attrs["key_normalizer"] = noop_normalizer

        return super().__new__(cls, clsname, bases, attrs)

    @staticmethod
    def _determine_sql_field(clsname, sql_class):
        """This function introspects the SQLAlchemy entity and finds the primary key."""
        if len(sql_class.__table__.primary_key.columns) != 1:
            raise NotImplementedError(
                f"Error validating {clsname} - SqlChildResource does not support sql models with multiple primary keys - sorry!"
            )
        return sql_class.__table__.primary_key.columns[0]


class SqlaCollectionTraversalNode(
    CollectionTraversalNode, metaclass=SqlaCollectionValidatorMeta
):
    """Helper class for cases where the child node is an instance of an SQLAlchemy enity.

    By default it will auto-detect the column to query by looking for the primary key.
    You can also explicitly specify the query column using `query_field` if needed.
    """

    # By ignoring typing here, we force any downstream class to implement these
    # These need to be set for any inheriting class to work properly
    sql_class: Type[DeclarativeBase] = None  # type: ignore
    child_traversal_node: Type[TraversalNode] = None  # type: ignore
    # Optional, overrides the field to be queried
    query_field: Optional[Type[Column]] = None

    # Auto-populated by the metaclass
    key_normalizer: Callable[[str], Any]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def get_dynamic_openapi_info(cls):
        return {
            "resource": cls.child_traversal_node,
            "params": [
                {
                    "name": cls.sql_class.__table__.name + "_" + cls.query_field.name,
                    "description": f"Primary key of {cls.sql_class.__table__.name}",
                    "schema": {
                        # TODO: autodetect a better type based on the primary key field type?
                        "type": "string",
                    },
                }
            ],
        }

    def _query_object(self, key):
        """Performs the SQLAlchemy query to fetch the object. By default uses the provided query field, or the one autodetected by the constructor.
        Override this if you have special requirements for how the query is made

        The database session is assumed to be reachable on request and be named dbsession.
        TODO: make this configurable"""

        normalized_key = self.key_normalizer(key)

        return self.request.dbsession.scalars(
            select(self.sql_class).where(self.query_field == normalized_key)
        ).first()

    def query_item(self, key):
        """Queries SQLAlchemy for the specified key"""
        return self._query_object(key)
