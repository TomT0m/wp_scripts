
# coding : utf-8
from __future__ import unicode_literals

"""
Simple NIH symdrome class to describe and validate configuration file format
(found nothing worth the dependance making and the learning curve for my Goldberg Machine codestyle)

The grammar is self documented : each fragment is attached to an help string who describes the
file fragment purpose
"""


class FormatFragment(object):

    "A grammar rule for the yaml config file format"

    def __init__(self, name, help_msg):
        self._name = name
        self._help = help_msg
        self._type = None

    def validate(self, param_fragment):
        raise NotImplementedError

    def prettyString(self):
        """ utility function to format autodescription in a regular way """
        return "{name} [{type}] : {help}".format(name=self._name,
                                                 help=self._help,
                                                 type="{type}")

    def __str__(self):
        return self.prettyString().format("UnspecifiedFragment")

    @property
    def name(self):
        return self._name


class StringParamUnit(FormatFragment):

    "A terminal symbol in the config file parameter"

    def __init__(self, name, help_msg):
        FormatFragment.__init__(self, name, help_msg)
        self._type = "String"

    def __str__(self):
        return self.prettyString().format(type="String")


class StringEnumUnit(StringParamUnit):

    "A terminal symbol in the config file parameter"

    def __init__(self, name, help_msg):
        FormatFragment.__init__(self, name, help_msg)
        self._type = "String"

    def __str__(self):
        return self.prettyString().format(type="String")


class ObjectFragment(FormatFragment):

    "A map of named parameters"

    def __init__(self, name, help_msg, fragments_map):
        FormatFragment.__init__(self, name, help_msg)
        self._type = "Object"
        self._attributes = fragments_map

    def __str__(self):
        attribute_docs = ["   {}\n".format(attribute) for attribute in self._attributes]

        return "{header}:\n:{attr_list}".format(header=self.prettyString().format(type="Object"),
                                                attr_list="".join(attribute_docs))


class ListFragment(FormatFragment):

    "A list of fragments of some type"
    type = "List"

    def __init__(self, name, help_msg, item_type):
        FormatFragment.__init__(self, name, help_msg)

        self._type = "List [{}]".format(item_type.name)
