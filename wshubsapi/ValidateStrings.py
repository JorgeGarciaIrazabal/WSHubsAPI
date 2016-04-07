# coding=utf-8
import re

__author__ = 'Jorge'


def is_numeric(string):
    try:
        float(string)
        return True
    except:
        return False


def is_int(string):
    try:
        int(string)
        return True
    except:
        return False


def is_float(string):
    return is_numeric(string)


email_validator = re.compile(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]*$")


def is_email(string):
    return email_validator.match(string) is not None


phone_validator = re.compile(r"^(00|\+)\d{7,15}$")


def is_international_phone(string):
    return phone_validator.match(string) is not None


urlValidator = re.compile(
    r"""(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))""")
"""from http://daringfireball.net/2010/07/improved_regex_for_matching_urls"""


def is_url(string):
    return urlValidator.match(string) is not None


# street names


ipValidator = re.compile(r"^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){0,3}$")


def is_ip(string):
    return ipValidator.match(string) is not None
