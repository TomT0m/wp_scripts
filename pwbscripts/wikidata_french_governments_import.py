#! /usr/bin/python --
#encoding: utf-8
""" 
Serie formatting in wikidata

TODO: * Handle serie season redirects not associated to any particular article
* Handle series with no items
* Use pywikibot infrastructure logging
"""


import pywikibot
# create a site object, here for en-wiki
# import logging

# NUM_CHANGED = 0

import wd_lib

from pywikibot import output as output
from pywikibot import NoPage as NoPage


from systemd import journal



ARTICLE = "Gouvernement_de_la_Défense_nationale"


__lang_patterns__ = {
    u"fr": {
        u"label": u'{name} saison {num}',
        u"description": u'saison {num} de la série télévisée « {name} »'
        
    },
    u"en": {
        u"label": u'{ordi} season of {name}',
        u"description": None
    }
} 


def set_season_labels(serie_page, season_page, serie_name, season_num):
    """ setting labels """

    datas = serie_page.get()

    #en
    enlabel = __lang_patterns__[u"en"][u"label"].format(name = serie_name, ordi = get_en_ordinal(season_num))
    wd_lib.set_for_lang(season_page, serie_name, u'en', enlabel, u"standard label setting")
    
    #fr
    if "fr" in datas["labels"]:
        frseriename = datas["labels"]["fr"]
    else:
        frseriename = serie_name

    frlabel = u'{name} saison {num}'.format(name = frseriename, num = season_num)
    wd_lib.set_for_lang(season_page, serie_name, u'fr', frlabel, u"standard label setting") 

    frdescription = u'saison {num} de la série télévisée « {name} »'.format(name = frseriename, num = season_num)
    if frseriename != serie_name:
        # correct a label set in english name when we got a french one
        wrongdescription = u'saison {num} de la série télévisée « {name} »'.format(name = serie_name, num = season_num)
    
        wd_lib.set_for_lang(season_page, wrongdescription, 
                           'fr', frdescription, u"standard fr label setting",
                            kind = 'descriptions')
        # end correction block
    
    wd_lib.set_for_lang(season_page, serie_name, 
                        'fr', frdescription, u"standard fr label setting", 
                        kind = 'descriptions')


def treat_serie(serie_name, site_name = 'en', main_page_name = None, num = None):
    """ main """

    if not main_page_name:
        main_page_name = serie_name
    

    site = pywikibot.Site(site_name, "wikipedia")
    output(u"======> Serie : {}, Page: {}".format(serie_name, main_page_name) )    
    serie_item = wd_lib.item_by_title(site, main_page_name)
    
    title_pattern = u"{}_(season_{})"

    has_previous = True
    current = 1
    items = {}

    if not num:
        num = 1000

    try:
        while has_previous and current <= num:
            title = title_pattern.format(serie_name, current)
            page = pywikibot.Page(site, title)
            output(title)
            if page.exists():
                datapage = pywikibot.ItemPage.fromPage(page)
                if datapage.exists():
                    datapage.get()
                    items[current] = datapage
                else:
                    raise NoPage("page do not exists")
                
                current += 1
            else:
                has_previous = False
    except NoPage:
        pass # doing nothing, TODO: mark and log

    num_season = current - 1

    output(u"=>Number of seasons : {}".format(num_season))
    
    for i in range(1, len(items) + 1):
        output("===> Saison {}\n".format(i))
        
        output(u"season {}, item: {}". format(i, items[i]))
        set_season_labels(serie_item, items[i], serie_name, i)
        if i > 1:
            wd_lib.set_previous(items[i], items[i-1])
        if i < num_season:
            wd_lib.set_next(items[i], items[i+1])
        # part of (P361): this item is a part of that item 
        wd_lib.maybe_set_claim(items[i], 361, serie_item)
        wd_lib.instance_of(items[i], wd_lib.item_by_title("fr", u"Saison (télévision)"))
        
        output("===> End of aison {} processing\n".format(i))
    
    output("======> End of serie (maybe) processing\n")

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

def logmain():
    """ main script function """
    
    if not sys.stdin.encoding:
        import codecs
        sys.stdin = codecs.getreader('utf-8')(sys.stdin)
    
    if not sys.stdout.encoding:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdin)
    
    opt_parse = create_options()
    opt = opt_parse.parse_args()

    if not opt.serie_name:
        opt_parse.print_help()
        exit(0)
    
    serie_name = u" ".join([ name.decode('utf-8')
                            for name in opt.serie_name])
    global ARTICLE
    ARTICLE = serie_name # remember for logging all errors    
    
    num = None
    if opt.max_num:
        num = opt.max_num
    
    if opt.main_page_name:
        treat_serie(serie_name, "en", opt.main_page_name.decode('utf-8'), num = num)
    else:
        treat_serie(serie_name, "en", num = num)

    output (u"Nombre de changements : {}".format(wd_lib.NUM_CHANGED) ) 
    return True

def main():
    """ plop """
    # journal.send("New serie name treatment")
    try:
        logmain()
    except Exception as err:
        journal.send("something went wrong for article {}".format(ARTICLE), ERROR=str(err))

main()


