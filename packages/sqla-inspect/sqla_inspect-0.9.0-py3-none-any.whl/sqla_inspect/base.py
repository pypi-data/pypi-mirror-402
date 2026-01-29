# * Authors:
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
#       * TJEBBES Gaston <g.t@majerti.fr>
#
"""
utilities to inspect Sqlalchemy models
"""

from colanderalchemy.schema import _creation_order
from sqlalchemy import inspect
from sqlalchemy.orm import (
    ColumnProperty,
    RelationshipProperty,
)


class BaseSqlaInspector(object):
    """
    Base class for exporters

    Provide base stuff for model introspection

    model

        The model to inspect

    excludes

        Model attributes to exclude

    includes

        Force the list of model attributes to use
    """

    def __init__(self, model, excludes=(), includes=(), **kw):
        self.inspector = inspect(model)
        self.excludes = excludes
        self.includes = includes

    def get_sorted_columns(self):
        """
        Return columns regarding their relevance in the model's declaration
        """
        return sorted(self.inspector.attrs, key=_creation_order)

    def get_columns_only(self):
        """
        Return only the columns
        """
        return [
            prop
            for prop in self.get_sorted_columns()
            if isinstance(prop, ColumnProperty)
        ]

    def get_relationships_only(self):
        """
        Return only the relationships
        """
        return [
            prop
            for prop in self.get_sorted_columns()
            if isinstance(prop, RelationshipProperty)
        ]

    @staticmethod
    def get_info_field(prop):
        """
        Return the info attribute of the given property
        """
        if isinstance(prop, ColumnProperty):
            column = prop.columns[0]

        elif isinstance(prop, RelationshipProperty):
            column = prop

        return column.info


class Registry(dict):
    """
    A registry used to store sqla columns <-> datas association
    """

    def add_item(self, sqla_col_type, item, key_specific=None):
        """
        Add an item to the registry
        """
        if key_specific is not None:
            self.setdefault(key_specific, {})[sqla_col_type] = item
        else:
            self[sqla_col_type] = item

    def get_item(self, sqla_col, key_specific=None):
        item = None
        if key_specific is not None:
            item = self.get(key_specific, {}).get(sqla_col.__class__)

        if item is None:
            item = self.get(sqla_col.__class__)

        return item


class FormatterRegistry(Registry):
    """
    Registry specific to formatters
    """

    def add_formatter(self, sqla_col_type, formatter, key_specific=None):
        """
        Add a formatter to the registry
        if key_specific is provided, this formatter will only be used for some
        specific exports
        """
        self.add_item(sqla_col_type, formatter, key_specific)

    def get_formatter(self, sqla_col, key_specific=None):
        """
        Returns a formatter stored in the registry
        """
        return self.get_item(sqla_col, key_specific)
