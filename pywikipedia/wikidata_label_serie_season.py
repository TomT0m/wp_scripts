#! /usr/bin/python
#encoding: utf-8
""" 
Serie formatting in wikidata

TODO: Handle serie season redirects not associated to any particular article
"""


import pywikibot
# create a site object, here for en-wiki
import time
import logging

NUM_CHANGED = 0

def change_made():
	""" sleep to avoid spam alert"""
	global NUM_CHANGED
	if NUM_CHANGED % 3 == 0:
		time.sleep(30)
	NUM_CHANGED = NUM_CHANGED + 1

def set_lang(page, serie_name, lang, text, kind = 'label'):
	""" per language labelling of description 
	* kind == 'label' or kind == 'description' 
	* """
	datas = page.get()
	if kind == 'label': 
		type_ = u'item'
		lng_param = u'label'
	elif kind == 'description': 
		type_ = kind
		lng_param = u'language'	
	else:
		raise ValueError('Unknow kind parameter, should be item or description')

	print datas

	if (kind not in datas or 
		lang not in datas[kind] or 
		datas[kind][lang] == serie_name):
		
		page.setitem(summary=u"serie season label disambiguation",
				items={'type': type_, lng_param: lang, 'value': text })
		change_made()
	else:
		logging.info("doing nothing")
		print("doing nothing")

def set_season_labels(page, serie_name, season_num):
	""" setting labels """
	set_lang(page, serie_name, 'en', '{name} season {num}'.format(name = serie_name, num = season_num))
	
	set_lang(page, serie_name, 'fr', '{name} saison {num}'.format(name = serie_name, num = season_num))
	
	set_lang(page, serie_name, 'fr', 
	 u'saison {num} de la série télévisée « {name} »'.format(name = serie_name, num = season_num),
	 kind = 'description')

def get_q_number(datapage):
	""" extracts the item number of a datapage"""
	return datapage.get()[u"entity"][1]

def get_claim_pairs(item):
	""" returns the list of claims for this item in format [(pnum, itemnum) *] """
	claims = item.get()["claims"]
	return [ (claims[plop]["m"][1], claims[plop]["m"][3][u"numeric-id"]) 
	 	for plop in range(len(claims)) ]

def has_claim(item, prop_num, item_num):
	""" returns trus if item has a claim with prop_num property and item_num value"""
	return (prop_num, item_num) in get_claim_pairs(item) 

def maybe_set_claim(item_data, prop_num, value_item):
	""" sets a claim and maybe pauses """
	if not has_claim(item_data, prop_num, get_q_number(value_item)):
		item_data.editclaim(prop_num, get_q_number(value_item))
		change_made()

def set_previous(season, previous):
	""" sets a 'preceded by' claim """
	# P155
	maybe_set_claim(season, 155, previous)

def set_next(season, next_season):
	""" sets a 'followed by' claim """
	# P156
	maybe_set_claim(season, 156, next_season)


def item_by_title(lang, title):
	""" returns the item assiciated to an article title """
	page = pywikibot.Page(lang, title)
	datapage = pywikibot.DataPage(page)
	datapage.get()
	return datapage

def instance_of(item, class_):
	""" Sets the claim that item is an instance of claim """
	maybe_set_claim(item, 31, class_)

def treat_serie(serie_name, site_name = 'en', main_page_name = None, num = None):
	""" main """

	if not main_page_name:
		main_page_name = serie_name
	

	site = pywikibot.getSite(site_name)
	print("Serie : {}, Page: {}".format(serie_name, main_page_name) )	
	serie_item = item_by_title(site, main_page_name)
	
	title_pattern = "{}_(season_{})"

	has_previous = True
	current = 1
	items = {}

	if not num:
		num = 1000

	while has_previous and current < num:
		title = title_pattern.format(serie_name, current)
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
		else:
			has_previous = False

	num_season = current - 1

	print("Number of seasons : {}".format(num_season))
	
	for i in range(1, len(items) + 1):
		print("season {}, item: {}". format(i, items[i]))
		set_season_labels(items[i], serie_name, i)
		if i > 1:
			set_previous(items[i], items[i-1])
		if i < num_season:
			set_next(items[i], items[i+1])
		# part of (P361): this item is a part of that item 
		maybe_set_claim(items[i], 361, serie_item)
		instance_of(items[i], item_by_title("fr", u"Saison (télévision)"))

from argparse import ArgumentParser

def create_options():
	""" Script option parsing """
	options = ArgumentParser()

	options.add_argument('-s', '--simulate', action='store_true', 
		    help = "don't save changes", dest = "simulate")
	options.add_argument('-t', '--test', action='store_true', 
		    help = "run tests", dest = "test")
	options.add_argument('-p', '--page', 
		    help = "optionally set a main title", metavar="PAGE", dest = "main_page_name"
		    )
	options.add_argument('-v', '--verbose', action = 'store_true',
		    help = "show debugging messages", dest = "debug")	
	
	options.add_argument('serie_name', nargs = '*', 
		    help = "main serie name", metavar="SERIE_NAME"
		    )

	options.add_argument('-n', dest = "max_num", type = int, 
		    help = "number of season to take into account", metavar="MAX_NUM"
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

	if opt.main_page_name:
		treat_serie(serie_name, "en", opt.main_page_name, num = num)
	else:
		treat_serie(serie_name, "en", num = num)

	print ("Nombre de changements : {}".format(NUM_CHANGED) ) 
	return True

exit(main())


