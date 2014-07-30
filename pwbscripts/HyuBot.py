#!/usr/bin/pythongather
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
    * update article stats for portals
"""

import re

import pywikibot as wikipedia
from pywikibot.compat import catlib

from pwbscripts.projects import read_conffile
from pwbscripts import bots_commons

from pwbscripts.HyuBotParser import Delimiter as Delimiter
from pwbscripts.HyuBotParser import bot_tag, noinclude_tag

import pwbscripts.HyuBotParser as HyuBotParser

from pwbscripts.HyuBotIO import IOModule


from snakeguice import inject

# TODO: check the API to know if it is still needed (quick and dirty fix)

def unique(l):
    """Given a list of hashable object, return an alphabetized unique list."""
    l = dict.fromkeys(l).keys()
    l.sort()
    return l


"""
Toolkit
"""

# store for the warnings to report on some user page
warnings_list = []


def agreement(question, default):
    print("{} (y/n), default : {}".format(question, default))
    invalid_input = True
    while invalid_input:
        rep = input()
        if rep in ['y', 'n', '']:
            invalid_input = False

    if rep == 'y':
        retval = True
    if rep == 'n':
        retval = False
    if rep == '':
        retval = default

    return retval

import string

class TranslationTable:
    def __init__(self, dicOfRelatives={},
                 defaultValue=None):
        self.unknownCharList = []
        self.dict = {}
        for c in string.printable:
            self.dict[c] = c
        for s in dicOfRelatives.keys():
            for c in dicOfRelatives[s]:
                self.dict[c] = s

        if defaultValue is not None:
            self.dict[None] = defaultValue

    def translate(self, text):
        try:
            return "".join([self.dict[c] for c in text])
        except KeyError:
            for c in text:
                if c not in self.dict:
                    self.unknownCharList.append((c, text))
            return "".join([self.dict.get(c, self.dict.get(None, c))
                            for c in text])

utf2ascii = TranslationTable(
    dicOfRelatives={
        'a': u'áàâäåāảãăạąặắǎấầ',  # 'а' dans l'alphabet cyrillique
        'e': u'éêèëěėễệęềếē', 'i': u'íîïīıìịǐĩ',
        'o': u'óôöōőøõòơồόŏờốṓởǫỗớ',  # les deux accents aigus sont différents
        'A': u'ÀÂÄÅÁĀ', 'E': u'ÉÊÈËĖ', 'I': u'ÎÏİÍ', 'O': u'ÔØÖŌÓÕ',
        'u': u'ùûüūúưứŭũửůűụ', 'y': u'ÿýỳ', 'U': u'ÙÛÜÚŪ',
        'ae': u'æ', 'AE': u'Æ', 'oe': u'œ', 'OE': u'Œ',
        'c': u'çćč', 'C': u'ÇČĈĆ', 'd': u'đð', 'D': u'ĐD̠',
        'g': u'ğġǧ', 'G': u'Ğ', 'h': u'ĥħ', 'H': u'ḤĦ', 'l': u'ḷłľℓļ', 'L': u'ŁĽ',
        'm': u'ṃ', 'n': u'ńñňṇņ', 'r': u'řṛṟ', 's': u'śšşs̩ṣș', 'S': u'ŠŞŚŜȘ',
        't': u'ţťt̠țṭ', 'T': u'T̩ŢȚ', 'z': u'žżź', 'Z': u'ŻŽ',
        'ss': u'ß', 'th': u'þ', 'Th': u'Þ', 'TM': u'™',
        'alpha': u'α', 'beta': u'β', 'gamma': u'γ', 'Gamma': u'Γ',
        'delta': u'δ', 'Delta': u'Δ', 'epsilon': u'ε', 'zeta': u'ζ',
        'eta': u'η', 'theta': u'θ', 'iota': u'ι', 'kappa': u'κ',
        'lambda': u'λ', 'Lambda': u'Λ', 'mu': u'μ', 'nu': u'ν',
        'xi': u'ξ', 'omicron': u'ο', 'pi': u'π', 'rho': u'ρ',
        'sigma': u'σ', 'Sigma': u'Σ', 'tau': u'τ', 'upsilon': u'υ',
        'phi': u'φϕ', 'Phi': u'Φ', 'chi': u'χ', 'psi': u'ψ', 'Psi': u'Ψ',
        'omega': u'ω', 'Omega': u'Ω',
        '1 2': u'½', '2': u'²', '3': u'³', 'micro': u'µ',  # symbole différent de la lettre mu
        ' ': u'’–−∞×÷≡«»°…—®⊥‐√ʼ§' + string.whitespace + string.punctuation,
        # à traiter : '‘´'
        # supprimé : 人
        '': u'·ʿ‘'  # diacritiques ou lettres négligées et caractère pour la coupure d'un mot
    },
    defaultValue=' '
)


def uppercase_first(text):
    """ returns a similar string with the first characters uppercased"""
    if text:
        return text[0].upper() + text[1:]
    else:
        return ''

#
# functions on the List (of Pages) article
#


def compareSortedLists(newList, oldList):
    """ calculates the differences between a list and a newer one

    returns a couple of lists (insertions, deletions)
    """
    gain = []
    loss = []
    index = 0
    for el in oldList:
        try:
            while newList[index] < el:
                gain.append(newList[index])
                index += 1
            if el == newList[index]:
                index += 1
            else:
                loss.append(el)
        except IndexError:
            loss.append(el)
    return (gain + newList[index:], loss)


def interSortedLists(list1, list2):
    """ computes the commons elements of two sorted list """
    index = 0
    intersection = []
    for el in list2:
        try:
            while list1[index] < el:
                index += 1
            if list1[index] == el:
                intersection.append(el)
                index += 1
            # else:
            #    print [el, list1[index]]
        except IndexError:
            break
    return intersection


def oddIndexList(longList):
    return [longList[i] for i in range(1, len(longList), 2)]


"""
Classes and functions for pywikipedia.
"""


class BotEditedPage(object):
    """
    Subclass of Page aimed to be edited by a bot.
    """
    def __init__(self, site, title, logger, insite=None, botTag=None,
                 create=False
                 # sectionLevel=None, edit=True
                 ):
        self.wikipage = wikipedia.Page(site, title, insite=insite)

        if botTag:
            self.botTag = botTag
        else:
            self.botTag = Delimiter()
        self.splitting = []
        self.editSummary = u'Robot : mise à jour'
        self.recovered = False
        self.create = create
        self.logger = logger
        self._title = title

        # self.edit = edit
    @property
    def title(self):
        return self._title

    def recover(self):
        """
        Recovers page's content, split along start and end tags.
        """
        if not self.recovered:
            try:
                self.splitting = self.botTag.split(self.wikipage.get())
            except wikipedia.NoPage:
                self.logger.output(u"\nLa page {} n'existe pas.".format(self.title()))

                if self.create:
                    self.splitting = ['', '']
                else:
                    raise wikipedia.NoPage
            finally:
                self.recovered = True

    def sectionString(self, sectionNumber=0):
        return self.splitting[2 * sectionNumber + 1]

    def sectionUpdate(self, newSection, sectionNumber=0,
                      changeWarning=None, noChangeWarning=False,
                      comment=None):
        if not self.recovered:
            self.recover()

        index = 2 * sectionNumber + 1
        try:
            oldSection = self.splitting[index]
        except IndexError:
            errmsgP = HyuBotParser.get_reconstruct_errmsgP()
            self.logger.output(errmsgP.format(self.botTag.start, str(sectionNumber), self.title()))

            if self.create:
                self.logger.output(u"Création de la section à la suite du texte.")
                oldSection = ''
            else:
                self.logger.output(u"Abandon des modifications.")
                return
        if oldSection == newSection:
            if noChangeWarning:
                self.logger.output(u"Pas de changement sur la page {}.".format(self.title()))
            return
        if not comment:
            comment = self.editSummary
        head = self.botTag.rebuild(self.splitting[:index])
        try:
            tail = self.botTag.rebuild(self.splitting[index + 1:])
        except IndexError:
            tail = ''
        try:
            self.wikipage.put(self.botTag.rebuild([head, newSection, tail]),
                              comment=comment)
        except:
            self.logger.output(u"Erreur pendant l'édition de la page [[{}]].".format(self.title()))
        else:
            if changeWarning:
                self.logger.output(changeWarning)

    def editContent(self, sectionNumber=0):
        if not self.recovered:
            self.recover()
        index = 2 * sectionNumber + 1
        try:
            body = self.splitting[index]
        except IndexError:

            err_msgP = u"Balise de début {} manquante; ou numéro de section {} trop élevé dans la page {}."
            self.logger.output(err_msgP.format(self.botTag.start, str(sectionNumber), self.title()))

            raise IndexError
        # else:
        #    if self.botTag.end and (len(self.splitting) == index+1):
        #        wikipedia.output('End tag missing in %s.'
        #                         % self.title())

        return body

    def update(self, newString, sectionNumber=0, edit=True, comment=None,
               warning=False):
        if self.exists():
            try:
                body = self.editContent(sectionNumber)
            except IndexError:
                self.edit = agreement(u'Add bot edit section?', True)
                body = ''
        else:
            self.edit = agreement(u'Page {} does not exist. Create?'
                                  .format(self.title()), default=self.edit)
        if newString == body:
            self.edit = False
        elif self.edit and edit:
            if not comment:
                comment = self.editSummary
            if warning:
                self.logger.output(u"(mise à jour) ")

            index = 2 * sectionNumber + 1
            head = self.botTag.rebuild(self.splitting[:index])
            try:
                tail = self.botTag.rebuild(self.splitting[index + 1:])
            except IndexError:
                tail = ''
            try:
                self.put(self.botTag.rebuild([head, newString, tail]),
                         comment=comment)
            except:
                self.logger.output(u"Erreur pendant l'édition de la page [[{}]].".format(self.title()))
        else:
            self.logger.output(u"Pas de modification de la page [[{}]].".format(self.title()))


class ListUpdateRobot(object):
    """
    Robot maintaining a list of articles in a Wikipage.

    Used to generate all the pages in a WikiProject, for example for a ProjectPage WatchList generation.
    """
    def __init__(self, listPage, listOfTitles=[], listName=None,
                 totalPage=None, edit=True, link=True,
                 itemFormat=None, talkpages=False,
                 sections=True, sortTable=utf2ascii):
        self.listPage = listPage
        self.list = listOfTitles
        self.totalPage = totalPage
        self.edit = edit
        self.link = link
        self.talkpages = talkpages
        self.sections = sections
        self.sortTable = sortTable
        self.new = []
        self.deleted = []
        if listName:
            self.listName = listName
        else:
            self.listName = listPage.title()

    def load(self, listOfTitles):
        self.list = listOfTitles

    def gatherNominations(self):  # , #newlist = [], edit = True, create = True):
        if not self.edit:
            return
        # try:
        self.listPage.recover()  # create = create)
        # except wikipedia.NoPage:
        #    return
        oldList = self.extractedList(self.listPage.sectionString())
        # wikipedia.output(u'Liste extraite')
        # except wikipedia.Error:
        #    oldList = []
        # except IndexError:
        #    oldList = []
        if oldList:
            (self.new, self.deleted) = compareSortedLists(self.list, oldList)
        # wikipedia.output(u'Comparaison effectuée')
            if self.deleted:
                changeWarning = (u" {{Moins2}}"
                                 + u' • '.join(self.formatTitles(self.deleted)))
            else:
                changeWarning = ''
            if self.new:
                changeWarning += (u" {{Plus4}}"
                                  + u' • '.join(self.formatTitle(self.new)))
        else:
            changeWarning = u" création."
        if changeWarning:
            self.listPage.sectionUpdate(
                u'\nMise à jour le ~~~~~ pour un total de %d articles.\n%s\n'
                % (len(self.list), self.listString(self.list) + '\n'),
                changeWarning=(u"%s :%s" % (self.listName, changeWarning)))
            if self.totalPage:
                self.totalPage.sectionUpdate(str(len(self.list)))
            self.list = oldList
            # if self.deleted:
            #    output(u"{{Moins2}}"
            #           +u' • '.join([u'[[%s]]' % title
            #                         for title in self.deleted]))
            # if self.new:
            #    output(u"{{Plus4}}"
            #           + u' • '.join([u'[[%s]]' % title
            #                          for title in self.new]))
        # else:
        #    output(u"*:Pas de changement dans la liste.")

    def extractedList(self, listString):
        formatTag = Delimiter('* [[', ']]')
        titlesList = []
        for line in listString.split('\n'):
            try:
                titlesList.append(formatTag.split(line)[1])
            except IndexError:
                pass
        return unique(titlesList)

    def formatWithoutTalkpages(self, title):
        return u'* [[{}]]'.format(title)

    def formatWithTalkpages(self, title):
        return u'* [[{}]] ([[Discussion:{}|d]])'.format(title, title)

    def listString(self, titlesList=[]):
        """
        Formats the list's output.
        """
        if (self.talkpages and self.link):
            formatting = self.formatWithTalkpages
        else:
            formatting = self.formatWithoutTalkpages
        listDict = {}
        if self.link:
            titleTag = Delimiter('', '')
        else:
            listDict[''] = '<no' + 'wiki>\n'
            titleTag = Delimiter('\n</no' + 'wiki>', '\n<no' + 'wiki>')
            listDict['~~~'] = '\n</no' + 'wiki>'
        if self.sections:
            listDict['0'] = titleTag.englobe(u'\n== 0–9 ==')
            listDict['~'] = titleTag.englobe(u'\n== Autres ==')
            for ch in string.uppercase:
                listDict[ch] = titleTag.englobe('\n== {} =='.format(ch))
        for title in titlesList:
            key = self.sortTable.translate(title).lstrip().upper()
            if not key:
                key = '~~'
            while key in listDict.keys():
                key += '\t'
            listDict[key] = formatting(title)
        keysList = listDict.keys()
        keysList.sort()
        # if self.sections and keysList[0].startswith(' '):
        #    keysList.insert(0,'')
        #    listDict[''] = '\n== ! =='
        return "\n".join([listDict[key] for key in keysList])

fusionTitleP = re.compile('\n=+\s*(.*?)\s*=+\s*?\n')
titleP = re.compile('\[\[\s*([^#\|\]]*[^#\|\]\s])[^\]]*?\]\]')
linkP = re.compile('\[\[(?:[^\|\]]*\|)?([^\]]*)\]\]')
# linkP = re.compile('(.*?)\[\[(?:[^\|\]]*\|)?([^\]]*)\]\]([^\[]*)')


class NominationsChecklist(object):
    """
    Computes intersection of a sorted list of articles and categories

    Purpose : store nominated articles for deletion, labels and merge.

    the "gatherNominations" method initialize the component with project wide announces
    """

    def __init__(self):
        self.nominTypeDict = {'PAS': u'Page proposée à la suppression',
                              'PAF': u'Article à fusionner',
                              'PBA': u'Article potentiellement bon',
                              'PAdQ': u'Article potentiellement de qualité'}
        self.listOfFusionTitles = []

    def gatherNominations(self):
        """ initialize"""
        for key, name in self.nominTypeDict.items():
            cat = catlib.Category(wikipedia.getSite(), u'Category:{}'.format(name))
            self.nominTypeDict[key] = {article.title() for article in cat.articles()}

        PAFPage = wikipedia.Page(wikipedia.getSite(),
                                 u'Wikipédia:Pages à fusionner')

        self.listOfFusionTitles = fusionTitleP.findall(PAFPage.get())
        print(self.listOfFusionTitles)


class Portal(wikipedia.Page):
    """
    Subclass of Page that has some special tricks that only work for
    portal: pages
    """
    def __init__(self, site, name, logger, insite=None,  # sortTable = None,
                 iconMedia=u'Bullet (typography).svg',
                 edit=True, option=[]):
        wikipedia.Page.__init__(self, site, 'Portal:' + name,
                                insite=insite, ns=4)
        # if self.namespace() != 4:
        #   raise ValueError(u'BUG: %s is not in the project namespace!' % name)
        self.logger = logger
        self.name = uppercase_first(name)
        # linkedCatName = u'Portail:%s/Articles liés' % name

        watchlistPage = BotEditedPage(wikipedia.getSite(),
                                      u'Portail:{}/Liste de suivi'.format(name),
                                      botTag=bot_tag, create=True)
        totalPage = BotEditedPage(wikipedia.getSite(),
                                  u'Portail:{}/Total'.format(name),
                                  create=True)
        self.listUpdateRobot = ListUpdateRobot(
            watchlistPage,
            listName=u'* Portail:{}'.format(name),
            totalPage=totalPage,
            edit=edit and ('noedit' not in option),
            talkpages=True, link=('nolink' not in option))

        self.iconMedia = iconMedia
        self.option = option
        self.site = site

    def iconify(self, iconMedia=None):
        if iconMedia:
            self.iconMedia = iconMedia
        else:
            try:
                iconPage = wikipedia.Page(wikipedia.getSite(),
                                          u'Portail:{}/Icône'.format(self.name))
                self.iconMedia = noinclude_tag.expurge(iconPage.get())
            except:
                pass

    def listify(self):
        templist = []
        # wikipedia.output(u"Recherche du bandeau de portail %s" % self.name)
        try:
            template = wikipedia.Page(self.site,
                                      u'Modèle:Portail {}'.format(self.name))
            # wikipedia.output(u'OK.')
        except wikipedia.NoPage:
            self.logger.output = u"Bandeau introuvable avec le nom du portail."
            # return agreement(u"On continue ?", False)
            raise wikipedia.NoPage
        if template.isRedirectPage():
            # wikipedia.output(u"Recherche du titre correct du bandeau.")
            template = template.getRedirectTarget()
            # wikipedia.output(u"OK.")
        for pg in template.getReferences():
            if pg.namespace() == 0:
                templist.append(pg.title())
        # wikipedia.output(u'Liste constituée')
        self.listUpdateRobot.load(unique(templist))
        # wikipedia.output(u'Liste chargée')


class ProjectPage(wikipedia.Page):
    """
    Specialisation of class Page for "ProjectPage:" pages
    """
    def __init__(self, parameters, logger):
        wikipedia.Page.__init__(self, parameters.site, 'Project:' + parameters.name,
                                insite=parameters.insite)  # , defaultNamespace = 4)

        self._parameters = parameters
        self.logger = logger

        if self.namespace() != 4:
            print self.namespace()
            raise ValueError(u'BUG: {} is not in the project namespace'.format(self.name))

        self.portalsList = [Portal(name, params) for name, params in parameters.portals]

        self.titlesList = []

    @property
    def name(self):
        return uppercase_first(self._parameters.name)

    def maintenance(self, checklist=None):
        self.logger.output(u"\n'''[[Projet:{}]]'''".format(self.name))
        for portal in self.portalsList:
            portal.iconify()
            portal.listify()
            self.titlesList += portal.listUpdateRobot.list
            portal.listUpdateRobot.gatherNominations()
        self.titlesList = unique(self.titlesList)
        self.totalUpdate()
        self.newArticlesUpdate()
        if checklist:
            self.nominationsListUpdate(checklist)

    def totalUpdate(self):
        totalPage = BotEditedPage(wikipedia.getSite(),
                                  u'Projet:{}/Total articles'.format(self.name),
                                  create=True)

        totalPage.sectionUpdate(str(len(self.titlesList)))
        # output(u"Total : %s articles " % len(self.titlesList))

    # list title formatting utility functions

    def formatTitles(self, titleList):
        """ formats a list of titles into a list of wikilinks """
        return [u'[[{}]]'.format(title)
                for title in unique(titleList)
                ]

    def formatArticleList(self, titleList):
        """ formats a list of titles into a list of {{m|a}} corresponding template """
        return [u'* {{a|1={}}}'.format(title)
                for title in titleList
                ]

    def newArticlesUpdate(self):
        backupList = []
        for portal in self.portalsList:
            backupList += portal.listUpdateRobot.list
        sList = []
        deletedList = []
        for portal in self.portalsList:
            newList = []
            for title in portal.listUpdateRobot.new:
                if title not in backupList:
                    newList.append(title)
                    backupList.append(title)
            if newList:
                sList.append(':[[Fichier:{}|12x24px|{}|link=Portail:{}]] '
                             .format(portal.iconMedia, portal.name, portal.name)
                             + u' • '.join(self.formatTitle(newList)))

                # backupList += newList
            for title in portal.listUpdateRobot.deleted:
                if title not in self.titlesList:
                    deletedList.append(title)
        if deletedList:
            deletedArticleString = u' • '.join(self.formatTitles(deletedList))

            listString = '\n{{Moins2}} {}'.format(deletedArticleString)
        else:
            listString = ''

        if sList:
            listString += ('\n;{{subst:CURRENTDAY}}'
                           + ' {{subst:CURRENTMONTHNAME}}'
                           + ' {{subst:CURRENTYEAR}}\n'
                           + '\n'.join(sList))
        if listString:
            newArticlesPage = BotEditedPage(wikipedia.getSite(),
                                            u'Projet:{}/Articles récents'.format(self.name),
                                            botTag=bot_tag, create=True)

            oldList = newArticlesPage.editContent().split('\n;')
            listString += '\n;' + '\n;'.join(oldList[1:10])

            newArticlesPage.sectionUpdate(
                listString,
                changeWarning=(
                    u"Mise à jour des "
                    + u"[[Projet:{}/Articles récents|articles récents]].".format(self.name)))

    def nominationsListUpdate(self, checklist):
        projectChecklistDict = {}
        for key, nominatesList in checklist.nominTypeDict.items():
            projectChecklistDict[key] = interSortedLists(
                self.titlesList, nominatesList)
        projectFusionList = []
        missingTitlesList = []
        for fusionTitle in checklist.listOfFusionTitles:
            fusionList = titleP.findall(fusionTitle)
            for title in fusionList:
                if uppercase_first(title) in self.titlesList:
                    # title = lbranch_tag.expurge(empty_if_tag.expurge(
                    #   arg_tag.expurge(fusionTitle))).replace('|}}','').strip()
                    projectFusionList.append(
                        u'* %s ' % fusionTitle
                        + u'<small>([[Wikipédia:Pages à fusionner#'
                        + u'%s' % re.sub(linkP, r'\1', fusionTitle)
                        + u'|discussion]])</small>')
                    for titlebis in fusionList:
                        titlebis = uppercase_first(titlebis)  # .strip()
                        try:
                            projectChecklistDict['PAF'].remove(titlebis)
                        except ValueError:
                            if u'{' not in titlebis:
                                missingTitlesList.append(titlebis)
                    break
        fusionWarning = ''
        if missingTitlesList:

            msg = u"\nBandeau de fusion à vérifier pour : [[{article_list}]].\n"
            fusionTitlesStr = "]] • [[".join(missingTitlesList)

            fusionWarning = msg.format(article_list=fusionTitlesStr)

        if projectChecklistDict['PAF']:
                # fusion list report generation : handling fusions props without comments

            pafList = self.formatTitles(projectChecklistDict['PAF'])
            fusionWarning += (u"\nProposition de fusion sans discussion initiée pour : {}\n"
                              .format(u' • '.join(pafList)))
        text = ''.join([u"[[Image:Icono consulta borrar.png|20px]] ",
                        u"'''Pages à supprimer'''",
                        u' [[Wikipédia:Pages à supprimer#Avertissements',
                        u'|(dernières demandes)]]\n',
                        '\n'.join(self.formatArticleLinks(projectChecklistDict['PAS'])),
                        u"\n[[Image:Merge-arrows.svg|20px]] ",
                        u"'''Pages à fusionner''' ",
                        u'[[Wikipédia:Pages à fusionner#',
                        u'Requêtes à traiter au mois de {{CURRENTMONTHNAME}} ',
                        u'{{CURRENTYEAR}}|(liste du mois)]]\n',
                        '\n'.join(projectFusionList), fusionWarning,
                        '\n[[Image:Fairytale questionmark.png|20px]] ',
                        u"'''Propositions aux labels'''",
                        u' [[WP:AdQ|AdQ]] ou [[WP:BArt|BA]]\n',
                        '\n'.join([u'* {{a|1= %s}}' % t
                                   for t in (projectChecklistDict['PAdQ']
                                             + projectChecklistDict['PBA'])])])
        nominationsPage = BotEditedPage(wikipedia.getSite(),
                                        u'Projet:{}/Consultations'.format(self.name),
                                        botTag=bot_tag, create=True)

        # output(u"• [[Projet:%s/Consultations|Consultations]] " % self.name)

        consultationPattern = u"[[Projet:{projet}/Consultations|consultations]]"
        editMessage = (u"Mise à jour des " + consultationPattern.format(projet=self.name))

        nominationsPage.sectionUpdate('\n' + text + '\n',
                                      changeWarning=editMessage
                                      )

warnings_page = wikipedia.Page(wikipedia.getSite(),
                               u'Utilisateur:HyuBoT/Contrôle')

class HuyBotApp(object):

    @inject(io = IOModule)
    def __init__(self, io):
        self.io = io

    def run(self):
        nominations_checklist = NominationsChecklist()
        nominations_checklist.gatherNominations()

# Bot plumbing part
from snakeguice.assist import assisted_inject
from HyuBotIO import PageFactory, Outputter

class Reporter(object):
    '''class definition for Reporter'''

    @assisted_inject(page_factory=PageFactory, output=Outputter, config=Config)
    def __init__(self, page_factory, output, config):
        self._warnings_list = []
        self.page_factory = page_factory
        self.output_pagename = config
        self.outputter = output


    def output(self, text):
        """ method that both output to screen logger and saves the message"""
        self.add_warning(text)
        self.logger.output(text)

    def add_warning(self, warning):
        """appends a warning report to the message report in prevision of Final report"""
        self._warnings_list.append(warning)

    @property
    def warning_list(self):
        """ getter for warning list messages"""
        return self._warnings_list

    def final_report(self):
        #TODO: code
        pass

from snakeguice.modules import Module
from HyuBotIO import SimulateIOModule, IOModule

class HyuBotModule(Module):
    def configure(self, binder):
        self.install(binder, IOModule)

class SimuHyuBotModule(Module):
    def configure(self, binder):
        self.install(binder, SimulateIOModule())

from snakeguice import Injector

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
        inj = Injector(SimuHyuBotModule())
    else:
        inj = Injector(HyuBotModule())

    logger = inj.instance("Logger")
    app = inj.instance("Bot")

    checklist = app.gatherNominations()
    for proj_param in proj_param_list:
        ppage = ProjectPage(proj_param, logger=logger)
        ppage.maintenance(checklist=checklist)

    # reports the runs warnings on logging page

    wpage_header = u"Opérations du ~~~~~.\n"

    if utf2ascii.unknownCharList:

        # update non transcripted titles characters

        characters_warn_section = u"; Caractères non transcrits : {untranscriptedStr}.\n"
        warn_list = [u"'{char}' dans « [[{title}]] »".format(char=c, title=text)
                     for (c, text)
                     in utf2ascii.unknownCharList
                     ]
        wpage_header += (characters_warn_section.format(untranscriptedStr=u' – '.join(warn_list)))

    try:
        wpage_pattern = "{header}\n{warn_list}"

        wl_content = u'\n'.join(warnings_list)
        header = wpage_header
        warnings_page.put(wpage_pattern.format(header=header,
                                               warn_list=wl_content),
                          comment=u'Contrôle des opérations effectuées.')

    except Exception as e:
        wikipedia.output(u"Erreur lors de l'édition du contrôle.\n {msg}".format(e.msg))
    finally:
        wikipedia.stopme()

if __name__ == "__main__":
    main()
