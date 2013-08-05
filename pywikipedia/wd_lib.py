
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


def make_sequence(iterable):
	""" Makes a 'preceded / succeeded by claims from a sequence of items"""
	i = 0
	previous = None
	for item in iterable:
		if previous != None:
			set_previous(item, previous)
			set_next(previous, item)
		previous = item

