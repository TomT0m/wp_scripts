
# coding:utf-8


class Delimiter:

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

    def indices(self, txt, textFrom=0):
        """ computes the indexes of the substring delimited by the start and end delimiters

        (or (StartIndex, None) if there is no end delimiters
        """
        startIndex = txt.index(self.start, textFrom)
        if self.end:
            try:
                endIndex = txt.index(self.end, startIndex + len(self.start))
            except ValueError:
                endIndex = None
        else:
            endIndex = None
        return (startIndex, endIndex)

    class EndTagMissing(Exception):
        def __init__(self, message, Errors):
            Exception.__init__(self, message)

            self.Errors = Errors

    def split(self, text):
        result = []
        index = 0
        try:
            while 1:
                (startIndex, endIndex) = self.indices(text, index)
                result.append(text[index:startIndex])
                result.append(text[startIndex + len(self.start):endIndex])
                index = endIndex + len(self.end)
        except ValueError:
            result.append(text[index:])
        except TypeError:
            if self.end:
                raise self.EndTagMissing("End tag '{}'".format(self.end), {"text": text})

        return result

    def rebuild(self, stringList):
        outside = True
        try:
            result = [stringList[0]]
        except IndexError:
            result = []
        for s in stringList[1:]:
            if outside:
                result.append(self.start)
            else:
                result.append(self.end)
            outside = not(outside and self.end)
            result.append(s)
        return ''.join(result)

    def expurge(self, text, explicitEnd=False):
        stringList = self.split(text)
        outside = True
        result = [stringList[0]]
        for s in stringList[1:]:
            outside = not(outside)
            if outside:
                result.append(s)
        if explicitEnd:
            if len(stringList) % 2 == 0:
                result.append(self.start)
                result.append(stringList[-1])
        return ''.join(result)

    def englobe(self, text):
        return self.start + text + self.end


class HtmlTag(Delimiter):

    """
    HTML tags delimiters definition
    """

    def __init__(self, s):
        self.start = '<%s>' % s
        self.end = '</%s>' % s

bot_tag = Delimiter(u'', u'<!-- FIN BOT -->')
link_tag = Delimiter(u'[[', u']]')

arg_tag = Delimiter(u'{{{', u'}}}')

comment_tag = Delimiter(u'<!--', u'-->')
includeonly_tag = HtmlTag('includeonly')
noinclude_tag = HtmlTag('noinclude')
nowiki_tag = HtmlTag('nowiki')


def get_reconstruct_errmsgP():
    err_msgP = u"Balise de début {} manquante; ou numéro de section {} trop élevé dans la page {}."
    return err_msgP
