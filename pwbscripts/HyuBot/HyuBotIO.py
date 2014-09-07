import pywikibot

from snakeguice.modules import Module

# IO modules definition : used when constructing the Bot class with respect to the configuration :
# TestBot ; Simulation Bot ; Bot

class IOModule(Module):
    """IOModule interface

    IOModule binds WikiPages objects for actual runs to the Logger and Pages classes
    of the Wikibots

    Useful for tests and for simulation runs

    """
    def configure(self, linker):
        pass


class SimulateIOModule(IOModule):
    """ IO not saving on Wikipedia pages, but rather putting pages elsewhere"""
    def configure(self, linker):
        pass

class Outputter(object):
    """base class to output message on screen or console"""

    def __init__(self):
        self.outputted = 0

    def output(self, message):
        """outputs a message to console """
        self.outputted += 1
        pywikibot.output(message)

    def output_usage(self):
        pywikibot.output("wow : {}".format(self.outputted))

from pwbscripts.projects import Config
from snakeguice import inject

class PageFactory(object):
    @inject(config=Config)
    def __init__(self, config):
        self._config = config

    def create_page(self, pagename):
        pass

class WikipageFactory(PageFactory):
    pass

def agreement(question, default):
    print("{} (y/n), default : {}".format(question, default))
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
