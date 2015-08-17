#! /usr/bin/python --
# encoding: utf-8
"""
Serie formatting in wikidata

TODO: * Handle serie season redirects not associated to any particular article
* Handle series with no items
* Use pywikibot infrastructure logging
"""


from pywikibot import NoPage as NoPage
from pywikibot import output as output
import pywikibot
import sys


import wd_lib
import lang

import bots_commons


# create a site object, here for en-wiki
# import logging
# NUM_CHANGED = 0
ARTICLE = None


__lang_patterns__ = {
    "fr": {
        "label": '{name} saison {num}',
        "description": 'saison {num} de la série télévisée « {name} »'

    },
    "en": {
        "label": '{ordi} season of {name}',
        "description": None
    }
}


def set_season_labels(serie_page, season_page, serie_name, season_num):
    """ setting labels """

    datas = serie_page.get()

#     en
    enlabel = __lang_patterns__["en"]["label"]\
        .format(name=serie_name,
                ordi=lang.get_en_ordinal(season_num))
    wd_lib.set_for_lang(season_page, serie_name, 'en',
                        enlabel, "standard label setting")

#     fr
    if "fr" in datas["labels"]:
        frseriename = datas["labels"]["fr"]
    else:
        frseriename = serie_name

    frlabel = '{name} saison {num}'.format(name=frseriename, num=season_num)
    wd_lib.set_for_lang(season_page, serie_name, 'fr', frlabel, "standard label setting")

    frdescription = 'saison {num} de la série télévisée « {name} »'.format(name=frseriename, num=season_num)
    if frseriename != serie_name:
        # correct a label set in english name when we got a french one
        wrongdescription = 'saison {num} de la série télévisée « {name} »'.format(name=serie_name, num=season_num)

        wd_lib.set_for_lang(season_page, wrongdescription,
                            'fr', frdescription, "standard fr label setting",
                            kind='descriptions')
        # end correction block

    wd_lib.set_for_lang(season_page, serie_name,
                        'fr', frdescription, "standard fr label setting",
                        kind='descriptions')


def treat_serie(serie_name, site_name='en', main_page_name=None, num=None):
    """ main """

    if not main_page_name:
        main_page_name = serie_name

    site = pywikibot.Site(site_name, "wikipedia")
    output("======> Serie : {}, Page: {}".format(serie_name, main_page_name))
    serie_item = wd_lib.item_by_title(site, main_page_name)

    TITLE_PATTERN = "{}_(season_{})"

    has_previous = True
    current = 1
    items = {}

    if not num:
        num = 1000

    try:
        while has_previous and current <= num:
            title = TITLE_PATTERN.format(serie_name, current)
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
        pass  # doing nothing, TODO: mark and log

    num_season = current - 1

    output("=>Number of seasons : {}".format(num_season))

    for i in range(1, len(items) + 1):
        output("===> Saison {}\n".format(i))

        output("season {}, item: {}". format(i, items[i]))
        set_season_labels(serie_item, items[i], serie_name, i)
        if i > 1:
            wd_lib.set_previous(items[i], items[i - 1])
        if i < num_season:
            wd_lib.set_next(items[i], items[i + 1])
#          part of (P361): this item is a part of that item
        wd_lib.maybe_set_claim(items[i], 361, serie_item)
        wd_lib.instance_of(items[i], wd_lib.item_by_title("fr", "Saison (télévision)"))

        output("===> End of aison {} processing\n".format(i))

    output("======> End of serie (maybe) processing\n")


def create_options():
    """ Script option parsing """
    options = bots_commons.create_options()

    options.add_argument('-p', '--page',
                         help="optionally set a main title", metavar="PAGE", dest="main_page_name")

    options.add_argument('serie_name', nargs='*',
                         help="main serie name", metavar="SERIE_NAME"
                         )

    options.add_argument('-n', dest="max_num", type=int,
                         help="number of season to take into account", metavar="MAX_NUM"
                         )
    return options


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

    serie_name = " ".join([name.decode('utf-8')
                           for name in opt.serie_name])
    global ARTICLE
    ARTICLE = serie_name  # remember for logging all errors

    num = None
    if opt.max_num:
        num = opt.max_num

    if opt.main_page_name:
        treat_serie(serie_name, "en", opt.main_page_name.decode('utf-8'), num=num)
    else:
        treat_serie(serie_name, "en", num=num)

    output("Nombre de changements : {}".format(wd_lib.NUM_CHANGED))
    return True


def main():
    """ plop """
    # journal.send("New serie name treatment")
    try:
        logmain()
    except Exception as err:
        output("something went wrong for article {} ; error:<{ERROR}>".format(ARTICLE, ERROR=str(err)))
        # journal.send("something went wrong for article {}".format(ARTICLE), ERROR=str(err))

main()
