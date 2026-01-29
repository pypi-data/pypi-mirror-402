# * Authors:
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
#       * TJEBBES Gaston <g.t@majerti.fr>

from sqla_inspect import ascii


def test_force_unicode():
    assert ascii.force_unicode("éko") == "éko"
    assert ascii.force_unicode("éko".encode("utf-8")) == "éko"


def test_force_utf8():
    assert ascii.force_utf8("éko") == "éko".encode("utf-8")


def test_force_ascii():
    assert ascii.force_ascii("éko") == "eko"
    assert ascii.force_ascii("éko".encode("utf-8")) == "eko"


def test_camel_case_to_name():
    assert ascii.camel_case_to_name("BaseObject") == "base_object"
    assert ascii.camel_case_to_name("BBaseObject") == "b_base_object"
