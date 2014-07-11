import pywikibot


class Outputer(object):
    def __init__(self):
        self._warnings_list = {}

    def output(self, text):
        pywikibot.output(text)
        self._warnings_list.append(text)

    @property
    def warning_list(self):
        return self._warnings_list
