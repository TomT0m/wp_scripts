#! /usr/bin/python
""" 
Serie formatting in wikidata
"""


import pywikibot
# create a site object, here for en-wiki
import sys



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
		print(page.get())
		print("plop")
		if page.exists():
			datapage = pywikibot.DataPage(page)
			if datapage.exists():
				items[current] = datapage.get()
				current += 1
			else:
				raise Exception()
		else:
			has_previous = False
	print("Number of seasons : {}".format(current))

main(sys.argv[1])

