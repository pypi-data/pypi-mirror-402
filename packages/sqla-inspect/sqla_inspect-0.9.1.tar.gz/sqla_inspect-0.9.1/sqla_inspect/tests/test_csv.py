# * Authors:
#       * TJEBBES Gaston <g.t@majerti.fr>
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;

from sqla_inspect.csv import CsvExporter


def test_writer():
    writer = CsvExporter()
    headers = [{"label": "Column %s" % i, "name": "col%s" % i} for i in range(3)]
    writer.set_headers(headers)
    writer.add_extra_header({"label": "Column 3", "name": "col3"})
    writer.add_extra_header({"label": "Column 4", "name": "col4"})
    writer.add_extra_header({"label": "Column 5", "name": "col5"})
    writer.add_row(dict(("col%s" % i, i) for i in range(4)))
    writer.add_extra_datas(["12", "4", "5"])
    f_buf = writer.render()
    assert len(writer.headers) == 3
    assert len(writer.extra_headers) == 3
    assert writer._datas[-1]["Column 3"] == "12"
