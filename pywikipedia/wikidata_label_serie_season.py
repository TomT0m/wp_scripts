#! /usr/bin/python
#encoding: utf-8
""" 
Serie formatting in wikidata
"""


import pywikibot
# create a site object, here for en-wiki
import sys
import logging

def set_lang_label(page, serie_name, season_num, lang, descr):
	""" per language labelling """
	datas = page.get()
	if ('label' not in datas or 
		not datas['label'][lang] or 
		datas['label'][lang] == serie_name):
			page.setitem(summary=u"serie season label disambiguation",
				items={'type': u'item', 'label': 'en', 'value': '{} season {}'.format(serie_name, season_num) })
	else:
		logging.info("doing nothing")
		print("doing nothing")

def set_season_labels(page, serie_name, season_num):
	""" setting labels """
	set_lang_label(page, serie_name, season_num, 'en', '{} season {}'.format(serie_name, season_num))
	set_lang_label(page, serie_name, season_num, 'fr', '{} saison {}'.format(serie_name, season_num))


def main(serie_name, site_name = 'en' ):
	""" main """

	site = pywikibot.getSite(site_name)
	#  
	#  # create a Page object for en-wiki
	page = pywikibot.Page(site, serie_name)
	#  #  
	#  #  # Now we create the corresponding DataPage:
	data = pywikibot.DataPage(page)

	title_pattern = "{}_(season_{})"

	has_previous = True
	current = 1
	items = {}
	

	while has_previous:
		title = title_pattern.format(serie_name, current)
		page = pywikibot.Page(site, title)
		print(title)
		page = pywikibot.Page(site, title)
		if page.exists():
			datapage = pywikibot.DataPage(page)
			if datapage.exists():
				datapage.get()
				items[current] = datapage
			else:
				raise Exception()
			
		else:
			has_previous = False

		current += 1

	print("Number of seasons : {}".format(current))

	for i in range(1, len(items)):
		set_season_labels(items[i], serie_name, i)

main(sys.argv[1])

