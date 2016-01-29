
# coding:utf-8

""" Module for input/output for HuyBot : logging, wikipages put/get content, ...

    IO modules definition : used when constructing the Bot class with respect to the configuration :
 TestBot ; Simulation Bot ; Bot

"""


class Reporter(object):
    '''class definition for Reporter'''

    def __init__(self, iomod):
        self._warnings_list = []
        self.iomod = iomod

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


class IOMod(object):
    """ Standard module for logging, wikipage creation, ...
    includes a page factory
    """

    def __init__(self, *args, **kwargs):

        self.args = args
        self.kwargs = kwargs

    def createPage(self, *args, **kwargs):
        pass


def agreement(question, default):
    """
    huybot function that asks for the user agreement to proceed
    """
    print(("{} (y/n), default : {}".format(question, default)))
    invalid_input = True
    while invalid_input:
        rep = input()
        if rep in ['y', 'n', '']:
            invalid_input = False

    if rep == 'y':
        retval = True
    if rep == 'n':
        retval = False
    if rep == '':
        retval = default

    return retval
