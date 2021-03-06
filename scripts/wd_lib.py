
#coding: utf-8
"""
Library for script to manipulate Wikidata Data
"""

# import time
import pywikibot

from pywikibot import output as output
from pywikibot.data.api import APIError

NUM_CHANGED = 0

def change_made():
    """ sleep to avoid spam alert"""
    global NUM_CHANGED
    # if NUM_CHANGED % 3 == 0:
    #    time.sleep(30)
    NUM_CHANGED = NUM_CHANGED + 1

def set_for_lang_aux(page, label_to_overload, lang, text, summary, kind = u'labels'):
    """ per language labelling of description 
    * kind == 'label' or kind == 'description' 
    * """
    
    output("===>>>> new label ===")
    
    # TODO: reload because of concurrency access problems
    page = reloaditempage(page)
    datas = page.get()
    
    if kind != u'labels' and kind != u'descriptions': 
        raise ValueError('Unknow "kind" parameter, is "{}", should be labels or descriptions'.format(kind))
   
    try:
        to_output = u"> {}: Current item label {} :".format(kind, datas[kind][lang])
        output(to_output)
    except KeyError:
        output(u"> Label: Nothing in language {}".format(lang))
        

    pywikibot.output(u"Edit {}: to overload: {}".format(kind, label_to_overload)) 

    if (kind not in datas or 
        lang not in datas[kind] or 
        (datas[kind][lang] == label_to_overload)
            and datas[kind][lang] != text):
        
        if kind == 'labels':
            page.editLabels({ lang : text }, summary=summary)
            change_made()
        else:
            output(u"|>>>>!Editing descriptions in {} with {}".format(lang, text))
            page.editDescriptions({ lang : text}, summary=summary)
            change_made()

        pywikibot.output(u"|>>>! Set label of {} in {} : {}".format(get_q_number(page), lang, text) )
        
    else:
        pywikibot.output(u"|>>> Label of {} in {}, nothing done.".format(get_q_number(page), lang) )

    output("===> End of label processing ===")

def reloaditempage(itempage):
    """ reload the datas of a page if needed"""

    #page = pywikibot.ItemPage(itempage, itempage.data_repository)
    
    itempage.get(force=True)
    return itempage

def set_for_lang(page, label_to_overload, lang, text, summary, kind = u'labels', depth=0):
    """ wrapper """
    try:
        set_for_lang_aux(page, label_to_overload, lang, text, summary, kind=kind)
    except APIError as err:
        if u"editconf" in str(err):
            output("|>>>>!!!!!!!!!!!!!!!!!! Editconflict, retrying ......")
            print("Nombre d'essais: {}, err : {}".format(depth, err))
            # reloading page 
            page = reloaditempage(page) 
            set_for_lang(page, label_to_overload, lang, text, summary, kind=kind, depth=depth+1 )
        else:
            raise err

def get_q_number(datapage):
    """ extracts the item number of a datapage"""
    return datapage.getID()[1:]

def get_claim_pairs(item):
    """ returns the list of claims for this item in format [(pnum, itemnum) *] """
    datas = item.get()
    claims = datas['claims']
    pairs = [ (claims[prop][n].getID(), claims[prop][n].target) 
        for prop in claims for n in range(len(claims[prop]))]
    
    return pairs

def has_claim(item, prop_num, item_num):
    """ returns trus if item has a claim with prop_num property and item_num value"""
    return (prop_num, item_num) in get_claim_pairs(item) 

def maybe_set_claim(item_data, prop_num, value_item):
    """ sets a claim and maybe pauses """
    try:
        value_item_num = get_q_number(value_item)
    
        if not has_claim(item_data, "P{}".format(prop_num), value_item):
            pywikibot.output("Setting claim <Q{}> P{} <Q{}>".format(get_q_number(item_data), prop_num, value_item_num))
        
        
            prop_p = pywikibot.PropertyPage(item_data.site, "P:P{}".format(prop_num))
            claim = prop_p.newClaim()
            claim.setTarget(value_item)
            item_data.addClaim(claim)
        
            change_made()
    except APIError as err:
        if "ediconflict" in str(err):
            
            output("editconflict ????, retrying")
            output("=====>".format(err))
            # TODO : FIX reload
            item_data = reloaditempage(item_data),
            maybe_set_claim( item_data, prop_num, value_item)
        else:
            raise

def set_previous(season, previous):
    """ sets a 'preceded by' claim """
    # P155
    maybe_set_claim(season, 155, previous)

def set_next(season, next_season):
    """ sets a 'followed by' claim """
    # P156
    maybe_set_claim(season, 156, next_season)


def item_by_title(lang, title, datasite = None):
    """ returns the item assiciated to an article title """
    
    if type(lang) == str:
        if lang != "wikidata":
            site = pywikibot.Site(lang, "wikipedia")
        else:
            site = pywikibot.site.DataSite("wikidata", "wikidata")
    elif datasite != None:
        site = datasite
    else:
        site = lang
    
    datapage = None 
    if lang == "wikidata":
        #print(title)
        print(site)
        datapage = pywikibot.ItemPage(site, title)
    else:
        page = pywikibot.Page(site, title)
        datapage = pywikibot.ItemPage.fromPage(page)
    datapage.get()
    
    return datapage

def instance_of(item, class_):
    """ Sets the claim that item is an instance of claim """
    maybe_set_claim(item, 31, class_)


def make_sequence(iterable, items_type = None):
    """ Makes a 'preceded / succeeded by claims from a sequence of items"""
    previous = None
    for item in iterable:
        if previous != None:
            set_previous(item, previous)
            set_next(previous, item)
        previous = item
        if items_type != None:
            instance_of(item, items_type)

