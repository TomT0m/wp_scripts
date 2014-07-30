#! /usr/bin/python
#encoding: utf-8
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

	datapage = Page(site=site, title).itemPage()

	print("getting item {} for title {} ".format(datapage.name, title))

	#for label in item.labels:
	#	print(item.labels[label])

	print(datapage.labels["fr"])

if __name__ == "__main__":
	main()

