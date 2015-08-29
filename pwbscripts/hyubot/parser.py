
# encoding:utf-8


"""

Huybot wikitext parsing and deconstructing module

"""

import re


class Delimiter(object):

    """
    Specifies start tag and end tag.

    class
    """

    def __init__(self, startTag='', endTag=None):
        """
        initialization of the begin and end delimiters
        used to extract a substring in a text
        """
        self.start = startTag
        self.end = endTag
        self._errors = None

    class EndTagMissing(Exception):

        """Exception launched when the page misses an end tag on parsing"""

        def __init__(self, message, Errors):
            Exception.__init__(self, message)

            self._errors = Errors

    def split(self, text):
        """
        in a text "plop<tagdebut>bidou<tagfin>plop2
        returns ["plop", "bidou", "plop2"]
        TODO: refactor

        """
        result = []

        if self.end is not None:

            result = re.split("({}|{})".format(self.start,
                                               self.end), text)
            if len(result) % 2 != 1:
                raise self.EndTagMissing("End tag '{}'".format(self.end), {"text": text})
        else:
            if self.start != "":
                result = text.split(self.start)
            else:
                result = [text]

        if self.start == "":
            return [""] + result
        return result

    def rebuild(self, string_list):
        """ I suppose this rebuild a splited string"""
        outside = True
        try:
            result = [string_list[0]]
        except IndexError:
            result = []
        for stringinstance in string_list[1:]:
            if outside:
                result.append(self.start)
            else:
                result.append(self.end)
            outside = not(outside and self.end)
            result.append(stringinstance)
        return ''.join(result)

    def expurge(self, text, explicit_end=False):
        """ returns the text without the tags and their content """
        string_list = self.split(text)
        outside = True
        result = [string_list[0]]
        for str_instance in string_list[1:]:
            outside = not outside
            if outside:
                result.append(str_instance)
        if explicit_end:
            if len(string_list) % 2 == 0:
                result.append(self.start)
                result.append(string_list[-1])
        return ''.join(result)

    def englobe(self, text):
        """ computes a wikitext str enclosed with the current tags"""
        return self.start + text + self.end


class HtmlTag(Delimiter):

    """
    HTML tags delimiters definition
    """

    def __init__(self, tagname):
        super(HtmlTag, self).__init__()
        self.start = '<{}>'.format(tagname)
        self.end = '</{}>'.format(tagname)

BOT_TAG = Delimiter('', '<!-- FIN BOT -->')
LINK_TAG = Delimiter('[[', ']]')

ARG_TAG = Delimiter('{{{', '}}}')

COMMENT_TAG = Delimiter('<!--', '-->')
INCLUDEONLY_TAG = HtmlTag('includeonly')
NOINCLUDE_TAG = HtmlTag('noinclude')
NOWIKI_TAG = HtmlTag('nowiki')


def get_reconstruct_errmsg_pattern():
    """ returns an error message pattern """
    err_msg_pattern = "Balise de début {} manquante; ou numéro de section {} trop élevé dans la page {}."
    return err_msg_pattern
