'''
Created on 29 janv. 2016

@author: tom
'''

from hyubot.io import Reporter, IOMod


class TestPage(object):
    """
    test object that does not really get and write on wiki pages
    """

    def get(self):
        """..."""
        pass

    def put(self):
        """..."""
        pass

    def exists(self):
        """ A test page always exists (?) """
        return True


class TestReporter(Reporter):

    '''class definition for Reporter'''

    def __init__(self, iomod):
        Reporter.__init__(self, iomod)

    def output(self, text):
        """ method that both output to screen logger and saves the message"""
        self.add_warning(text)
        self.iomod.output(text)

    def add_warning(self, warning):
        """appends a warning report to the message report in prevision of Final report"""
        self._warnings_list.append(warning)

    @property
    def warning_list(self):
        """ getter for warning list messages"""
        return self._warnings_list


class TestIOMod(IOMod):
    """ Standard module for logging, wikipage creation, ...
    includes a page factory
    """

    def __init__(self, *args, **kwargs):
        IOMod.__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs

    def createPage(self, *args, **kwargs):
        pass
