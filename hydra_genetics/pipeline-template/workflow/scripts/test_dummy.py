# vim: syntax=python tabstop=4 expandtab
# coding: utf-8

__author__ = "{{ author }}"
__copyright__ = "Copyright {{ year }}, {{ author }}"
__email__ = "{{ email }}"
__license__ = "GPL-3"


def test_dummy():
    from dummy import dummy
    assert dummy() == 1
