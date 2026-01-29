# * Authors:
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
#       * TJEBBES Gaston <g.t@majerti.fr>
"""
Ods exportation module
"""

import io
import logging

import odswriter

from sqla_inspect.base import Registry
from sqla_inspect.export import (
    BaseExporter,
    SqlaExporter,
)

log = logging.getLogger(__name__)
# To be overriden by end user
FORMAT_REGISTRY = Registry()


class OdsWriter(object):
    """
    Class providing common tools to write ods files from tabular datas

    Has to be subclassed, the subclass should provide a _datas and a headers
    attribute that contains the datas to render and the headers

        _datas

            list of tuples (each tuple is a row)

        headers

            list of dict containing the label of each column:
                {'label': <a label>}
    """

    default_title = "Export"

    def __init__(self, title=None, **kw):
        self.sheets = []
        self.title = title or self.default_title
        self.options = kw

    def render(self, f_buf=None):
        """
        Definitely render the workbook

        :param obj f_buf: A file buffer supporting the write and seek
        methods
        """
        if f_buf is None:
            f_buf = io.BytesIO()

        with odswriter.writer(f_buf) as writer:
            default_sheet = writer.new_sheet(self.title)
            self._render_headers(default_sheet)
            self._render_rows(default_sheet)

            # abstract_sheet require the same attributes as our current writer
            for abstract_sheet in self.sheets:
                sheet = writer.new_sheet(name=abstract_sheet.title)
                abstract_sheet._render_headers(sheet)
                abstract_sheet._render_rows(sheet)
        f_buf.seek(0)
        return f_buf

    def format_cell(self, column_name: str, value: str):
        """
        Format a cell
        """
        if hasattr(self, "format_%s" % column_name):
            value = getattr(self, "format_%s" % column_name)(value)
        return value

    def format_row(self, row):
        """
        The render method expects rows as lists, here we switch our row format
        from dict to list respecting the order of the headers
        """
        res = []
        headers = getattr(self, "headers", [])
        for column in headers:
            column_name = column["name"]
            value = row.get(column_name, "")
            value = self.format_cell(column_name, value)
            res.append(value)
        return res

    def _render_rows(self, sheet):
        """
        Add the datas to the given sheet

        :param obj sheet: an odswriter Sheet object
        """
        _datas = getattr(self, "_datas", ())
        sheet.writerows(_datas)

    def _render_headers(self, sheet):
        """
        Write the headers row

        :param obj sheet: an odswriter Sheet object
        """
        headers = getattr(self, "headers", ())
        labels = [header["label"] for header in headers]
        extra_headers = getattr(self, "extra_headers", ())
        labels.extend([header["label"] for header in extra_headers])
        sheet.writerow(labels)

    def add_sheet(self, sheet_object):
        """
        Add a OdsWriter instance as a sheet of the main workbook

        :param obj sheet_object: A sheet object added to the current workbook
        """
        self.sheets.append(sheet_object)

    def set_title(self, title):
        self.title = title

    def set_headers(self, headers):
        """
        Set the headers of our writer
        :param list headers: list of dict with at least a label key
        (label is mandatory : used for the export)

        Headers are filtered and ordered regarding the order option
        """
        self.headers = []
        if "order" in self.options:
            for element in self.options["order"]:
                for header in headers:
                    if header.get("key", header["label"]) == element:
                        self.headers.append(header)
                        break
        else:
            self.headers = headers


class SqlaOdsExporter(OdsWriter, SqlaExporter):
    """
    Main class used for exporting datas to the Ods format

    Models attributes output can be customized through the info param :

        Column(Integer, infos={'export':
            {'ods':<ods_specific_options>,
             <main_export_options>
            }
        }

    main_export_options and ods_specific_options can be :

        label

            label of the column header

        format

            a function that will be fired on each row to format the output

        related_key

            If the attribute is a relationship, the value of the given attribute
            of the related object will be used to fill the cells

        exclude

            This data will not be inserted in the export if True

    Usage:

        a = SqlaOdsExporter(MyModel)
        for i in MyModel.query().filter(<myfilter>):
            a.add_row(i)
        file_buffer = a.render()
    """

    config_key = "ods"

    def __init__(self, model, is_root=True, title=None, **kw):
        self.is_root = is_root
        OdsWriter.__init__(self, title=title, **kw)
        SqlaExporter.__init__(self, model, **kw)

    def _get_related_exporter(self, related_obj, column):
        """
        returns an SqlaOdsExporter for the given related object and stores it in
        the column object as a cache
        """
        result = column.get("sqla_ods_exporter")
        if result is None:
            result = column["sqla_ods_exporter"] = SqlaOdsExporter(
                related_obj.__class__,
                is_root=False,
                title=column.get("label", column["key"]),
            )
            self.add_sheet(result)
        return result

    def _get_relationship_cell_val(self, obj, column):
        """
        Return the value to insert in a relationship cell
        Handle the case of complex related datas we want to handle
        """
        val = SqlaExporter._get_relationship_cell_val(self, obj, column)
        if val == "":
            related_key = column.get("related_key", None)

            if column["__col__"].uselist and related_key is None and self.is_root:
                # on récupère les objets liés
                key = column["key"]
                related_objects = getattr(obj, key, None)
                if not related_objects:
                    return ""
                else:
                    exporter = self._get_related_exporter(
                        related_objects[0],
                        column,
                    )
                    for rel_obj in related_objects:
                        exporter.add_row(rel_obj)

        return val


class OdsExporter(OdsWriter, BaseExporter):
    """
    A main Ods exportation tool (without sqlalchemy support)

    writer = OdsExporter(headers=({'label': 'Colonne 1', 'key': 'key'},))
    writer.add_row({'key': u'La valeur de la cellule de la colonne 1'})
    writer.render()
    """

    headers = ()

    def __init__(self, title=None, **kw):
        OdsWriter.__init__(self, title, **kw)
        BaseExporter.__init__(self, **kw)
