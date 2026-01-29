# * Authors:
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
#       * TJEBBES Gaston <g.t@majerti.fr>
"""
Provide common tools for string handling
"""

import random
import re
from string import ascii_lowercase

from unidecode import unidecode


def force_ascii(value):
    """
    Return enforced ascii string
    éko=>ko
    """
    if isinstance(value, bytes):
        value = force_string(value)
    value = unidecode(value)
    return value


def force_utf8(value):
    """
    return a utf-8 byte string

    :param str value:
    :rtype: bytes
    """
    return force_encoding(value, "utf-8")


def force_encoding(value, encoding):
    """
    :rtype: bytes
    """
    if not isinstance(value, (str, bytes)):
        value = str(value)

    if isinstance(value, str):
        value = value.encode(encoding)
    elif encoding != "utf-8":
        value = value.decode("utf-8").encode(encoding)
    return value


def force_string(value):
    """
    return an utf-8 str

    :param bytes value: The original value to convert
    :rtype: str
    """
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    elif not isinstance(value, str):
        value = str(value)
    return value


force_unicode = force_string


def camel_case_to_name(name):
    """
    Used to convert a classname to a lowercase name
    """

    def convert_func(val):
        return "_" + val.group(0).lower()

    return name[0].lower() + re.sub(r"([A-Z])", convert_func, name[1:])


def gen_random_string(size=15):
    """
    Generate random string

        size

            size of the resulting string
    """
    return "".join(random.choice(ascii_lowercase) for _ in range(size))


def random_tag_id(size=15):
    """
    Return a random string supposed to be used as tag id
    """
    return gen_random_string(size)


def to_utf8(data):
    """
    Force utf8 string entries in the given datas
    """
    res = data
    if isinstance(data, dict):
        res = {}
        for key, value in data.items():
            key = to_utf8(key)
            value = to_utf8(value)
            res[key] = value

    elif isinstance(data, (list, tuple)):
        res = []
        for data in data:
            res.append(to_utf8(data))

    elif isinstance(data, (str, bytes)):
        res = force_utf8(data)

    return res
