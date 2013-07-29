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

def set_for_lang(page, label_to_overload, lang, text, summary, kind = 'label'):
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
	
	try:
		print(datas)
		print(u"Current item label {} :".format(datas["label"][lang]))
		print(u"Current interwiki in {} {}:".format(lang, datas["links"]["{}wiki".format(lang)]))
	except KeyError:
		print("nothing in language {}".format(lang))
	finally:
		pass

	if (kind not in datas or 
		lang not in datas[kind] or 
		datas[kind][lang] == label_to_overload):
		
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

def make_sequence(iterable):
	""" Makes a 'preceded / succeeded by claims from a sequence of items"""
	i = 0
	previous = None
	for item in iterable:
		if previous != None:
			set_previous(item, previous)
			set_next(previous, item)
		previous = item


SOURCE="""<strong class="selflink">10000 – 10FFF</strong></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(11000-11FFF)" title="Table des caractères Unicode (11000-11FFF)">11000 – 11FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(12000-12FFF)" title="">12000 – 12FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(13000-13FFF)" title="">13000 – 13FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(14000-14FFF)" title="">14000 – 14FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(15000-15FFF)" title="">15000 – 15FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(16000-16FFF)" title="">16000 – 16FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(17000-17FFF)" title="">17000 – 17FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(18000-18FFF)" title="">18000 – 18FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(19000-19FFF)" title="">19000 – 19FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1A000-1AFFF)" title="">1A000 – 1AFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1B000-1BFFF)" title="Table des caractères Unicode (1B000-1BFFF)">1B000 – 1BFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1C000-1CFFF)" title="">1C000 – 1CFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1D000-1DFFF)" title="">1D000 – 1DFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1E000-1EFFF)" title="">1E000 – 1EFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1F000-1FFFF)" title="">1F000 – 1FFFF</a></li>
</ul>
</div>
</td>
</tr>
<tr>
<th colspan="2" style="text-align:center;background-color:#CEE0F2;color:#000000"><b>Autres plans Unicode</b></th>
</tr>
<tr>
<td></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(0000-0FFF)" title="">0000 – 0FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(0000-FFFF)" title="">plan 0 (BMP)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><strong class="selflink">10000 – 10FFF</strong></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(10000-1FFFF)" title="">plan 1 (SMP)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(20000-20FFF)" title="">20000 – 20FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(20000-2FFFF)" title="Table des caractères Unicode (20000-2FFFF)">plan 2 (SIP)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(30000-DFFFF)" title="">30000 – DFFFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(30000-DFFFF)" title=""><i>plans 3–13 (réservés)</i></a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(E0000-E0FFF)" title="">E0000 – E0FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(E0000-EFFFF)" title="Table des caractères Unicode (E0000-EFFFF)">plan 14 (SSP)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(F0000-F0FFF)" title="Table des caractères Unicode (F0000-F0FFF)">F0000 – F0FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(F0000-FFFFF)" title="">plan 15 (privé - A)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(100000-100FFF)" title="Table des caractères Unicode (100000-100FFF)">100000 – 100FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(100000-10FFFF)" title="">plan 16 (privé - B)</a>
"""

MAINS = [u"Table des caractères Unicode (0000-FFFF)",
u"Table des caractères Unicode (10000-1FFFF)",
u"Table des caractères Unicode (20000-2FFFF)",
u"Table des caractères Unicode (30000-DFFFF)",
u"Table des caractères Unicode (E0000-EFFFF)",
u"Table des caractères Unicode (F0000-FFFFF)",
u"Table des caractères Unicode (100000-10FFFF)"]

LESSER = """0000 0FFF
1000 1FFF
2000 2FFF
3000 3FFF
4000 4FFF
5000 5FFF
6000 6FFF
7000 7FFF
8000 8FFF
9000 9FFF
A000 AFFF
B000 BFFF
C000 CFFF
D000 DFFF
E000 EFFF
F000 FFFF"""


import re

def label(mi_, ma_):
	""" returns a calculated label from a range """
	return "caractères Unicode des points de code {} à {}".format(mi_, ma_)

def enlabel(mi_, ma_):
	""" returns a calculated label from a range """
	return "Unicode characters from {} to {} codepoints".format(mi_, ma_)

def frtitle(mi_, ma_):
	"""returns formated title """
	return u"Table des caractères Unicode ({}-{})".format(mi_, ma_)

def main():
	""" main script function """
	def extr_mini_maxi(titl):
		""" extract bounds from title"""
		res = re.split(u"[()-]", titl)
		return res[1], res[2]

	items  = [ item_by_title("fr", title)  for title in MAINS ]
	ranges = [ extr_mini_maxi(title) for title in MAINS ]

	all_items = items
	for item in items:
		print(item)

	make_sequence(items)

	for (item, rang_) in zip(items, ranges):
		(min_, max_) = rang_
		prefix = min_[0:-4]
		print ("====================='{}'========================".format(prefix))
		def gen_title(lrange):
			""" title gen"""
			mi_ = ('{}{}'.format(prefix, lrange.split(" ")[0]))
			ma_ = ('{}{}'.format(prefix, lrange.split(" ")[1]))
			# import pdb ; pdb.set_trace()
			return frtitle(mi_, ma_)
		titles = [  gen_title(lrange) for lrange in LESSER.split("\n") ]
		
		items  = [ item_by_title("fr", title) for title in titles ]
		ranges = [ extr_mini_maxi(title) for title in titles ]

		make_sequence(items)
		# suboptimal
		all_items = all_items + items

	for item in all_items:
		set_for_lang( item, u"Table des caractères Unicode", "fr", label(min_, max_), "ambiguity and label correction")
		set_for_lang( item, u"", "en", enlabel(min_, max_), "ambiguity and label correction")

if __name__ == "__main__": 
	main()



