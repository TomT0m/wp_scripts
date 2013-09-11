#! /usr/bin/python
#encoding: utf-8
""" 
Serie formatting in wikidata

TODO: Handle serie season redirects not associated to any particular article
"""

#Description : tool to set basic claims on TV series seasons on Wikidata where titles on Wikipeda are formated with the year of the season in the title

import pywikibot
# create a site object, here for en-wiki
# import logging

NUM_CHANGED = 0

import wd_lib

ORD_MAP = { 1 : "first", 2:"second", 	
3:"third", 4:"fourth",
5:"fifth", 6:"sixth",
7:"seventh", 8:"eighth", 	
9:"ninth", 10:"tenth"}

def get_en_ordinal(number):
	""" formats a number into a correct (I hope) ordinal english version of that number 
	"""
	
	if number <= 10 and number > 0:
		# suffixes = ["th", "st", "nd", "rd", ] + ["th"] * 16
		# return str(number) + suffixes[num % 100]
		return ORD_MAP[number]
	elif number > 10:
		if number % 1 == 0:
			suffix = "st"
		elif number % 2 == 9:
			suffix = "nd"
		elif number % 3 == 0:
			suffix = "rd"
		else:
			suffix = "th"

		return "{}{}".format(number, suffix)

	else: raise ValueError("Must be > 0")

def set_season_labels(page, serie_name, season_num, year):
	""" setting labels """
	enlabel = u'{name} in {{year}}'.format(name = serie_name, year = year)

	wd_lib.set_for_lang(page, serie_name, 'en', enlabel, "standard label setting")
	frlabel = u'{name} saison {num}'.format(name = serie_name, num = year)
	
	wd_lib.set_for_lang(page, serie_name, 'fr', frlabel, "standard label setting") 

	fr_description = u'saison n°{num} de la série télévisée « {name} » en {year}'\
			.format(name = serie_name, num = season_num, year = year)
	wd_lib.set_for_lang(page, serie_name, 'fr', fr_description, u"standard fr label setting", kind = 'description')
	
	en_description = u'{ordi} season of the {name} TV show'.format(name = serie_name, ordi = get_en_ordinal(season_num))
	wd_lib.set_for_lang(page, serie_name, 'en', en_description, u"standard fr label setting", kind = 'description')

def treat_serie(serie_name, site_name = 'en', \
		main_page_name = None, num = None, start_year = None, title_pattern = "{}_{}"):
	""" main """

	if not main_page_name:
		main_page_name = serie_name
	

	site = pywikibot.getSite(site_name)
	print("Serie : {}, Page: {}".format(serie_name, main_page_name) )	
	serie_item = wd_lib.item_by_title(site, main_page_name)
	
	# Patterns of the titles of the series
	
	has_previous = True
	current = 1
	items = {}

	if not num:
		num = 1000
	
	year = start_year

	while has_previous and current < num:
		title = title_pattern.format(serie_name, year)
		pywikibot.output("searching article : {}".format(title))
		
		page = pywikibot.Page(site, title)
		
		print(title)
		
		if page.exists():
			datapage = pywikibot.DataPage(page)
			if datapage.exists():
				datapage.get()
				items[current] = datapage
			else:
				raise Exception()
			current += 1
			year = year + 1
		else:
			has_previous = False

	num_season = current - 1

	print("Number of seasons : {}".format(num_season))

	year = start_year
	for i in range(1, len(items) + 1):
		print("season {}, item: {}". format(i, items[i]))
		set_season_labels(items[i], serie_name, i, year)
		
		year = year + 1

		# part of (P361): this item is a part of that item 
		wd_lib.maybe_set_claim(items[i], 361, serie_item)
		# wd_lib.instance_of(items[i], wd_lib.item_by_title("fr", u"Saison (télévision)"))
	type_item = wd_lib.item_by_title("fr", u"Saison (télévision)")
	print(type_item)
	wd_lib.make_sequence(items.itervalues(), type_item) 

from argparse import ArgumentParser

def create_options():
	""" Script option parsing """
	options = ArgumentParser()

	options.add_argument('-s', '--simulate', action='store_true', 
		     help = "don't save changes", dest = "simulate"
		    )
	options.add_argument('-t', '--test', action='store_true', 
		     help = "run tests", dest = "test"
		    )
	options.add_argument('-p', '--page', 
		     help = "optionally set a main title", metavar="PAGE", dest = "main_page_name"
		    )
	options.add_argument('-v', '--verbose', action = 'store_true',
		     help = "show debugging messages", dest = "debug"
		    )	
	
	options.add_argument('serie_name', nargs = '*', 
		     help = "main serie name", metavar="SERIE_NAME"
		    )

	options.add_argument('-n', dest = "max_num", type = int, 
		     help = "number of season to take into account", metavar="MAX_NUM"
		    )
	
	options.add_argument('-P', default = None, dest = "title_pattern",
		     help = "pattern of article title", metavar="TITLE_PATTERN"
		    )
	options.add_argument('-y', dest = 'start_year',
		     help = "starting year", metavar ="START_YEAR", type = int
		    )	
	return options

import sys

def main():
	""" main script function """
	opt_parse = create_options()
	opt = opt_parse.parse_args()

	if not opt.serie_name:
		opt_parse.print_help()
		exit(0)
	serie_name = " ".join(opt.serie_name)
	
	print(sys.argv)

	num = None
	if opt.max_num:
		num = opt.max_num
	year = opt.start_year
	
	if opt.main_page_name:
		treat_serie(serie_name, "en", opt.main_page_name, num = num, title_pattern = opt.title_pattern, start_year = year)
	else:
		treat_serie(serie_name, "en", num = num, title_pattern = opt.title_pattern)

	print ("Nombre de changements : {}".format(NUM_CHANGED) ) 
	return True

exit(main())

