#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
#Description: Déplace les annonces de proposition de suppression de la page
 Projet:Informatique vers la page d'annonces du projet

"""


from __future__ import unicode_literals

# TODO: Fix duplicates announces bug.
# TODO: Fix fusion status.


import re
#from pwb import pwb


import pywikibot as pwb
import mwparserfromhell

from date import Date, extract_date
from projects import read_conffile
from page_status import get_page_status

# Constants

ANNOUNCE_DEL_TMPL = "Annonce proposition suppression"
ANNOUNCE_FUSION_TMPL = "Annonce fusion d'articles"

# Parsing functions



def msg_line_eating():
    """
    generates a pattern matching a complete line not beginning with '=='
    >>> opts = re.MULTILINE # | re.DEBUG
    >>> re.match(msg_line_eating(), "plop").group(0)
    u'plop'
    >>> re.match(msg_line_eating(), "p").group(0)
    u'p'
    >>> re.match(msg_line_eating(), "== plop ==")

    >>> re.match("([^=]|=?!=).*$", "aa").group(0)
    u'aa'
    >>> msg = "ab" + os.linesep + "b" + os.linesep + "==plop=="
    >>> re.match('(' +msg_line_eating() + ')*', msg, opts).group(0).split(os.linesep)
    [u'ab', u'b', u'']
    >>> msg = msg + os.linesep + os.linesep + "==plop==" + os.linesep
    >>> re.match('(' +msg_line_eating() + ')*', msg, opts).group(0).split(os.linesep)
    [u'ab', u'b', u'']
    """
    # newline_pattern = "(?:$\n)?^"
    not_eq_eq = "^(?:[^=]|=?!=)"

    return '(?:' + '^$\n?' + '|' + not_eq_eq + ".*$\n?" + ')'


def extract_full_del_props(text):
    """ Takes wikicode, returns a pair
    ([(title(str), Date)*], newtext)

    Searches deletion proposition generated with the standard ''full template'' form
    """
    pattern = """== L'article {} est proposé à la suppression ==$\n""" + '((?:' + msg_line_eating() + ')*' + ')'
    articles = []
    del_sum = 0

    for article in re.finditer(pattern.format(u'(.*)'), text, re.MULTILINE):
        date = extract_date(article.group(2))
        articles.append((article.group(1), date))
        del_sum += len(article.group(0))

        pwb.output(" Article : {} (annoncé le {})".format(article.group(1), date))
        pwb.output(" Annonce : \n'''{}'''".format(len(article.group(2))))

    del_pattern = pattern.format(u'.*')
    newpage = re.sub(del_pattern, '', text, flags=re.MULTILINE)

    pwb.debug("(taille en octets) : Supprimé {} - nouvelle : {}, ancienne {}, différence {}: "
                  .format(
                      del_sum,
                      len(newpage),
                      len(text),
                      del_sum - (len(text) - len(newpage)))
                  ,
              "bot")

    return (articles, newpage)


from wikitext.wikitext import Template

def format_del_announce(date, article_name):
    """ returns a mediawiki template text for a deletion announce"""

    announce = Template(ANNOUNCE_DEL_TMPL, posargs = [date], kwargs = {"nom": article_name})

    return unicode(announce)


def extract_fusion_articles(title):
    """ Extracts article titles from section title
    >>> title = '== Les articles [[Jasper]] et [[Jasper (informatique)]] sont proposés à la fusion =='
    >>> extract_fusion_articles(title)
    [u'Jasper', u'Jasper (informatique)']

    """
    lbegin = re.escape("[[")
    lend = re.escape("]]")
    match = re.findall("{}(.*?){}".format(lbegin, lend), title)
    return match


SAMPLE_FUSION_ANNOUNCE = """== Les articles [[Jasper]] et [[Jasper (informatique)]] sont proposés à la fusion ==
[[Image:Merge-arrows.svg|60px|left|Proposition de fusion en cours.]]

La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#Jasper et Jasper (informatique)]]. La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].

[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 25 juillet 2013 à 12:23 (CEST)
"""


def extract_link_to_fusionprops(section):
    """ Extracts the section in fusion prop global page from a (parsed) fusion prop section in Project Chat
    >>> parsed = mwparserfromhell.parse(SAMPLE_FUSION_ANNOUNCE)
    >>> extract_link_to_fusionprops(parsed)
    u'Wikipédia:Pages à fusionner#Jasper et Jasper (informatique)'
    """
    expected = section.filter_wikilinks(matches="Wikipédia:Pages à fusionner#")[0]
    return expected[2:-2]


def extract_fusion_props(text):
    """ returns a couple:

        (props, new_text)
        with props a triple:
            * article list
            * fusion section title in fusion page
            * date

    """

    parsed = mwparserfromhell.parse(text)

    sections = parsed.get_sections([2], matches="Les articles .*? sont proposés à la fusion")

    fusions = []

    for sect in sections:

        articles = extract_fusion_articles(sect.split("==")[1])
        date = extract_date(sect)
        link_to_discussion = extract_link_to_fusionprops(sect)

        fusions.append((articles, link_to_discussion, date))
        text = text.replace(unicode(sect), "")

    return (fusions, text)


def insert_new_announces(old_text, dated_new_announces):
    """ Creates a text with to_del_list announces inserted at timely sorted"""

    # découpage en utilisant les marqueurs de la section annonces dans la page

    sep_preamble = "------->"
    sep_end = "<noinclude>"

    (preamble, following) = old_text.split(sep_preamble, 1)
    (section_annonces, rest) = following.split(sep_end, 1)

    # prétraitement des annonces : création d'une liste de couple (template, Date)
    announces_lines = section_annonces.split("\n")

    dated_old_announces = [
        (text, extract_date(text))
        for text in announces_lines
        if text != ""
    ]

    # tri par date
    sorted_announces = sorted(dated_old_announces + dated_new_announces,
                              key=lambda (_, date): date, reverse=True)

    # création de la section finale

    new_section = Text("\n").join([text for text, _ in sorted_announces])

    return preamble + sep_preamble + "\n" + new_section + "\n" + sep_end + rest


def gen_month_announces(month):
    return "\n* ".join(month)


def gen_archives_page(old_archive_text, new_archived_announces):
    """ génère une page d'archive à partir de l'ancienne page et des nouvelles archives """

    announces_lines = old_archive_text.split("\n")

    dated_old_announces = [(text, extract_date(text))
                           for text in announces_lines if text != "" and text.strip()[:2] == "{{"]

    sorted_announces = sorted(dated_old_announces + new_archived_announces,
                              key=lambda (_, date): date, reverse=False)

    by_month = {month: [value for (date, value) in sorted_announces + dated_old_announces
                        if date.mois == month] for month in Date.MOIS
                }
    # new_text = reduce(, string.concat)

    new_text = "\n".join([
        "== {} ==\n{}\n".format(Date.MOIS[mois], gen_month_announces(by_month[mois]))
        for mois in by_month
    ])

    return new_text

# writing functions


def projects_maintenance(projects, options):
    """ Function launching maintenance for all projects """
    for project in projects:
        # TODO: log

        pwb.output("Project : " + project.name)

        deletion_prop_maintenance(project)
        fusion_prop_maintenance(project)

        print("> Diff des Annonces <\n")
        project.announce_page.show_diff()

        print("> Diff PDD <\n")
        project.discussion_page.show_diff()

        pwb.output("Simulate ? {}".format(options.simulate))

        pwb.output("> touched files : {} ; {}".format(project.discussion_page, project.announce_page))

        # Sauvegarde éventuelle #
        if not options.simulate:
            if project.discussion_page.modified:
                project.discussion_page.save()

            if project.announce_page.modified:
                project.announce_page.save()


import datas.test_data as tdata
ANNOUNCES_SAMPLE = tdata.ANNOUNCES_SAMPLE


def del_prop_iteration(page):
    """ iterator on deletion proposition announces in announce page

    >>>
    >>> liste = list(del_prop_iteration(mwparserfromhell.parse(tdata.ANNOUNCES_SAMPLE)))
    >>> liste[0].get("nom").value
    u'PagePlus'
    >>> len(liste)
    13
    >>> liste[0].name == ANNOUNCE_DEL_TMPL
    True
    """

    for tmpl in page.filter_templates():
        if tmpl.name == ANNOUNCE_DEL_TMPL:
            yield tmpl


def deletion_prop_status_update(announce_page):
    """ returns an updated announce page
    where deletion proposition annouce have been
    modified to reflect their real status (closed ?)
    """

    parsed = mwparserfromhell.parse(announce_page)

    for announce in del_prop_iteration(parsed):
        article_title = announce.get("nom").value
        pwb.output("-> {}".format(article_title))
        try:
            status = get_page_status(unicode(article_title))
            if status.is_deleted():
                announce.add(2, "supprimé")
            elif status.is_proposed_to_deletion():
                pwb.output("* still opened")
            elif status.is_redirect_page():
                announce.add(2, "fusionné")
                announce.add("fusionné_avec", status.redirected_to)
            else:
                if "fait" not in announce:
                    announce.add(2, "fait")
        except pwb.exceptions.InvalidTitle:
            pwb.log("Annonce malformée !! {}".format(article_title))

    return unicode(parsed)

from wikitext.wikitext import Text

def deletion_prop_maintenance(project):
    """ Real Action """

    # Récupération des données #

    announces_pagename = project.announce_pagename
    discussion_pagename = project.discussion_pagename

    discussion_text = project.discussion_page.get_content()
    announces_text = project.announce_page.get_content()

    # Traitements #

    # récupération des annonces noyées dans la PDD
    #
    (articles, new_discussion_text) = extract_full_del_props(discussion_text)

    # stats sur le diff entre page générée et page originale
    pwb.output("Before : {} ; After {} ; expected around {}"
                 .format(len(discussion_text),
                         len(new_discussion_text),
                         len(discussion_text) - len(articles) * 1200)
                 )

    pwb.output("Articles extraits")
    for elem in articles:
        (nom, date) = elem
        pwb.output("Date d'annonce : {} ; Article à supprimer : {}".format(date, nom))

    # insertions des annonces extraites dans la page d'annonce

    dated_new_announces = [
        (format_del_announce(Text(unicode(date)), name), date)
        for name, date in articles
    ]
    new_announces_text = insert_new_announces(announces_text, dated_new_announces)

    announce_commentP = "proposition(s) de suppression déplacée(s) depuis [[{disc_page}|La page de discussion]]"
    announce_comment = announce_commentP.format(disc_page=discussion_pagename)

    project.announce_page.set_content(new_announces_text, announce_comment)

    # mise à jour de l'état des annonces #

    new_announces_text = deletion_prop_status_update(new_announces_text)

    commentP = "Déplacements vers [[{announce_page}|la page d'annonces]]"
    comment = commentP.format(announce_page=announces_pagename)
    announce_comment = "Mise à jour de l'état de propositions de suppression"

    project.discussion_page.set_content(new_discussion_text, comment)
    project.announce_page.set_content(new_announces_text, announce_comment)

from wikitext.wikitext import Text as WikiText, Link as WikiLink, Template as WikiTmpl
from wikitext.wikitext import Pattern as WikiPattern


def format_fusion_props(articles, section, date):
    """ format a fusion proposition announce name

    >>> format_fusion_props(["a", "b"], "wow", Date(1, 1, 2001)

    """

    msgP = WikiPattern("{paf_link} entre {articles_links}")
    list_article_msgP = WikiPattern("{rest}{antepenultimate} et {last}")

    wikiannounce_PaF_link = WikiLink(section,
                                     WikiText("Proposition de fusion"))

    all_links = [WikiLink(name) for name in articles]
    (antepenultimate, last) = (all_links[-2], all_links[-1])

    list_article_msg = list_article_msgP.format(rest=Text(", ").join(all_links[:-2]),
                                                antepenultimate=antepenultimate,
                                                last=last)
    msg = msgP.format(paf_link=wikiannounce_PaF_link, articles_links=list_article_msg)

    return WikiTmpl(ANNOUNCE_FUSION_TMPL, [msg, date])


def fusion_prop_maintenance(project):
    """ Testing """
    pwb.output("gestion des propositions de fusion ...")
    (fusion_prop_list, new_d_text) = extract_fusion_props(project.discussion_page.get_content())

    if len(fusion_prop_list) > 0:
        dated_new_announces = [(format_fusion_props(*elem), elem[2]) for elem in fusion_prop_list]
        new_a_text = insert_new_announces(project.announce_page.get_content(), dated_new_announces)

        fusion_msgP = "Déplacement d'annonces de proposition de fusion depuis la [[{}|La PDD]]"

        project.announce_page.set_content(new_a_text,
                                          fusion_msgP.format(project.discussion_pagename))

        msgP = "Déplacement des annonces de proposition fusion vers [[{}|La page d'annonce]] "
        project.discussion_page.set_content(new_d_text,
                                            msgP.format(project.announce_pagename))


# CLI management, UI

from bots_commons import create_options

#############################################################
# testing

import unittest

from unittest import TestCase


class Test(TestCase):

    """ Test cases : test of deletion proposition extraction"""

    def test_extraction(self):
        """ Simple test """
        text = SAMPLE_TEXT
        (articles, new_text) = extract_full_del_props(text)
        self.assertTrue("Feteke" not in new_text)
        (nom, date) = articles[0]
        self.assertEqual(nom, "Jean-Daniel Fekete")
        self.assertEqual(date, Date(3, "janvier", 2013))

    def count_titles(self, text):
        """ count wiki section titles in a text """
        return len([line for line in text.split("\n")
                    if "==" in line
                    ])

    def test_real(self):
        """ Real World extraction """
        import datas.test_data as datas
        text = datas.FULL_TEST
        num_titles = self.count_titles(text)
        (articles, new_text) = extract_full_del_props(text)
        new_num_titles = self.count_titles(new_text)
        self.assertEqual(num_titles, len(articles) + new_num_titles)


def test_doctest():
    """ testing doctests string """
    print("\ndoctests ...")
    import doctest
    doctest.testmod()
    print("/doctests")


def test():
    """ unittest launching :
        * TestCases from unittest module,
        * docstring tests
    """
    import sys

    test_doctest()
    unittest.main(argv=[sys.argv[0]])

from bots_commons import get_default_configfile

def main():
    """ Main function"""
    opt_parse = create_options()
    opts = opt_parse.parse_args()

    if opts.debug:
        #pwb.logging.basicConfig(level=logging.DEBUG)
        #TODO: call the relevant Bot class method
        pass
    if opts.test:
        test()
    else:
        # paramètres par defaut : "Projet:Informatique", False
        if opts.conffile:
            conffile = opts.conffile
        else:
            conffile = get_default_configfile()

        projects = [project
                    for project in read_conffile(conffile)
                    if "announces" in project.tasks
                    ]
        projects_maintenance(projects, opts)

from datas import test_data

SAMPLE_TEXT = test_data.SAMPLE_TEXT

####
####
# Tests samples


if __name__ == "__main__":
    main()
