#! /usr/bin/python --
# encoding: utf-8

"""
Serie formatting in wikidata

TODO: * Handle serie season redirects not associated to any particular article
* Handle series with no items
* Use pywikibot infrastructure logging
"""

import pywikibot
# create a site object, here for en-wiki
# import logging

# NUM_CHANGED = 0

import wd_lib

from pywikibot import output as output
from pywikibot import NoPage as NoPage


# from systemd import journal


ARTICLE = "Gouvernement_de_la_Défense_nationale"

def main():
    """ plop """
    # journal.send("New serie name treatment")

    #TODO: follow Gouvernement_de_la_Défense_nationale links

main()


