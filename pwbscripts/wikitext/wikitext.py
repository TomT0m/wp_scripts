#! /usr/bin/python
# coding: utf-8

"""
Wikitext generation lib
"""


def wikiconcat(wikitexts):
    """ concatenates fragments of wikitext"""
    return CompositeText(wikitexts)


class Wikicode(object):

    """
    Base class to ensure instances of Wikitext are actually instances of this class.
    Helps ensuring the inputs have been validated
    """

    def __add__(self, arg):
        assert isinstance(arg, Wikicode)

        return wikiconcat([self, arg])

    reserved = {"{{", "}}", "[[", "]]", "|"}
    reserved_chars = "{|}"

    @classmethod
    def get_reserved_sequences(cls):
        """ returns interpreted sequences in template expansion"""
        return cls.reserved

    @classmethod
    def get_reserved_chars(cls):
        """ returns invalid chars in page or template name"""
        return cls.reserved_chars

    def __str__(self):
        pass


def isvalidtitle(title):
    """
    returns true if the title do not contains invalid characters
        TODO: make this more accurate ?
    """
    return all([char not in title for char in Wikicode.reserved_chars])


class Template(Wikicode):

    "Class for a WikiTemplate representation"

    begin_delimiter = "{{"
    end_delimiter = "}}"

    def __init__(self, name, posargs=None, kwargs=None):
        self._name = name
        self._posargs = posargs or []
        self._kwargs = kwargs or {}
        assert self.is_validid(name)

    @staticmethod
    def is_validid(name):
        """
        checks the validity of the name
        """
        return isvalidtitle(name)

    def __str__(self):
        return self.begin_delimiter + str(self._name) + self._format_args() + self.end_delimiter

    @staticmethod
    def _fmt_keyval(key, val):
        "format a key/val argument pairs to the template for the template call"
        return "{}={}".format(key, val)

    def _format_args(self):
        """utility function : format arguments to be printed as Wikitext template call"""

        pargs = self.posargs
        kwargs = self.kwargs
        if len(pargs) + len(kwargs) > 0:
            return "|" + "|".join(
                [self._fmt_keyval(i + 1, pargs[i]) for i in range(len(pargs))]
                +
                [self._fmt_keyval(key, val) for (key, val) in list(self._kwargs.items())]
            )
        else:
            return ""

    @property
    def posargs(self):
        """returns the list of positional arguments to the template"""
        return self._posargs

    @property
    def kwargs(self):
        """returns the dict of positional arguments to the template"""
        return self._posargs


class Text(Wikicode):

    """Pure text"""

    def __init__(self, value):
        self._value = self.escape(value)

    @staticmethod
    def escape(text):
        """escape pure text"""

        # TODO: more to escape probably (idea : collect them by class attributes and get them from Base class

        return text.replace("|", "{{!}}")

    def __str__(self):
        return str(self.text)

    def __repr__(self):
        return "Text({})".format(self.text)

    @property
    def text(self):
        """the plain content of the string, escaped"""
        return self._value

    def join(self, args):
        """The join method for wikiTexts
        * args : a list of WikiCode objects
        """
        return wikiconcat([self + arg for arg in args])


class CompositeText(Wikicode):

    """ Wikitext mixing correctly escaped strings and sanitized generated template calls or links"""

    def __init__(self, fragments):

        for fragment in fragments:
            # Yes, I '''want to''' do this :) the whole point is to assucre everything has been constructed correctly
            # to ensure class invariant properties
            assert isinstance(fragment, Wikicode)

        self._fragments = fragments

    def __str__(self):
        return "".join([str(fragment) for fragment in self._fragments])

    def __unicode__(self):
        return "".join([str(fragment) for fragment in self._fragments])

    def __repr__(self):
        first = self._fragments[0]
        return "TextWithTemplate({first}{next})".format(
            first=first, next=["," + fragment for fragment in self._fragments[1:]]
        )

    @property
    def fragments(self):
        """returns a table of the fragments"""
        return self._fragments

    def type(self):
        """ type : the method returning the object kind of plop"""
        return "Composite"


class Link(Wikicode):

    """WikiLink code management class"""

    def __init__(self, pagename, text=None):
        # TODO: validate pagename
        assert "|" not in pagename

        self._pagename = pagename
        self._displayed = text
        if text is not None:
            assert isinstance(text, Wikicode)

    def __repr__(self):
        if self._displayed:
            return "Link({}, {:r})".format(self._pagename, self._displayed)
        else:
            return "Link({})".format(self._pagename)

    def __str__(self):
        if self._displayed:
            return "[[{}|{}]]".format(self._pagename, self._displayed)
        else:
            return "[[{}]]".format(self._pagename)


class InvalidPattern(Exception):

    """Exception to be raised when the user creates a pattern:
    * with reserved strings subsequences
    """

    def __init__(self, pattern, msg):
        Exception.__init__(self, msg)
        self._pattern = pattern
        self._msg = msg

    def __repr__(self):
        return "InvalidPattern({}, {})".format(self._pattern, self._msg)

    def __str__(self):
        return "{} : Invalid Pattern. {}".format(self._pattern, self._msg)


class _Formated(Wikicode):

    """ class to store text built with a pattern """

    def __init__(self, text):
        self._text = text

    def __unicode__(self):
        return self._text


class Pattern(object):

    """Patterns to be expanded
    TODO: use python mechanisms
    """

    def __init__(self, pattern):
        self._pattern = pattern

        reserved_in_pattern = [reserved for reserved in Wikicode.reserved
                               if reserved in pattern
                               ]
        if len(reserved_in_pattern) > 0:
            out_reservered = ['"{}"'.format(reserved for reserved in reserved_in_pattern)]
            raise InvalidPattern(pattern,
                                 "found reserved {first}{rest}".format(first=out_reservered[0],
                                                                       rest=", ".join(out_reservered[1:])
                                                                       )
                                 )

    @property
    def pattern(self):
        """ getter for the pattern """
        return self._pattern

    def format(self, *args, **kwargs):
        "main class method"
        return _Formated(self.pattern.format(*args, **kwargs))
