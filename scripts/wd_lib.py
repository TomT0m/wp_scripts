#coding: utf-8
"""
Library for script to manipulate Wikidata Data
"""

import time
import pywikibot

NUM_CHANGED = 0

def change_made():
    """ sleep to avoid spam alert"""
    global NUM_CHANGED
    if NUM_CHANGED % 3 == 0:
        time.sleep(30)
    NUM_CHANGED = NUM_CHANGED + 1

def set_for_lang(page, label_to_overload, lang, text, summary, kind = u'labels'):
    """ per language labelling of description 
    * kind == 'label' or kind == 'description' 
    * """
    datas = page.get()
    if kind != u'labels' and kind != u'descriptions': 
        raise ValueError('Unknow "kind" parameter, is "{}", should be labels or descriptions'.format(kind))
    
    try:
        # print(datas)
        print(u"Label: Current item label {} :".format(datas["label"][lang]))
        print(u"Label: Current interwiki in {} {}:".format(lang, datas["links"]["{}wiki".format(lang)]))
    except KeyError:
        print("Label : !! * nothing in language {}".format(lang))
    finally:
        pass
    pywikibot.output(u"Label: to overload: {}".format(label_to_overload)) 

    if (kind not in datas or 
        lang not in datas[kind] or 
        datas[kind][lang] == label_to_overload):
        
        if kind == 'labels':
            page.editLabels({ lang : text }, summary=summary)
        else:
            page.editDescriptions({ lang : text}, summary=summary)
        
        pywikibot.output(u"Set label of {} in {} : {}".format(get_q_number(page), lang, text) )
        
        # change_made()
    else:
        pywikibot.output(u"Label of {} in {} doing nothing".format(get_q_number(page), lang) )

def get_q_number(datapage):
    """ extracts the item number of a datapage"""
    return datapage.getID()[1:]

def get_claim_pairs(item):
    """ returns the list of claims for this item in format [(pnum, itemnum) *] """
    claims = item.get()["claims"]
    print(claims)
    pairs = [ (claims[prop][n].getID(), claims[prop][n].target) 
        for prop in claims for n in range(len(claims[prop]))]
    print(pairs)
    return pairs

def has_claim(item, prop_num, item_num):
    """ returns trus if item has a claim with prop_num property and item_num value"""
    return (prop_num, item_num) in get_claim_pairs(item) 

def maybe_set_claim(item_data, prop_num, value_item):
    """ sets a claim and maybe pauses """
    value_item_num = get_q_number(value_item)
    
    if not has_claim(item_data, prop_num, value_item_num):
        pywikibot.output("Setting claim <Q{}> P{} <Q{}>".format(get_q_number(item_data), prop_num, value_item_num))
        
        
        prop_p = pywikibot.PropertyPage(item_data.site, "P:P{}".format(prop_num))
        claim = prop_p.newClaim()
        claim.setTarget(value_item)
        item_data.addClaim(claim)
        
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
    if type(lang) == str:
        site = pywikibot.Site(lang, "wikipedia")
    else:
        site = lang
    page = pywikibot.Page(site, title)
    # repo = 
    datapage = pywikibot.ItemPage.fromPage(page)
    datapage.get()
    
    return datapage

def instance_of(item, class_):
    """ Sets the claim that item is an instance of claim """
    print(type(class_))
    print(type(item))
    maybe_set_claim(item, 31, class_)


def make_sequence(iterable, items_type = None):
    """ Makes a 'preceded / succeeded by claims from a sequence of items"""
    previous = None
    for item in iterable:
        print(type(item))
        if previous != None:
            set_previous(item, previous)
            set_next(previous, item)
        previous = item
        print(type(item))
        if items_type != None:
            instance_of(item, items_type)

