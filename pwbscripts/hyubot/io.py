
# coding:utf-8

""" Module for input/output for HuyBot : logging, wikipages put/get content, ...

    IO modules definition : used when constructing the Bot class with respect to the configuration :
 TestBot ; Simulation Bot ; Bot

"""

import pywikibot


from projects import Config


class Outputter(object):

    """base class to output message on screen or console"""

    def __init__(self):
        self.outputted = 0

    def output(self, message):
        """outputs a message to console """
        self.outputted += 1
        pywikibot.output(message)

    # def output_usage(self):
    #    pywikibot.output("wow : {}".format(self.outputted))


class PageFactory(object):

    """ How to get a WikiPage
    """

    def __init__(self, config):
        self._config = config

    def create_page(self, pagename):
        """ main page creation function """
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
