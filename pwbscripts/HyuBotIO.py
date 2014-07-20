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
    """base class to screen output message"""

    def __init__(self):
        self.outputted = 0

    def output(self, message):
        """outputs a message to console """
        self.outputted += 1
        pywikibot.output(message)

    def output_usage(self):
        pywikibot.output("wow : {}".format(self.outputted))

from pwbscripts import projects

class Reporter(object):
    '''class definition for Reporter'''
    @inject(page_factory=PageFactory, output=Outputter, config=Config)
    def __init__(self, page_factory, output, config):
        self._warnings_list = []
        self.page_factory = page_factory
        self.output_pagename = config
        self.outputter = outputter

    def output(self, text):
        """ method that both output to screen logger and saves the message"""
        self.add_warning(text)
        self.logger.output(text)

    def add_warning(self, warning):
        """appends a warning report to the message report in prevision of Final report"""
        self._warnings_list.append(warning)

    @property
    def warning_list(self):
        """ getter for warning list messages"""
        return self._warnings_list

    def final_report(self):
        #TODO: code
        pass
