#! /usr/bin/python
# encoding: utf-8

"""
#Description: takes an english title and translates it into french
"""

from pywikibot.page import Page
import pywikibot

import sys


def main():
    """ main """
    title = sys.argv[1]
    site = pywikibot.getSite("en", "wikipedia")

    page = Page(site, title)
    datapage = pywikibot.ItemPage.fromPage(page)

    print("getting item {} for title {} ".format(datapage.name, title))

    print(datapage.labels["fr"])

if __name__ == "__main__":
    main()
