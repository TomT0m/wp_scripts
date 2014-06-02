#! /usr/bin/python
# -*- coding: UTF-8 -*-
"""
#Description: Déplace les annonces de proposition de suppression de la page Projet:Informatique vers la page d'annonces

"""

#TODO: Fix duplicates announces bug.
#TODO: Fix fusion status.

import re, logging

import pywikibot
import mwparserfromhell

from date import Date, extract_date
from project_parameters import ProjectParameters
from projects import read_conffile
from page_status import get_page_status

# Constants

ANNOUNCE_DEL_TMPL = "Annonce proposition suppression"
ANNOUNCE_FUSION_TMPL = "Annonce fusion d'articles"

# Parsing functions

#pylint: disable=W0611
import os

def msg_line_eating():
    """
    generates a pattern matching a complete line not beginning with '=='
    >>> opts = re.MULTILINE # | re.DEBUG
    >>> re.match(msg_line_eating(), "plop").group(0)
    'plop'
    >>> re.match(msg_line_eating(), "p").group(0)
    'p'
    >>> re.match(msg_line_eating(), "== plop ==")

    >>> re.match(u"([^=]|=?!=).*$", u"aa").group(0)
    u'aa'
    >>> msg = "ab" + os.linesep + "b" + os.linesep + "==plop=="
    >>> re.match('(' +msg_line_eating() + ')*', msg, opts).group(0).split(os.linesep)
    ['ab', 'b', '']
    >>> msg = msg + os.linesep + os.linesep + "==plop==" + os.linesep
    >>> re.match('(' +msg_line_eating() + ')*', msg, opts).group(0).split(os.linesep)
    ['ab', 'b', '']
    """
    # newline_pattern = "(?:$\n)?^"
    not_eq_eq = "^(?:[^=]|=?!=)"

    return '(?:' + '^$\n?' +'|'+ not_eq_eq + ".*$\n?" + ')'


def extract_full_del_props(text):
    """ Takes wikicode, returns a pair
    ([(title(str), Date)*], newtext)

    Searches deletion proposition generated with the standard ''full template'' form
    """
    pattern = u"""== L'article {} est proposé à la suppression ==$\n""" + '((?:' + msg_line_eating() +')*'+ ')'
    articles = []
    del_sum = 0

    for article in re.finditer(pattern.format(u'(.*)'), text, re.MULTILINE):
        date = extract_date(article.group(2))
        articles.append((article.group(1), date))
        del_sum += len(article.group(0))

        logging.info(u" Article : {} (annoncé le {})".format(article.group(1), date))
        logging.info(u" Annonce : \n'''{}'''".format(len(article.group(2))))

    del_pattern = pattern.format(u'.*')
    newpage = re.sub(del_pattern, '', text, flags=re.MULTILINE)


    logging.debug(u"(taille en octets) : Supprimé {} - nouvelle : {}, ancienne {}, différence {}: "
                  .format(
                      del_sum,
                      len(newpage),
                      len(text),
                      del_sum-(len(text) - len(newpage))
                  )
                 )

    return (articles, newpage)

def format_del_announce(date, article_name):
    """ returns a mediawiki template text for a deletion announce"""
    return u"{{Annonce proposition suppression|nom=" +\
            article_name + u"|" +\
            date.__str__() + u"}}"
    #TODO: gni str/unicode ?



def extract_fusion_articles(title):
    """ Extracts article titles from section title
    >>> title = '== Les articles [[Jasper]] et [[Jasper (informatique)]] sont proposés à la fusion =='
    >>> extract_fusion_articles(title)
    ['Jasper', 'Jasper (informatique)']

    """
    lbegin = re.escape("[[")
    lend = re.escape("]]")
    match = re.findall("{}(.*?){}".format(lbegin, lend), title)
    return match

SAMPLE_FUSION_ANNOUNCE = u"""== Les articles [[Jasper]] et [[Jasper (informatique)]] sont proposés à la fusion ==
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
    expected = unicode(section.filter_wikilinks(matches=u"Wikipédia:Pages à fusionner#")[0])
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

    sections = parsed.get_sections([2], matches=u"Les articles .*? sont proposés à la fusion")

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


    sep_preamble = u"------->"
    sep_end = u"<noinclude>"

    (preamble, following) = old_text.split(sep_preamble, 1)
    (section_annonces, rest) = following.split(sep_end, 1)

    # prétraitement des annonces : création d'une liste de couple (template, Date)
    announces_lines = section_annonces.split(u"\n")

    dated_old_announces = [
        (text, extract_date(text))
        for text in announces_lines 
        if text != u""
    ]

    # tri par date
    sorted_announces = sorted(dated_old_announces + dated_new_announces,
                              key=lambda (_, date): date, reverse=True)

    # création de la section finale

    new_section = u"\n".join([text for text, _ in sorted_announces])

    return preamble + sep_preamble + u"\n" + new_section + u"\n" + sep_end + rest



def gen_archives_page(old_archive_text, new_archived_announces):
    """ génère une page d'archive à partir de l'ancienne page et des nouvelles archives """

    announces_lines = old_archive_text.split(u"\n")

    dated_old_announces = [(text, extract_date(text))
                           for text in announces_lines if text != u"" and text.strip()[:2] == "{{"]

    sorted_announces = sorted(dated_old_announces + new_archived_announces,
                              key=lambda (_, date): date, reverse=False)

    by_month = {month: [value for (date, value) in sorted_announces + dated_old_announces
                          if date.mois == month] for month in Date.MOIS
                }
    #new_text = reduce(, string.concat)

    new_text = "\n".join([
        "== {} ==\n{}\n".format(date.MOIS[mois], by_month[annonce])
        for mois in by_month
    ])

    return new_text

# writing functions

def projects_maintenance(projects, options):
    """ Function launching maintenance for all projects """
    for project in projects:
        # TODO: log

        pywikibot.log("Project : " + project.name)

        deletion_prop_maintenance(project)
        fusion_prop_maintenance(project)


        print(u"> Diff des Annonces <\n")
        project.announce_page.show_diff()

        print(u"> Diff PDD <\n")
        project.discussion_page.show_diff()

        # Sauvegarde éventuelle #
        if not options.simulate:
            if project.discussion_page.modified:
                project.discussion_page.save()

            if project.announce_page.modified:
                project.announce_page.save()

def del_prop_iteration(page):
    """ iterator on deletion proposition announces in announce page
    >>> liste = list(del_prop_iteration(mwparserfromhell.parse(ANNOUNCES_SAMPLE)))
    >>> liste[0].get("nom").value
    u'PagePlus'
    >>> len(liste)
    13
    >>> liste[0].name ==  ANNOUNCE_DEL_TMPL
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
        pywikibot.output("-> {}".format(article_title))
        try:
            status = get_page_status(unicode(article_title))
            if status.is_proposed_to_deletion():
                pywikibot.output("* still opened")
            else:
                if "fait" not in announce:
                    announce.add(2, u"fait")
        except pywikibot.exceptions.InvalidTitle:
            logging.warn("Annonce malformée !! {}".format(article_title))

    return unicode(parsed)



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
    logging.info(u"Before : {} ; After {} ; expected around {}"
                 .format(len(discussion_text),
                         len(new_discussion_text),
                        len(discussion_text) - len(articles) * 1200)
                )

    logging.info(u"Articles extraits")
    for elem in articles:
        (nom, date) = elem
        logging.info(u"Date d'annonce : {} ; Article à supprimer : {}".format(date, nom))

    # insertions des annonces extraites dans la page d'annonce

    dated_new_announces = [
        (format_del_announce(date, name), date)
        for name, date in articles
    ]
    new_announces_text = insert_new_announces(announces_text, dated_new_announces)

    announce_comment = u"proposition(s) de suppression déplacée(s) depuis [[{}|La page de discussion]]"\
            .format(discussion_pagename)
    project.discussion_page.set_content(new_announces_text, announce_comment)
    project.announce_page.set_content(new_announces_text, announce_comment)



    # mise à jour de l'état des annonces #

    new_announces_text = deletion_prop_status_update(new_announces_text)


    comment = u"Déplacements vers [[{}|la page d'annonces]]".format(announces_pagename)
    announce_comment = u"Mise à jour de l'état de propositions de suppression"

    project.discussion_page.set_content(new_discussion_text, comment)
    project.announce_page.set_content(new_announces_text, announce_comment)


def format_fusion_props(articles, section, date):
    """ format a fusion proposition """
    debut = u"{{Annonce fusion d'article|" +\
            unicode(date) +\
            u'|[[{}|Proposition de fusion]] entre '.format(section)
    
    suite = ""
    
    if len(articles) > 2:
        suite = u", ".join(u'[[{}]]'.format(articles[3:]))
    fin = "}}"
    
    msg = debut + suite + u'[[' + articles[1] + u']]' + u" et [["+ articles[0] + ']]' + fin
    
    return msg

def fusion_prop_maintenance(project):
    """ Testing """
    logging.info("gestion des propositions de fusion ...")
    (fusion_prop_list, new_d_text) = extract_fusion_props(project.discussion_page.get_content())

    if len(fusion_prop_list) > 0:
        dated_new_announces = [(format_fusion_props(*elem), elem[2]) for elem in fusion_prop_list]
        new_a_text = insert_new_announces(project.announce_page.get_content(), dated_new_announces)
        project.announce_page.set_content(new_a_text,
                          u"Déplacement d'annonces de proposition de fusion depuis la [[{}|La PDD]]"
                              .format(project.discussion_pagename)
        )

        project.discussion_page.set_content(new_d_text,
                          u"Déplacement des annonces de proposition fusion vers [[{}|La page d'annonce]] "
                              .format(project.announce_pagename)
        )


# CLI management, UI

from argparse import ArgumentParser

def create_options():
    """ Script option parsing """
    options = ArgumentParser("Project talk page cleaner")


    options.add_argument('-C', '--config-file', metavar='FILE',
            help="configuration file", dest="conffile")
    options.add_argument('-s', '--simulate', action='store_true',
            help="don't save changes", dest="simulate")
    options.add_argument('-t', '--test', action='store_true',
            help="run tests", dest="test")
    options.add_argument('-p', '--page',
            help="run tests", metavar="PAGE", dest="page",
            default="Projet:Informatique")
    options.add_argument('-v', '--verbose', action='store_true',
            help="show debugging messages", dest="debug")
    return options



#############################################################
# testing

import unittest
import sys

class Test(unittest.TestCase):
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
    test_doctest()
    unittest.main(argv=[sys.argv[0]])

def main():
    """ Main function"""
    opt_parse = create_options()
    opts = opt_parse.parse_args()
    
    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)
    if opts.test:
        test()
    else:
        # paramètres par defaut : "Projet:Informatique", False
        if opts.conffile:
            
            projects = [project
                        for project in read_conffile(opts.conffile)
                        if "announces" in project.tasks
                       ]
            projects_maintenance(projects, opts)
        else:
            print("configuration file not found, it is mandatory for regular execution")
            opts.print_help()
            return 0

from datas import test_data

SAMPLE_TEXT = test_data.SAMPLE_TEXT

####
####
#### Tests samples


if __name__ == "__main__":
    main()
