#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Description : updates stats and announces and global project watchlist using Portals

"""
code importé de https://fr.wikipedia.org/w/index.php?title=Utilisateur:HyuBoT/Script&oldid=76074223
écrit par le Wikipédien AmbiGraphe

"""

"""
Scripts for HyuBoT

Features :
    * monitors the articles recently created or added in a Category
    * reports its finding on a Wikipage
    * maintains a list of articles to be watched by the member of the project
      using the "linked pages changes" Mediawiki features
    * page_update article stats for portals
"""


from pywikibot.compat import catlib
import re
import pywikibot as pwb
import string

from projects import Config
import bots_commons


from hyubot.lists import compare_sorted_lists, inter_sorted_lists
from hyubot.io import PageFactory, Outputter
from hyubot.io import SimulateIOModule, IOModule
from hyubot.io import agreement
from hyubot.parser import Delimiter as Delimiter
from hyubot.parser import BOT_TAG, NOINCLUDE_TAG, get_reconstruct_errmsg_pattern
from hyubot.utils import UTF2ASCII, uppercase_first

from projects import read_conffile
import pywikibot as wikipedia


# TODO: check the API to know if it is still needed (quick and dirty fix)
def unique(l):
    """Given a list of hashable object, return an alphabetized unique list."""
    l = list(dict.fromkeys(l).keys())
    l.sort()
    return l


"""
Toolkit
"""

# store for the warnings to report on some user page
warnings_list = []


"""
Classes and functions for pywikipedia.
"""


def format_without_talkpages(title):
    """ generates a string of wikitext, a wikilink."""
    return '* [[{}]]'.format(title)


def format_with_talkpages(title):
    """ generate a string of wikitext, two wikilinks to a page and its takpage, respectively"""
    return '* [[{}]] ([[Discussion:{}|d]])'.format(title, title)


class BotEditedPage(object):

    """
    Subclass of Page aimed to be edited by a bot.
    """

    def __init__(self, site, title, logger, bot_tag=None,
                 create=False
                 # sectionLevel=None, edit=True
                 ):
        self.wikipage = wikipedia.Page(site, title)

        if bot_tag:
            self.bot_tag = bot_tag
        else:
            self.bot_tag = Delimiter()
        self.splitting = []
        self.edit_summary = 'Robot : mise à jour'
        self.recovered = False
        self.create = create
        self.logger = logger
        self._title = title

        self.edit = True

    @property
    def title(self):
        """ accessor for the title property"""
        return self._title

    def recover(self):
        """
        Recovers page's content, split along start and end tags.
        """
        if not self.recovered:
            try:
                self.splitting = self.bot_tag.split(self.wikipage.get())
            except wikipedia.NoPage:
                self.logger.output("\nLa page {} n'existe pas.".format(self.title))

                if self.create:
                    self.splitting = ['', '']
                else:
                    raise wikipedia.NoPage
            finally:
                self.recovered = True

    def section_string(self, section_number=0):
        """ returns the section content given a number
        (the table contains also section names at odd indexes)"""

        return self.splitting[2 * section_number + 1]

    def section_update(self, new_section, section_number=0,
                       change_warning=None, no_change_warning=False,
                       comment=None):
        """
        uploads the content of a section,
        """

        if not self.recovered:
            self.recover()

        index = 2 * section_number + 1
        try:
            old_section = self.splitting[index]
        except IndexError:
            errmsg_pattern = get_reconstruct_errmsg_pattern()
            self.logger.output(errmsg_pattern.format(self.bot_tag.start, str(section_number), self.title))

            if self.create:
                self.logger.output("Création de la section à la suite du texte.")
                old_section = ''
            else:
                self.logger.output("Abandon des modifications.")
                return
        if old_section == new_section:
            if no_change_warning:
                self.logger.output("Pas de changement sur la page {}.".format(self.title))
            return
        if not comment:
            comment = self.edit_summary
        head = self.bot_tag.rebuild(self.splitting[:index])
        try:
            tail = self.bot_tag.rebuild(self.splitting[index + 1:])
        except IndexError:
            tail = ''
        try:
            self.wikipage.put(self.bot_tag.rebuild([head, new_section, tail]),
                              comment=comment)

        except Exception as exc:
            self.logger.output("Erreur pendant l'édition de la page [[{}]]: {}.".format(self.title, exc))
        else:
            if change_warning:
                self.logger.output(change_warning)

    def edit_section_content(self, section_number=0):
        """ modifies the content of a section (no upload)"""
        if not self.recovered:
            self.recover()
        index = 2 * section_number + 1
        try:
            body = self.splitting[index]
        except IndexError as exc:

            err_msg_pattern = "Balise de début {} manquante; ou numéro de section {} trop élevé dans la page {}."
            self.logger.output(err_msg_pattern.format(self.bot_tag.start, str(section_number), self.title))

            raise exc

        return body

    def page_update(self, new_string, section_number=0, edit=True, comment=None,
                    warning=False):
        """
        uploads the content of the whole page
        """

        if self.wikipage.exists():
            try:
                body = self.edit_section_content(section_number)
            except IndexError:
                self.edit = agreement('Add bot edit section?', True)
                body = ''
        else:
            self.edit = agreement('Page {} does not exist. Create?'
                                  .format(self.title), default=self.edit)
        if new_string == body:
            self.edit = False
        elif self.edit and edit:
            if not comment:
                comment = self.edit_summary
            if warning:
                self.logger.output("(mise à jour) ")

            index = 2 * section_number + 1
            head = self.bot_tag.rebuild(self.splitting[:index])
            try:
                tail = self.bot_tag.rebuild(self.splitting[index + 1:])
            except IndexError:
                tail = ''
            try:
                self.wikipage.put(self.bot_tag.rebuild([head, new_string, tail]),
                                  comment=comment)
            except Exception as exc:
                self.logger.output("Erreur pendant l'édition de la page [[{}]]: {}".format(self.title, exc))
        else:
            self.logger.output("Pas de modification de la page [[{}]].".format(self.title))


class Bot(object):

    """ declaration for the injector """

    def run(self):
        """ the main bot task"""
        pass

    def gather_nominations(self):
        """ dummy methods, returns lists of nominations to adq, fusion, ..."""
        pass


class ListUpdateRobot(object):

    """
    Robot maintaining a list of articles in a Wikipage.

    Used to generate all the pages in a WikiProject, for example for a ProjectPage WatchList generation.
    """

    def __init__(self, list_page, list_of_titles=None, list_name=None,
                 article_number_page=None, edit=True, link=True,
                 talkpages=False,
                 sections=True, sort_table=UTF2ASCII):

        self.list_page = list_page
        self.article_number_page = article_number_page
        self.edit = edit
        self.link = link
        self.talkpages = talkpages
        self.sections = sections
        self.sort_table = sort_table
        self.new = []
        self.deleted = []
        self._list_of_titles = list_of_titles

        if self._list_of_titles is None:
            self._list_of_titles = []
        if list_name:
            self.list_name = list_name
        else:
            self.list_name = list_page.title()

    @property
    def list_of_titles(self):
        """ Accessor for the Portal subjects string"""
        return self._list_of_titles

    @list_of_titles.setter
    def list_of_titles(self, liste):
        """ Setter for the Portal subjects string"""
        self._list_of_titles = liste

    def gather_nominations(self):
        """
        computes the nominations to deletions, badges, on Wikipedia for the project
        """
        if not self.edit:
            return
        # try:
        self.list_page.recover()  # create = create)

        old_list = self.extract_titles(self.list_page.section_string())

        if old_list:
            (self.new, self.deleted) = compare_sorted_lists(self.list_of_titles, old_list)

            if self.deleted:
                change_warning = (" {{Moins2}}"
                                  + ' • '.join(format_titles(self.deleted)))
            else:
                change_warning = ''

            if self.new:
                change_warning += (" {{Plus4}}"
                                   + ' • '.join(format_titles(self.new)))

        else:
            change_warning = " création."
        if change_warning:
            self.list_page.section_update(
                '\nMise à jour le ~~~~~ pour un total de {} articles'.format(len(self.list_of_titles))
                + '\n' + self.list_string(self.list_of_titles) + '\n',
                change_warning=("{} :{}".format(self.list_name, change_warning))
            )

            if self.article_number_page:
                self.article_number_page.section_update(str(len(self.list_of_titles)))
            self.list = old_list

    def extract_titles(self, list_string):
        """ Extracts a list of article title from a wikilist of article links """
        titles_list = []
        for line in list_string.split('\n'):
            res = re.match('\* [[(.*)]]', line)
            if res:
                article = res.group(1)
                titles_list.append(article)

        return unique(titles_list)

    def list_string(self, titles_list=None):
        """
        Formats the list's output.
        """

        if titles_list is None:
            titles_list = []

        if self.talkpages and self.link:
            formatting = format_with_talkpages
        else:
            formatting = format_without_talkpages

        list_dict = {}

        if self.link:
            title_tag = Delimiter('', '')
        else:
            list_dict[''] = '<no' + 'wiki>\n'
            title_tag = Delimiter('\n</no' + 'wiki>', '\n<no' + 'wiki>')
            list_dict['~~~'] = '\n</no' + 'wiki>'

        if self.sections:
            list_dict['0'] = title_tag.englobe('\n== 0–9 ==')
            list_dict['~'] = title_tag.englobe('\n== Autres ==')

            for character in string.ascii_uppercase:
                list_dict[character] = title_tag.englobe('\n== {} =='.format(character))

        for title in titles_list:
            key = self.sort_table.translate(title).lstrip().upper()
            if not key:
                key = '~~'
            while key in list(list_dict.keys()):
                key += '\t'
            list_dict[key] = formatting(title)

        keys_list = list(list_dict.keys())
        keys_list.sort()

        return "\n".join([list_dict[key] for key in keys_list])

FUSION_TITLE_PATTERN = re.compile(r'\n=+\s*(.*?)\s*=+\s*?\n')
TITLE_PATTERN = re.compile(r'\[\[\s*([^#\|\]]*[^#\|\]\s])[^\]]*?\]\]')
LINK_PATTERN = re.compile(r'\[\[(?:[^\|\]]*\|)?([^\]]*)\]\]')


def format_titles(title_list):
    """ formats a list of titles into a list of wikilinks """
    return ['[[{}]]'.format(title)
            for title in unique(title_list)
            ]


def format_article_list(title_list):
    """ formats a list of titles into a list of {{m|a}} corresponding template """
    return ['* {{a|1={}}}'.format(title)
            for title in title_list
            ]


class NominationsChecklist(object):

    """
    Computes intersection of a sorted list of articles and categories

    Purpose : store nominated articles for deletion, labels and merge.

    the "gather_nominations" method initialize the component with project wide announces
    """

    def __init__(self):
        self.nomination_type_label = {'PAS': 'Page proposée à la suppression',
                                      'PAF': 'Article à fusionner',
                                      'PBA': 'Article potentiellement bon',
                                      'PAdQ': 'Article potentiellement de qualité'}

        self.list_of_fusion_titles = []

    def gather_nominations(self):
        """ initialization :
        * inspects the corresponding categories
        * extracts fusion nominations in the relevant frwiki page
        """

        for key, name in list(self.nomination_type_label.items()):
            cat = catlib.Category(wikipedia.getSite(), 'Category:{}'.format(name))
            self.nomination_type_label[key] = {article.title() for article in cat.articles()}

        frwiki_fusion_nomination_page = wikipedia.Page(wikipedia.getSite(),
                                                       'Wikipédia:Pages à fusionner')

        self.list_of_fusion_titles = FUSION_TITLE_PATTERN.findall(frwiki_fusion_nomination_page.get())

        # print(self.list_of_fusion_titles)


class Portal(wikipedia.Page):

    """
    Subclass of Page that has some special tricks that only work for
    portal: pages
    """

    def __init__(self, site, name, logger,  # sort_table = None,
                 iconMedia='Bullet (typography).svg',
                 edit=True, option=None):
        logger.output(name)
        wikipedia.Page.__init__(self, site, 'Portal:' + name,
                                ns=4)
        # if self.namespace() != 4:
        #   raise ValueError(u'BUG: %s is not in the project namespace!' % name)
        if option is None:
            option = []

        self.logger = logger
        self.name = uppercase_first(name)
        # linkedCatName = u'Portail:%s/Articles liés' % name

        watchlist_page = BotEditedPage(wikipedia.getSite(),
                                       'Portail:{}/Liste de suivi'.format(name),
                                       bot_tag=BOT_TAG, create=True, logger=logger)

        article_number_page = BotEditedPage(wikipedia.getSite(),
                                            'Portail:{}/Total'.format(name),
                                            create=True, logger=logger)

        self.list_updater_bot = ListUpdateRobot(watchlist_page,
                                                list_name='* Portail:{}'.format(name),
                                                article_number_page=article_number_page,
                                                edit=edit and ('noedit' not in option),
                                                talkpages=True,
                                                link=('nolink' not in option))

        self.icon_media = iconMedia
        self.option = option
        self._site = site

    def iconify(self, icon_media=None):
        """
        Downloading an illustration icon for the project, if possible
        """

        if icon_media:
            self.icon_media = icon_media
        else:
            try:
                icon_page = wikipedia.Page(wikipedia.getSite(),
                                           'Portail:{}/Icône'.format(self.name))
                self.icon_media = NOINCLUDE_TAG.expurge(icon_page.get())

#             pylint: disable=broad-except
            except Exception as exc:
                print(("failed to get icon for project {} some reason {}, ignoring"
                       .format(self.name, exc)))

    def listify(self):
        """
        gets a list of all pages including a {{Modèle:Portal [portal name]}}
        and updates the list of articles of this portal
        """

        templist = []

        try:
            template = wikipedia.Page(self.site,
                                      'Modèle:Portail {}'.format(self.name))
            # wikipedia.output(u'OK.')
        except wikipedia.NoPage:
            self.logger.output = "Bandeau introuvable avec le nom du portail."

            raise wikipedia.NoPage

        if template.isRedirectPage():

            template = template.getRedirectTarget()

        for page in template.getReferences():
            if page.namespace() == 0:
                templist.append(page.title())

        self.list_updater_bot.list_of_titles = unique(templist)


class ProjectPage(wikipedia.Page):

    """
    Specialization of class Page for "ProjectPage:" pages
    """

    def __init__(self, parameters, logger):
        wikipedia.Page.__init__(self, parameters.site, 'Project:' + parameters.name,
                                insite=parameters.insite)  # , defaultNamespace = 4)

        self._parameters = parameters
        self.logger = logger

        if self.namespace() != 4:
            print(self.namespace())
            raise ValueError('BUG: {} is not in the project namespace'.format(self.name))

        logger.output(parameters.portals)

        self.portals_list = [Portal(wikipedia.getSite(), name, logger)
                             for (name, params) in parameters.portals]

        self.titles_list = []

    @property
    def name(self):
        """ Accessor for the Portal subjects string"""
        return uppercase_first(self._parameters.name)

    def maintenance(self, checklist=None):
        """Performing maintenance for the portal
        * update the page listing the articles
        * gathering nominations
        """

        self.logger.output("\n'''[[Projet:{}]]'''".format(self.name))

        for portal in self.portals_list:
            portal.iconify()
            portal.listify()
            self.titles_list += portal.list_updater_bot.list_of_titles
            portal.list_updater_bot.gather_nominations()
        self.titles_list = unique(self.titles_list)
        self.total_update()
        self.new_articles_update()
        if checklist:
            self.nominations_list_update(checklist)

    def total_update(self):
        """ Put on Wikipedia the full list of articles of the project"""

        total_page = BotEditedPage(wikipedia.getSite(),
                                   'Projet:{}/Total articles'.format(self.name),
                                   create=True, logger=self.logger)

        total_page.section_update(str(len(self.titles_list)))

    # list title formatting utility functions

    def new_articles_update(self):
        """ update the page on which will be seen the new and deleted articles list
        formated in wikitext with templates"""
        backup_list = []
        for portal in self.portals_list:
            backup_list += portal.list_updater_bot.list

        additions_stringlist = []
        deleted_list = []

        for portal in self.portals_list:
            new_list = []
            for title in portal.list_updater_bot.new:
                if title not in backup_list:
                    new_list.append(title)
                    backup_list.append(title)
            if new_list:
                additions_stringlist.append(':[[Fichier:{}|12x24px|{}|link=Portail:{}]] '
                                            .format(portal.icon_media, portal.name, portal.name)
                                            + ' • '.join(format_titles(new_list)))

                # backup_list += new_list
            for title in portal.list_updater_bot.deleted:
                if title not in self.titles_list:
                    deleted_list.append(title)
        if deleted_list:
            deleted_article_string = ' • '.join(format_titles(deleted_list))

            list_string = '\n{{Moins2}} {}'.format(deleted_article_string)
        else:
            list_string = ''

        if additions_stringlist:
            list_string += ('\n;{{subst:CURRENTDAY}}'
                            + ' {{subst:CURRENTMONTHNAME}}'
                            + ' {{subst:CURRENTYEAR}}\n'
                            + '\n'.join(additions_stringlist))
        if list_string:
            new_articles_page = BotEditedPage(wikipedia.getSite(),
                                              'Projet:{}/Articles récents'.format(self.name),
                                              bot_tag=BOT_TAG, create=True, logger=self.logger)

            old_list = new_articles_page.edit_section_content().split('\n;')
            list_string += '\n;' + '\n;'.join(old_list[1:10])

            new_articles_page.section_update(
                list_string,
                change_warning=(
                    "Mise à jour des "
                    + "[[Projet:{}/Articles récents|articles récents]].".format(self.name)))

    def nominations_list_update(self, checklist):
        """ updates the formated page in wikitext of fusion nominations, adq, and so on
        """
        project_checklist_dict = {}
        for key, nominates_list in list(checklist.nomination_type_label.items()):
            project_checklist_dict[key] = inter_sorted_lists(
                self.titles_list, nominates_list)
        project_fusion_list = []
        missing_titles_list = []
        for fusion_title in checklist.list_of_fusion_titles:
            fusion_list = TITLE_PATTERN.findall(fusion_title)
            for title in fusion_list:
                if uppercase_first(title) in self.titles_list:
                    # title = lbranch_tag.expurge(empty_if_tag.expurge(
                    #   arg_tag.expurge(fusion_title))).replace('|}}','').strip()
                    project_fusion_list.append(
                        '* %s ' % fusion_title
                        + '<small>([[Wikipédia:Pages à fusionner#'
                        + '%s' % re.sub(LINK_PATTERN, r'\1', fusion_title)
                        + '|discussion]])</small>')
                    for titlebis in fusion_list:
                        titlebis = uppercase_first(titlebis)  # .strip()
                        try:
                            project_checklist_dict['PAF'].remove(titlebis)
                        except ValueError:
                            if '{' not in titlebis:
                                missing_titles_list.append(titlebis)
                    break
        fusion_warning = ''
        if missing_titles_list:

            msg = "\nBandeau de fusion à vérifier pour : [[{article_list}]].\n"
            fusion_titles_str = "]] • [[".join(missing_titles_list)

            fusion_warning = msg.format(article_list=fusion_titles_str)

        if project_checklist_dict['PAF']:
                # fusion list report generation : handling fusions props without comments

            paf_list = format_titles(project_checklist_dict['PAF'])
            fusion_warning += ("\nProposition de fusion sans discussion initiée pour : {}\n"
                               .format(' • '.join(paf_list)))
        text = ''.join(["[[Image:Icono consulta borrar.png|20px]] ",
                        "'''Pages à supprimer'''",
                        ' [[Wikipédia:Pages à supprimer#Avertissements',
                        '|(dernières demandes)]]\n',
                        '\n'.join(format_article_list(project_checklist_dict['PAS'])),
                        "\n[[Image:Merge-arrows.svg|20px]] ",
                        "'''Pages à fusionner''' ",
                        '[[Wikipédia:Pages à fusionner#',
                        'Requêtes à traiter au mois de {{CURRENTMONTHNAME}} ',
                        '{{CURRENTYEAR}}|(liste du mois)]]\n',
                        '\n'.join(project_fusion_list), fusion_warning,
                        '\n[[Image:Fairytale questionmark.png|20px]] ',
                        "'''Propositions aux labels'''",
                        ' [[WP:AdQ|AdQ]] ou [[WP:BArt|BA]]\n',
                        '\n'.join(['* {{a|1= %s}}' % t
                                   for t in (project_checklist_dict['PAdQ']
                                             + project_checklist_dict['PBA'])])])

        nominations_page = BotEditedPage(wikipedia.getSite(),
                                         'Projet:{}/Consultations'.format(self.name),
                                         bot_tag=BOT_TAG, create=True, logger=self.logger)

        # output(u"• [[Projet:%s/Consultations|Consultations]] " % self.name)

        consultation_pattern = "[[Projet:{projet}/Consultations|consultations]]"
        edit_message = ("Mise à jour des " + consultation_pattern.format(projet=self.name))

        nominations_page.section_update('\n' + text + '\n',
                                        change_warning=edit_message
                                        )


WARNINGS_PAGE = wikipedia.Page(wikipedia.getSite(),
                               'Utilisateur:HyuBoT/Contrôle')


class HuyBotApp(object):

    """ Full robot app for snakejuice"""

    def __init__(self, iomod):
        self.iomod = iomod

    def run(self):
        """ Run the full task list """
        nominations_checklist = NominationsChecklist()
        nominations_checklist.gather_nominations()

# Bot plumbing part


class Reporter(object):

    '''class definition for Reporter'''

    def __init__(self, page_factory, output, config):
        self._warnings_list = []
        self.page_factory = page_factory
        self.output_pagename = config
        self.outputter = output

    def output(self, text):
        """ method that both output to screen logger and saves the message"""
        self.add_warning(text)
        self.outputter.output(text)

    def add_warning(self, warning):
        """appends a warning report to the message report in prevision of Final report"""
        self._warnings_list.append(warning)

    @property
    def warning_list(self):
        """ getter for warning list messages"""
        return self._warnings_list

    def final_report(self):
        #       TODO: code @IgnorePep8
        pass


def main():
    """ main function : defines global logger and so on"""

    arguments = bots_commons.create_options()

    options = arguments.parse_args()

    if options.conffile:
        conffile = options.conffile
    else:
        conffile = bots_commons.get_default_configfile()

    proj_param_list = [project_param
                       for project_param in read_conffile(conffile)
                       if "HyuBot" in project_param.tasks
                       ]

    if options.simulate:
        pass
    else:
        pass

    app = Bot()

#     pylint: disable=maybe-no-member
    checklist = app.gather_nominations()

    for proj_param in proj_param_list:
        ppage = ProjectPage(proj_param, logger=wikipedia)
        ppage.maintenance(checklist=checklist)

    # reports the runs warnings on logging page

    wpage_header = "Opérations du ~~~~~.\n"

    if UTF2ASCII.unknown_char_list:

        # page_update non transcripted titles characters

        characters_warn_section = "; Caractères non transcrits : {untranscriptedStr}.\n"
        warn_list = ["'{char}' dans « [[{title}]] »".format(char=c, title=text)
                     for (c, text)
                     in UTF2ASCII.unknown_char_list
                     ]
        wpage_header += (characters_warn_section.format(untranscriptedStr=' – '.join(warn_list)))

    try:
        wpage_pattern = "{header}\n{warn_list}"

        wl_content = '\n'.join(warnings_list)
        header = wpage_header
        WARNINGS_PAGE.put(wpage_pattern.format(header=header,
                                               warn_list=wl_content),
                          comment='Contrôle des opérations effectuées.')

# pylint: disable=broad-except
    except Exception as exc:
        wikipedia.output("Erreur lors de l'édition du contrôle.\n {msg}".format(msg=exc))
    finally:
        wikipedia.stopme()

if __name__ == "__main__":
    main()
