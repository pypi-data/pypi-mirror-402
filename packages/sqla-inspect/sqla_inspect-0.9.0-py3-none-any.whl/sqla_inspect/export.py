# * Authors:
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
#       * TJEBBES Gaston <g.t@majerti.fr>
"""
Base export class
"""

import logging

from sqlalchemy.orm import (
    ColumnProperty,
    RelationshipProperty,
)

from sqla_inspect.base import (
    BaseSqlaInspector,
    FormatterRegistry,
)

BLACKLISTED_KEYS = []


# Should be completed (to see how this will be done)
FORMATTERS_REGISTRY = FormatterRegistry()


logger = logging.getLogger(__name__)


class BaseExporter:
    """
    A base exportation object, used to export tabular datas (csv or xls format)
    Should be used in conjunction with a writer
    """

    headers = []

    def __init__(self, **kw):
        self._datas = []
        if "headers" in kw:
            self.set_headers(kw["headers"])
        self.extra_headers = []

    def set_headers(self, headers):
        self.headers = headers

    @staticmethod
    def format_row(row):
        """
        Row formatter, should be implemented in subclasses
        """
        return row

    def add_row(self, row):
        """
        Add a row to our buffer
        """
        self._datas.append(self.format_row(row))

    def set_datas(self, datas):
        """
        bulk add rows
        """
        for data in datas:
            self.add_row(data)

    def render(self):
        """
        Render the datas as a file buffer
        """
        raise NotImplementedError()

    def add_extra_header(self, header_dict):
        """
        Add extra headers that allow to pass non sqlalchemy datas when
        populating
        """
        self.extra_headers.append(header_dict)

    def add_extra_datas(self, extra_datas):
        """
        Add extra datas to the last row

        :param list extra_datas: A list of formatted datas
        """
        for data in extra_datas:
            self._datas[-1].append(data)


def format_value(column_dict, value, key=None):
    """
    Format a value coming from the database (for example converts datetimes to
    strings)

    :param column_dict: The column datas collected during inspection
    :param value: A value coming from the database
    :param key: The exportation key
    """
    formatter = column_dict.get("formatter")
    prop = column_dict["__col__"]

    res = value

    if value in (
        "",
        None,
    ):
        res = ""

    elif formatter is not None:
        res = formatter(value)

    else:
        if hasattr(prop, "columns"):
            sqla_column = prop.columns[0]
            column_type = getattr(sqla_column.type, "impl", sqla_column.type)

            formatter = FORMATTERS_REGISTRY.get_formatter(column_type, key)
            if formatter is not None:
                res = formatter(value)

    return res


class SqlaExporter(BaseExporter, BaseSqlaInspector):
    """
    Sqla exportation class
    Allow to stream datas to be exported

        config_key

            The key in the export subdict in the sqlalchemy Column's info dict
            that is used to configure this export e.g : set config_key = "csv"
            if your column configuration looks like the following

            .. code-block:: python

                Column(Integer, info={'export' :
                    {'csv': {<config>}},
                        <main_export_config>
                    }

        .. note::

            By default, we look for the title in the colanderalchemy's title
            key info={'colanderalchemy': {'title': u'Column title'}}
    """

    config_key = ""

    def __init__(self, model, **kw):
        BaseExporter.__init__(self)
        BaseSqlaInspector.__init__(self, model, **kw)
        self.set_headers(self._collect_headers())

    def _is_excluded(self, prop, info_dict):
        """
        Check if the given prop should be excluded from the export
        """
        if prop.key in BLACKLISTED_KEYS:
            return True

        if info_dict.get("exclude", False):
            return True

        if prop.key in self.excludes:
            return True

        if self.includes and prop.key not in self.includes:
            return True

        return False

    def _get_title(self, prop, main_infos, info_dict):
        """
        Return the title configured as in colanderalchemy
        """
        result = main_infos.get("label")
        if result is None:
            result = info_dict.get("colanderalchemy", {}).get("title")
        if result is None:
            result = prop.key
        return result

    def _get_prop_infos(self, prop):
        """
        Return the infos configured for this specific prop, merging the
        different configuration level
        """
        info_dict = self.get_info_field(prop)
        main_infos = info_dict.get("export", {}).copy()
        infos = main_infos.get(self.config_key, {})
        main_infos["label"] = self._get_title(prop, main_infos, info_dict)
        main_infos["name"] = prop.key
        main_infos["key"] = prop.key
        main_infos.update(infos)
        main_infos["__col__"] = prop
        return main_infos

    def _collect_headers(self):
        """
        Collect headers from the models attribute info col
        """
        res = []

        for prop in self.get_sorted_columns():
            main_infos = self._get_prop_infos(prop)

            if self._is_excluded(prop, main_infos):
                continue

            if isinstance(prop, RelationshipProperty):
                main_infos = self._collect_relationship(main_infos, prop, res)

                if not main_infos:
                    # If still no success, we forgot this one
                    print(
                        "Maybe there's missing some informations \
about a relationship"
                    )
                    continue
            else:
                main_infos = self._merge_many_to_one_field_from_fkey(
                    main_infos, prop, res
                )
                if not main_infos:
                    continue

            if isinstance(main_infos, (list, tuple)):
                # In case _collect_relationship returned a list
                res.extend(main_infos)
            else:
                res.append(main_infos)
        return res

    def _collect_relationship(self, main_infos, prop, result):
        """
        collect a relationship header:

        * One To many : if {'export': {'reletad_key': 'remote_attr'}} is
            provided, we take all the related objects and join their remote
            attr's value with commas
            If an index is provided, only the related element of index 'index'
            is retrieved and it's attr value is returned
            In case of excel exports, a specific sheet is generated by table
            (see excel.py for more details)

        * Many To One :

            If a related_key is provided, we remove the associated foreign key
            from the output (we collect its associated title) and only the
            given key of the associated object will be exported
            If no related_key is provided, we use the relationship's title as
            prefix and for each attribute of the related object, we add a
            column
            If a callable is provided under the formatter key, it will be used
            to format the related object


        :param dict main_infos: The already collected datas about this column
        :param obj prop: The property mapper of the relationship
        :param list result: The actual collected headers
        :returns: a dict with the datas matching this header
        """
        # No handling of the uselist relationships for the moment
        # Maybe with indexes ? ( to see: on row add, append headers on the fly
        # if needed )
        if prop.uselist:
            # One to many
            pass
        else:
            if "related_key" in main_infos or "formatter" in main_infos:
                self._merge_many_to_one_field(main_infos, prop, result)
            else:
                related_field_inspector = BaseSqlaInspector(prop.mapper)
                main_infos_list = []

                for column in related_field_inspector.get_columns_only():
                    infos = self._get_prop_infos(column)
                    if self._is_excluded(column, infos):
                        continue

                    infos["label"] = "%s %s" % (main_infos["label"], infos["label"])
                    infos["__col__"] = main_infos["__col__"]
                    infos["name"] = "%s %s" % (main_infos["name"], column.key)
                    infos["key"] = main_infos["key"]
                    infos["related_key"] = column.key
                    main_infos_list.append(infos)
                return main_infos_list

        return main_infos

    def _merge_many_to_one_field(self, main_infos, prop, result):
        """
        * Find the foreignkey associated to the current relationship
        * Get its title
        * Remove this fkey field from the export

        :param dict main_infos: The datas collected about the relationship
        :param obj prop: The property mapper of the relationship
        :param list result: The actual collected headers
        :returns: a title
        """
        title = None
        # We first find the related foreignkey to get the good title
        rel_base = list(prop.local_columns)[0]
        related_fkey_name = rel_base.name
        if not main_infos.get("keep_key", False):
            for val in result:
                if val["name"] == related_fkey_name:
                    title = val["label"]
                    main_infos["label"] = title
                    result.remove(val)
                    break

        return main_infos

    def _merge_many_to_one_field_from_fkey(self, main_infos, prop, result):
        """
        Find the relationship associated with this fkey and set the title

        :param dict main_infos: The already collected datas about this column
        :param obj prop: The property mapper of the relationship
        :param list result: The actual collected headers
        :returns: a main_infos dict or None
        """
        if prop.columns[0].foreign_keys and prop.key.endswith("_id"):
            # We have a foreign key, we'll try to merge it with the
            # associated foreign key
            rel_name = prop.key[0:-3]
            for val in result:
                if val["name"] == rel_name:
                    val["label"] = main_infos["label"]
                    main_infos = None  # We can forget this field in export
                    break
        return main_infos

    def add_row(self, obj):
        """
        fill a new row with the given obj

            obj

               instance of the exporter's model
        """
        row = {}
        for column in self.headers:
            value = ""

            if "__col__" in column:
                if isinstance(column["__col__"], ColumnProperty):
                    value = self._get_column_cell_val(obj, column)

                elif isinstance(column["__col__"], RelationshipProperty):
                    value = self._get_relationship_cell_val(obj, column)

            row[column["name"]] = value

        self._datas.append(self.format_row(row))

    def _get_formatted_val(self, obj, name, column):
        """
        Format the value of the attribute 'name' from the given object
        """
        attr_path = name.split(".")
        val = None
        tmp_val = obj
        for attr in attr_path:
            tmp_val = getattr(tmp_val, attr, None)
            if tmp_val is None:
                break
        if tmp_val is not None:
            val = tmp_val

        return format_value(column, val, self.config_key)

    def _get_relationship_cell_val(self, obj, column):
        """
        Return the value to insert in a relationship cell
        """
        val = ""
        key = column["key"]
        related_key = column.get("related_key", None)

        related_obj = getattr(obj, key, None)

        if related_obj is None:
            return ""

        if column["__col__"].uselist:  # OneToMany
            # We know how to retrieve a value from the related objects
            if related_key is not None:
                # Only the related object of the given index
                if column.get("index") is not None:
                    if len(related_obj) > column["index"]:
                        rel_obj = related_obj[column["index"]]
                        val = self._get_formatted_val(
                            rel_obj,
                            related_key,
                            column,
                        )
                # We join all the related objects val
                else:
                    _vals = []
                    for rel_obj in related_obj:
                        _vals.append(
                            self._get_formatted_val(
                                rel_obj,
                                related_key,
                                column,
                            )
                        )
                    val = "\n".join(_vals)
        else:  # Many to One
            if related_key is not None:
                val = self._get_formatted_val(related_obj, related_key, column)
            elif "formatter" in column:
                val = format_value(column, related_obj)

        return val

    def _get_column_cell_val(self, obj, column):
        """
        Return a value of a "column" cell
        """
        name = column["name"]
        return self._get_formatted_val(obj, name, column)
