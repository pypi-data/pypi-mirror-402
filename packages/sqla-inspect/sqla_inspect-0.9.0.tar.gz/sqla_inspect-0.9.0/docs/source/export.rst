Exportation tools
=================

sqla-inspect provide tools to export sqlalchemy models as :

* A py3o template context
* A csv file
* An excel file

Py3o Context
-------------

py3o is an elegant and scalable solution to design reports using LibreOffice or
OpenOffice. py3o.template is the templating component that takes care of
merging your data sets with a corresponding templated OpenOffice document.

More here : `https://pypi.python.org/pypi/py3o.template`_

sqla-inspect allows to compile a template using a sqlalchemy model instance as
context.

.. code-block:: python

    from sqla_inspect.py3o import compile_template
    from .models import DBSession, MyModel

    mymodel_instance = DBSession.query(MyModel).first()
    output_buffer = compile_template(
        mymodel_instance,
        "/tmp/mytemplate.odt",
        {'custom_key': 'custom_value'},
    )

The *output_buffer* is a cStringIO.StringIO() object.

sqla-inspect essentially build the templating context through the
sqla_inspect.py3o.get_compilation_context.

Relationships handling strategy
................................

The model is inspected in depth, recursively through the relationships.

if you have

.. code-block:: python

    class Parent(Base):
       id = Column(Integer, primary_key=True)
       name = Column(String(255))


    class Child(Base):
       id = Column(Integer, primary_key=True)
       parent_id = Column(ForeignKey('parent.id'))
       parent = relationship('Parent', backref='children')


.. code-block:: python

    >>> print py3o.get_template_context(child)
    {
        'id': 1,
        'parent_id': 5,
        'name': 'Youssouf',
        'parent': {'id': 5, 'name': 'Moha'}
    }


.. code-block:: python

    >>> print py3o.get_template_context(parent)
    {
        'id': 5,
        'name': 'Moha'
        'children': {
            'l': [
                {'id': 1, 'parent_id': 5, 'name': 'Youssouf'}
                {'id': 2, 'parent_id': 5, 'name': 'Myriam'}
            ],
            '0': {'id': 1, 'parent_id': 5, 'name': 'Youssouf'}
            '1': {'id': 2, 'parent_id': 5, 'name': 'Myriam'}
        }
    }

Here children datas could be accessed :

* In a for loop : through the 'l' key
* By index : through the '0', '1' key (e.g : 'py3o.children.1.name')

WARNING : You need to provide exclude arguments to avoid recursive loops


See `Customization`_ to know how to set custom formatters or to exclude columns
from export.

Csv Export
-----------------

.. code-block:: python

    from sqla_inspect.csv import SqlaCsvExporter

    exporter = SqlaCsvExporter(Model)
    for row in Model.query():
        exporter.add_row(row)
    with open('/tmp/test.csv', 'w') as f_buffer:
        exporter.render(f_buffer)


See `Customization`_ to know how to set custom formatters, labels, exclusions
and relationship formatters.

NB : OneToMany relationships are not exported in CSV format.


Excel export
-------------

.. code-block:: python

    from sqla_inspect.csv import SqlaXlsExporter

    exporter = SqlaXlsExporter(Model)
    for row in Model.query():
        exporter.add_row(row)
    with open('/tmp/test.xls', 'w') as f_buffer:
        exporter.render(f_buffer)


See `Customization`_ to know how to set custom formatters, labels, exclusions
and relationship formatters.

NB : In this case OneToMany relationships will be exported in separate sheets.


Ods export
-------------

.. code-block:: python

    from sqla_inspect.csv import SqlaOdsExporter

    exporter = SqlaOdsExporter(Model)
    for row in Model.query():
        exporter.add_row(row)
    with open('/tmp/test.ods', 'w') as f_buffer:
        exporter.render(f_buffer)


See `Customization`_ to know how to set custom formatters, labels, exclusions
and relationship formatters.

NB : In this case OneToMany relationships will be exported in separate sheets.


Customization
--------------

Globally
.........

You can globally set formatters through which value of a specific type will be
passed before export.

.. code-block:: python

    from sqla_inspect.export import FORMATTERS_REGISTRY
    FORMATTERS_REGISTRY.add_formatter(
        sqlalchemy.Boolean,
        lambda val: 'Y' and val or 'N'
    )

All booleans will be converted to 'Y' or 'N'. If you want to do this formatting
only for a specific export, add a key (the key as configured in the exporter
class, csv/excel/py3o for provided exporters)

.. code-block:: python

    from sqla_inspect.export import FORMATTERS_REGISTRY
    FORMATTERS_REGISTRY.add_formatter(
        sqlalchemy.Boolean,
        lambda val: 'Y' and val or 'N',
        'csv'
    )

You can globally blacklist some fields to avoid exporting them

.. code-block:: python

    from sqla_inspect.export import BLACKLISTED_KEYS
    BLACKLISTED_KEYS = ('_acl', 'password')


Per Column
..........

You can customize columns informations:

* The header label through the 'label' key
* The way a relationship is exported through the 'related_key' (the attribute on
  the related object that will replace the related object)
* The way the datas is formatted providing a formatter under the 'formatter' key
* Exclude a column setting the 'exclude' key

All this keys can be set at differente levels:

If you want to customize the header labels, you can provide informations in the
export/csv key

.. code-block:: python

    class Model(Base):
        attr1 = Column(
            Integer,
            info={'export': {'csv': {'label': u'My custom header'}}}
        )


If not set it will look one level higher in the export key

.. code-block:: python

    class Model(Base):
        attr1 = Column(
            Integer,
            info={
                'export': {
                    'label': u'My custom header',
                    'formatter': lambda value: 5 * value
                }
            }
        )

Labels
~~~~~~

If the label is not set (only in the case of labels), it will look into the
colanderalchemy 'title' attribute

.. code-block:: python

    class Model(Base):
        attr1 = Column(
            Integer,
            info={'colanderalchemy': {'title': u'My title'}}
        )

Formatter
~~~~~~~~~~

If the value stored in the database should be presented differently in the csv
output. We use the `formatter` configuration key. A formatter is a callable
taking the db value as parameters.

.. code-block:: python

    class Model(Base):
        attr1 = Column(
            Integer,
            info={'export': {
            'title': u'My title',
            'formatter': lambda value: convert_value_to_display_format(value)
            }}
        )


M2O Relationships
~~~~~~~~~~~~~~~~~~~

ManyToOne relationships can be considered in two ways :

1- The related object is an "option" an object holding a label
2- The related object is another entity with several interesting attributes

Case 1 can be handled by specifying a related_key that sets the "option's"
attribute to use to fill the Csv column

.. code-block:: python

    class Model(Base):
        attr1 = relationship(
            "OptionModel",
            info={'export': {'related_key': 'label'}}
        )

Related key can also be a path (allows to go further on in M2O relationships.
The path is dot separated.

.. code-block:: python

    class Model(Base):
        attr1 = relationship(
            "OptionModel",
            info={'export': {'related_key': 'other_option.label'}}
        )

Case 1 can also be handled with a formatter, a formatter is a callable taking
the remote object as parameter and returning a computed value (here we call
the OptionModel.method() method)

.. code-block:: python

    class Model(Base):
        attr1 = relationship(
            "OptionModel",
            info={'export': {'formatter': lambda value: value.method()}}
        )

Case 2 can be handled by setting the configuration keys on the different
attributes from the related class.


The same things can be done with the excel.SqlaXlsExporter and ods.SqlaOdsExport
class (that shares the export dict with the SqlaCsvExporter.


LIMITATIONS
------------

OneToMany relationships (that point to lists) are not handled in csv format.

If you configure several exports (around different objects), export
configuration may conflict (excludes maybe usefull to avoid circular inspection
one side but not the other).
