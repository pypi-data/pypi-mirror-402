# * Authors:
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
#       * TJEBBES Gaston <g.t@majerti.fr>
"""
Py3o exporters


>>> model = Company.query().first()
>>> template = Template.query().first()
>>> odt_file_datas = compile_template(model, template.data_obj)
"""

from __future__ import absolute_import

from io import BytesIO
from xml.sax.saxutils import escape

from genshi.core import Markup
from py3o.template import Template
from sqlalchemy.orm import (
    ColumnProperty,
    RelationshipProperty,
)

from sqla_inspect.ascii import (
    force_unicode,
)
from sqla_inspect.base import (
    BaseSqlaInspector,
)
from sqla_inspect.export import (
    format_value,
)
from sqla_inspect.py3o_tmpl import CONTENT_TMPL


def format_py3o_val(value):
    """
    format a value to fit py3o's context

    * Handle linebreaks
    """
    value = force_unicode(value)
    value = escape(value)
    value = value.replace("\n", "<text:line-break/>")
    return Markup(value)


class SqlaContext(BaseSqlaInspector):
    """
    Provide a tool to build a context dict based on a given model. The datas are
    built following the informations retrieved from the model's declaration.

    Custom configuration can be achieved by customizing the info dict attribute
    from each column.

        config_key

            The key in the info dict we will look for.

            Actually handles the following informations :
                exclude : should the column be excluded from the output
                name : the key in the resulting dict


    >>> serializer = SqlaContext(Company)
    >>> company = Company.get(263)
    >>> res = s.compile_obj(company)


    :param model: a SQLA model
    """

    config_key = "py3o"

    def __init__(self, model, rels=None, **kw):
        BaseSqlaInspector.__init__(self, model, **kw)
        # We store the relations already treated by storing the primaryjoin that
        # they use, since the backref uses the same join string, we can avoid
        # recursive collection
        self.parent_rels = rels or []
        self.rels = []
        self.columns = self.collect_columns()

    def collect_columns(self):
        """
        Collect columns information from a given model.

        a column info contains

            the py3 informations

                exclude

                    Should the column be excluded from the current context ?

                name

                    the name of the key in the resulting py3o context of the
                    column

            __col__

                The original column object

            __prop__

                In case of a relationship, the SqlaContext wrapping the given
                object

        """
        res = []
        for prop in self.get_sorted_columns():
            info_dict = self.get_info_field(prop)
            export_infos = info_dict.get("export", {}).copy()

            main_infos = export_infos.get(self.config_key, {}).copy()

            if export_infos.get("exclude"):
                if main_infos.get("exclude", True):
                    continue

            infos = export_infos
            infos.update(main_infos)

            # Si la clé name n'est pas définit on la met au nom de la colonne
            # par défaut
            infos.setdefault("name", prop.key)
            infos["__col__"] = prop
            if isinstance(prop, RelationshipProperty):
                join = str(prop.primaryjoin)
                if join in self.parent_rels:
                    continue
                else:
                    self.rels.append(str(join))
                    infos["__prop__"] = SqlaContext(
                        prop.mapper, rels=self.rels + self.parent_rels
                    )

            res.append(infos)
        return res

    def make_doc(self):
        """
        Generate the doc for the current context in the form
        {'key': 'label'}
        """
        res = {}
        for column in self.columns:
            if isinstance(column["__col__"], ColumnProperty):
                key = column["name"]
                label = (
                    column["__col__"]
                    .columns[0]
                    .info.get("colanderalchemy", {})
                    .get("title")
                )
                if label is None:
                    continue
                res[key] = label

            elif isinstance(column["__col__"], RelationshipProperty):
                # 1- si la relation est directe (une AppOption), on override le
                # champ avec la valeur (pour éviter des profondeurs)
                # 2- si l'objet lié est plus complexe, on lui fait son propre
                # chemin
                # 3- si la relation est uselist, on fait une liste d'élément
                # liés qu'on place dans une clé "l" et on place l'élément lié
                # dans une clé portant le nom de son index
                key = column["name"]
                label = column["__col__"].info.get("colanderalchemy", {}).get("title")
                if label is None:
                    continue

                if column["__col__"].uselist:
                    subres = column["__prop__"].make_doc()

                    for subkey, value in subres.items():
                        new_key = "%s.first.%s" % (key, subkey)
                        res[new_key] = "%s - %s (premier élément)" % (label, value)
                        new_key = "%s.last.%s" % (key, subkey)
                        res[new_key] = "%s - %s (dernier élément)" % (label, value)
                else:
                    subres = column["__prop__"].make_doc()
                    for subkey, value in subres.items():
                        new_key = "%s.%s" % (key, subkey)
                        res[new_key] = "%s - %s" % (label, value)

        print("------------------ Rendering the docs -------------------")
        keys = res.keys()
        keys.sort()
        for key in keys:
            value = res[key]

            print("{0} : py3o.{1}".format(value, key))

        return res

    def gen_xml_doc(self):
        """
        Generate the text tags that should be inserted in the content.xml of a
        full model
        """
        res = self.make_doc()
        var_tag = """
        <text:user-field-decl office:value-type="string"
        office:string-value="%s" text:name="py3o.%s"/>"""
        text_tag = """<text:p text:style-name="P1">
            <text:user-field-get text:name="py3o.%s">%s</text:user-field-get>
        </text:p>
        """
        keys = res.keys()
        keys.sort()
        texts = ""
        vars = ""
        for key in keys:
            value = res[key]
            vars += var_tag % (value, key)
            texts += text_tag % (key, value)
        return CONTENT_TMPL % (vars, texts)

    def _get_formatted_val(self, obj, attribute, column):
        """
        Return the formatted value of the attribute "attribute" of the obj "obj"
        regarding the column's description

        :param obj obj: The instance we manage
        :param str attribute: The string defining the path to access the end
        attribute we want to manage
        :param dict column: The column description dictionnary
        :returns: The associated value
        """
        attr_path = attribute.split(".")
        val = None
        tmp_val = obj
        for attr in attr_path:
            tmp_val = getattr(tmp_val, attr, None)
            if tmp_val is None:
                break
        if tmp_val is not None:
            val = tmp_val

        value = format_value(column, val, self.config_key)
        return format_py3o_val(value)

    def _get_column_value(self, obj, column):
        """
        Return a single cell's value

        :param obj obj: The instance we manage
        :param dict column: The column description dictionnary
        :returns: The associated value
        """
        return self._get_formatted_val(obj, column["__col__"].key, column)

    def _get_to_many_relationship_value(self, obj, column):
        """
        Get the resulting datas for a One To many or a many to many relationship

        :param obj obj: The instance we manage
        :param dict column: The column description dictionnary
        :returns: The associated value
        """
        related_key = column.get("related_key", None)

        related = getattr(obj, column["__col__"].key)
        value = {}
        if related:
            total = len(related)
            for index, rel_obj in enumerate(related):
                if related_key:
                    compiled_res = self._get_formatted_val(rel_obj, related_key, column)
                else:
                    compiled_res = column["__prop__"].compile_obj(rel_obj)
                value["item_%d" % index] = compiled_res
                value[str(index)] = compiled_res
                value["_" + str(index)] = compiled_res

                if index == 0:
                    value["first"] = compiled_res

                if index == total - 1:
                    value["last"] = compiled_res

        return value

    def _get_to_one_relationship_value(self, obj, column):
        """
        Compute datas produced for a many to one relationship

        :param obj obj: The instance we manage
        :param dict column: The column description dictionnary
        :returns: The associated value
        """
        related_key = column.get("related_key", None)
        related = getattr(obj, column["__col__"].key)
        if related:
            if related_key is not None:
                value = self._get_formatted_val(related, related_key, column)
            else:
                value = column["__prop__"].compile_obj(related)
        else:
            value = ""
        return value

    def _get_relationship_value(self, obj, column):
        """
        Compute datas produced for a given relationship
        """
        if column["__col__"].uselist:
            value = self._get_to_many_relationship_value(obj, column)
        else:
            value = self._get_to_one_relationship_value(obj, column)

        return value

    def compile_obj(self, obj):
        """
        generate a context based on the given obj

        :param obj: an instance of the model
        """
        res = {}
        for column in self.columns:
            if isinstance(column["__col__"], ColumnProperty):
                value = self._get_column_value(obj, column)

            elif isinstance(column["__col__"], RelationshipProperty):
                value = self._get_relationship_value(obj, column)

            res[column["name"]] = value

        return res


def get_compilation_context(instance):
    """
    Return the compilation context for py3o templating

    Build a deep dict representation of the given instance and add config values

    :param obj instance: a SQLAlchemy model instance
    :return: a multi level dict with context datas
    :rtype: dict
    """
    context_builder = SqlaContext(instance.__class__)
    py3o_context = context_builder.compile_obj(instance)
    return py3o_context


def compile_template(instance, template, additionnal_context=None):
    """
    Fill the given template with the instance's datas and return the odt file

    For every instance class, common values are also inserted in the context
    dict (and so can be used) :

        * config values

    :param obj instance: the instance of a model (like Userdatas, Company)
    :param template: the template object to use
    :param dict additionnal_context: A dict containing datas we'd like to add to
    the py3o compilation template
    :return: a stringIO object filled with the resulting odt's informations
    """
    py3o_context = get_compilation_context(instance)

    if additionnal_context is not None:
        py3o_context.update(additionnal_context)

    output_doc = BytesIO()

    odt_builder = Template(template, output_doc)
    odt_builder.render(py3o_context)

    return output_doc
