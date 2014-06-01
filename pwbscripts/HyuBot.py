#!/usr/bin/python
# -*- coding: utf-8 -*-

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
    * ?
"""

import string, re

import pywikibot as wikipedia
import pywikibot.catlib as catlib

# TODO: check the API to know if it is still needed (quick and dirty fix)
def unique(l):
    """Given a list of hashable object, return an alphabetized unique list."""
    l = dict.fromkeys(l).keys()
    l.sort()
    return l

catlib.unique = unique

"""
Toolkit
"""

# store for the warnings to report on some userpage
warnings_list = []

def output(text):
    wikipedia.output(text)
    warnings_list.append(text)

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
                if not self.dict.has_key(c):
                    self.unknownCharList.append((c, text))
            return "".join([self.dict.get(c, self.dict.get(None, c))
                            for c in text])

utf2ascii = TranslationTable(
    dicOfRelatives={
        'a': u'áàâäåāảãăạąặắǎấầ', # 'а' dans l'alphabet cyrillique
        'e': u'éêèëěėễệęềếē', 'i': u'íîïīıìịǐĩ',
        'o': u'óôöōőøõòơồόŏờốṓởǫỗớ', # les deux accents aigus sont différents
        'u': u'ùûüūúưứŭũửůűụ', 'y':u'ÿýỳ',
        'A': u'ÀÂÄÅÁĀ', 'E': u'ÉÊÈËĖ', 'I': u'ÎÏİÍ', 'O': u'ÔØÖŌÓÕ',
        'U': u'ÙÛÜÚŪ',
        'ae': u'æ', 'AE': u'Æ', 'oe': u'œ', 'OE': u'Œ',
        'c': u'çćč', 'C': u'ÇČĈĆ', 'd': u'đð', 'D':u'ĐD̠',
        'g': u'ğġǧ', 'G': u'Ğ', 'h':u'ĥħ', 'H':u'ḤĦ', 'l': u'ḷłľℓļ', 'L': u'ŁĽ',
        'm': u'ṃ', 'n': u'ńñňṇņ', 'r':u'řṛṟ', 's': u'śšşs̩ṣș', 'S': u'ŠŞŚŜȘ',
        't':u'ţťt̠țṭ', 'T':u'T̩ŢȚ', 'z':u'žżź', 'Z':u'ŻŽ',
        'ss': u'ß', 'th':u'þ', 'Th': u'Þ', 'TM': u'™',
        'alpha': u'α', 'beta': u'β', 'gamma': u'γ', 'Gamma': u'Γ',
        'delta': u'δ', 'Delta': u'Δ', 'epsilon': u'ε', 'zeta': u'ζ',
        'eta': u'η', 'theta': u'θ', 'iota': u'ι', 'kappa': u'κ',
        'lambda': u'λ', 'Lambda': u'Λ', 'mu': u'μ', 'nu': u'ν',
        'xi': u'ξ', 'omicron': u'ο', 'pi': u'π', 'rho': u'ρ',
        'sigma': u'σ', 'Sigma': u'Σ', 'tau': u'τ', 'upsilon': u'υ',
        'phi': u'φϕ', 'Phi': u'Φ', 'chi': u'χ', 'psi': u'ψ', 'Psi': u'Ψ',
        'omega': u'ω', 'Omega': u'Ω',
        '1 2': u'½', '2': u'²', '3': u'³', 'micro': u'µ', # symbole différent de la lettre mu
        ' ': u'’–−∞×÷≡«»°…—®⊥‐√ʼ§' + string.whitespace + string.punctuation,
        # à traiter : '‘´'
        # supprimé : 人
        '':u'·ʿ‘' #diacritiques ou lettres négligées et caractère pour la coupure d'un mot
    },
    defaultValue=' '
)

def uppercase_first(text):
    """ returns a similar string with the first characters uppercased""" 
    if text:
        return text[0].upper() +  text[1:]
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
            #else:
            #    print [el, list1[index]]
        except IndexError:
            break
    return intersection

def oddIndexList(longList):
    return [longList[i] for i in range(1, len(longList), 2)]

class Tag:
    """
    Specifies start tag and end tag.

    class
    """
    def __init__(self, startTag = '', endTag = None):
        """
        intialisation of the begin and end delimeter
        used to extract a substring in a text
        """
        self.start = startTag
        self.end = endTag

    def indices(self, txt, textFrom = 0):
        """ computes the indexes of the substring delimited by the start and end delimiters

        (or (StartIndex, None) if there is no end delimiters
        """
        startIndex = txt.index(self.start, textFrom)
        if self.end:
            try:
                endIndex = txt.index(self.end, startIndex + len(self.start))
            except ValueError:
                endIndex = None
        else:
            endIndex = None
        return (startIndex, endIndex)

    def split(self, text):
        result = []
        index = 0
        try:
            while 1:
                (startIndex, endIndex) = self.indices(text, index)
                result.append(text[index:startIndex])
                result.append(text[startIndex+len(self.start):endIndex])
                index = endIndex+len(self.end)
        except ValueError:
            result.append(text[index:])
        except TypeError:
            if self.end:
                output(u"Balise de fin %s manquante." % self.end)
        return result

    def rebuild(self, stringList):
        outside = True
        try:
            result = [stringList[0]]
        except IndexError:
            result = []
        for s in stringList[1:]:
            if outside:
                result.append(self.start)
            else:
                result.append(self.end)
            outside = not(outside and self.end)
            result.append(s)
        return ''.join(result)

    def expurge(self, text, explicitEnd = False):
        stringList = self.split(text)
        outside = True
        result = [stringList[0]]
        for s in stringList[1:]:
            outside = not(outside)
            if outside:
                result.append(s)
        if explicitEnd:
            if len(stringList) % 2 == 0:
                result.append(self.start)
                result.append(stringList[-1])
        return ''.join(result)

    def englobe(self, text):
        return self.start + text + self.end

class HtmlTag(Tag):
    def __init__(self, s):
        self.start = '<%s>' % s
        self.end = '</%s>' % s

bot_tag = Tag('', '<!-- FIN BOT -->')
link_tag = Tag(u'[[', u']]')

arg_tag = Tag(u'{{{', u'}}}')

comment_tag = Tag('<!--', '-->')
includeonly_tag = HtmlTag('includeonly')
noinclude_tag = HtmlTag('noinclude')
nowiki_tag = HtmlTag('nowiki')

"""
Classes and functions for pywikipedia.
"""

class BotEditPage(wikipedia.Page):
    """
    Subclass of Page aimed to be edited by a bot.
    """
    def __init__(self, site, title, insite=None, botTag=None,
                 create=False
                 #sectionLevel=None, edit=True
                 ):
        wikipedia.Page.__init__(self, site, title,
                                insite=insite)
        if botTag:
            self.botTag = botTag
        else:
            self.botTag = Tag()
        self.splitting = []
        self.editSummary = u'Robot : mise à jour'
        self.recovered = False
        self.create = create
        #self.edit = edit

    def recover(self):
        """
        Recovers page's content, split along start and end tags.
        """
        if not self.recovered:
            try:
                self.splitting = self.botTag.split(self.get())
            except wikipedia.NoPage:
                output(u"\nLa page %s n'existe pas." % self.title())
                if self.create:
                    self.splitting = ['', '']
                else:
                    raise wikipedia.NoPage
            finally:
                self.recovered = True

    def sectionString(self, sectionNumber = 0):
        return self.splitting[2*sectionNumber+1]

    def sectionUpdate(self, newSection, sectionNumber = 0,
                      changeWarning = None, noChangeWarning = False,
                      comment = None):
        if not self.recovered:
            self.recover()

        index = 2*sectionNumber+1
        try:
            oldSection = self.splitting[index]
        except IndexError:
            output(u"Balise de début {} manquante".format(self.botTag.start)
                   + u" ou numéro de section {} trop élevé".format(str(sectionNumber))
                   + u" dans la page {}.".format(self.title()))

            if self.create:
                output(u"Création de la section à la suite du texte.")
                oldSection = ''
            else:
                output(u"Abandon des modifications.")
                return
        if oldSection == newSection:
            if noChangeWarning:
                output(u"Pas de changement sur la page {}.".format(self.title()))
            return
        if not comment:
            comment = self.editSummary
        head = self.botTag.rebuild(self.splitting[:index])
        try:
            tail = self.botTag.rebuild(self.splitting[index+1:])
        except IndexError:
            tail = ''
        try:
            self.put(self.botTag.rebuild([head, newSection, tail]),
                     comment = comment)
        except:
            output(u"Erreur pendant l'édition de la page [[%s]]."
                   % self.title())
        else:
            if changeWarning:
                output(changeWarning)

    def editContent(self, sectionNumber = 0):
        if not self.recovered:
            self.recover()
        index = 2*sectionNumber+1
        try:
            body = self.splitting[index]
        except IndexError:
            output(u"Balise de début %s manquante"
                   + u" ou numéro de section %s trop élevé"
                   + u" dans la page %s."
                   % (self.botTag.start, str(sectionNumber), self.title()))
            raise IndexError
        #else:
        #    if self.botTag.end and (len(self.splitting) == index+1):
        #        wikipedia.output('End tag missing in %s.'
        #                         % self.title())
        return body

    def update(self, newString, sectionNumber = 0, edit = True, comment = None,
               warning = False):
        if self.exists():
            try:
                body = self.editContent(sectionNumber)
            except IndexError:
                self.edit = agreement(u'Add bot edit section?', True)
                body = ''
        else:
            self.edit = agreement(u'Page %s does not exist. Create?'
                                  % self.title(), default = self.edit)
        if newString == body:
            self.edit = False
        elif self.edit and edit:
            if not comment:
                comment = self.editSummary
            if warning:
                output(u"(mise à jour) ")
            index = 2*sectionNumber+1
            head = self.botTag.rebuild(self.splitting[:index])
            try:
                tail = self.botTag.rebuild(self.splitting[index+1:])
            except IndexError:
                tail = ''
            try:
                self.put(self.botTag.rebuild([head, newString, tail]),
                         comment=comment)
            except:
                output(u"Erreur pendant l'édition de la page [[%s]]."
                       % self.title())
        else:
            output(u"Pas de modification de la page [[%s]]." % self.title())

class ListUpdateRobot:
    """
    Updates a page containing a list of articles.
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

    def run(self): #, #newlist = [], edit = True, create = True):
        if not self.edit:
            return
        #try:
        self.listPage.recover() #create = create)
        #except wikipedia.NoPage:
        #    return
        oldList = self.extractedList(self.listPage.sectionString())
        #wikipedia.output(u'Liste extraite')
        #except wikipedia.Error:
        #    oldList = []
        #except IndexError:
        #    oldList = []
        if oldList:
            (self.new, self.deleted) = compareSortedLists(self.list, oldList)
        #wikipedia.output(u'Comparaison effectuée')
            if self.deleted:
                changeWarning = (u" {{Moins2}}"
                                 + u' • '.join([u'[[%s]]' % title
                                                for title in self.deleted]))
            else:
                changeWarning = ''
            if self.new:
                changeWarning += (u" {{Plus4}}"
                                  + u' • '.join([u'[[%s]]' % title
                                                 for title in self.new]))
        else:
            changeWarning = u" création."
        if changeWarning:
            self.listPage.sectionUpdate(
                u'\nMise à jour le ~~~~~ pour un total de %d articles.\n%s\n'
                % (len(self.list), self.listString(self.list) +'\n'),
                changeWarning = (u"%s :%s" % (self.listName, changeWarning)))
            if self.totalPage:
                self.totalPage.sectionUpdate(str(len(self.list)))
            self.list = oldList
            #if self.deleted:
            #    output(u"{{Moins2}}"
            #           +u' • '.join([u'[[%s]]' % title
            #                         for title in self.deleted]))
            #if self.new:
            #    output(u"{{Plus4}}"
            #           + u' • '.join([u'[[%s]]' % title
            #                          for title in self.new]))
        #else:
        #    output(u"*:Pas de changement dans la liste.")

    def extractedList(self, listString):
        formatTag = Tag('* [[',']]')
        titlesList = []
        for line in listString.split('\n'):
            try:
                titlesList.append(formatTag.split(line)[1])
            except IndexError:
                pass
        return catlib.unique(titlesList)

    def formatWithoutTalkpages(self, title):
        return u'* [[{}]]'.format(title)

    def formatWithTalkpages(self, title):
        return u'* [[{}]] ([[Discussion:{}|d]])'.format(title, title)

    def listString(self, titlesList=[]):
        """
        Formats the list's output.
        """
        if (self.talkpages and self.link):
            format = self.formatWithTalkpages
        else:
            format = self.formatWithoutTalkpages
        listDict = {}
        if self.link:
            titleTag = Tag('','')
        else:
            listDict[''] = '<no'+'wiki>\n'
            titleTag = Tag('\n</no'+'wiki>', '\n<no'+'wiki>')
            listDict['~~~'] = '\n</no'+'wiki>'
        if self.sections:
            listDict['0'] = titleTag.englobe(u'\n== 0–9 ==')
            listDict['~'] = titleTag.englobe(u'\n== Autres ==')
            for ch in string.uppercase:
                listDict[ch] = titleTag.englobe('\n== %s ==' % ch)
        for title in titlesList:
            key = self.sortTable.translate(title).lstrip().upper()
            if not key:
                key = '~~'
            while key in listDict.keys():
                key += '\t'
            listDict[key] = format(title)
        keysList = listDict.keys()
        keysList.sort()
        #if self.sections and keysList[0].startswith(' '):
        #    keysList.insert(0,'')
        #    listDict[''] = '\n== ! =='
        return "\n".join([listDict[key] for key in keysList])

fusionTitleP = re.compile('\n=+\s*(.*?)\s*=+\s*?\n')
titleP = re.compile('\[\[\s*([^#\|\]]*[^#\|\]\s])[^\]]*?\]\]')
linkP = re.compile('\[\[(?:[^\|\]]*\|)?([^\]]*)\]\]')
#linkP = re.compile('(.*?)\[\[(?:[^\|\]]*\|)?([^\]]*)\]\]([^\[]*)')

class NominationsChecklist:
    """
    Checks intersection of a sorted list of articles
    and categories of nominates articles for deletion, labels and merge.
    """
    def __init__(self):
        self.nominTypeDict = {'PAS':u'Page proposée à la suppression',
                              'PAF':u'Article à fusionner',
                              'PBA':u'Article potentiellement bon',
                              'PAdQ':u'Article potentiellement de qualité'}
        self.listOfFusionTitles = []

    def fusionList(self, s):
        try:
            index = s.index('{{')
        except ValueError:
            try:
                index = s.index('==')
            except ValueError:
                return []
        return oddIndexList(link_tag.split(s[:index]))

    def run(self):
        for key, name in self.nominTypeDict.items():
            cat = catlib.Category(wikipedia.getSite(), u'Category:%s' % name)
            self.nominTypeDict[key] = catlib.unique([
                    article.title() for article in cat.articles()])
        PAFPage = wikipedia.Page(wikipedia.getSite(),
                                 u'Wikipédia:Pages à fusionner')
        self.listOfFusionTitles = fusionTitleP.findall(PAFPage.get())
        print self.listOfFusionTitles

class Portal(wikipedia.Page):
    """
    Subclass of Page that has some special tricks that only work for
    portal: pages
    """
    def __init__(self, site, name, insite=None, #sortTable = None,
                 iconName=u'Bullet (typography).svg',
                 edit=True, option = []):
        wikipedia.Page.__init__(self, site, 'Portal:'+name,
                                insite=insite, ns=4)
        #if self.namespace() != 4:
        #   raise ValueError(u'BUG: %s is not in the project namespace!' % name)
        self.name = uppercase_first(name)
        #linkedCatName = u'Portail:%s/Articles liés' % name
        watchlistPage = BotEditPage(wikipedia.getSite(),
                                    u'Portail:%s/Liste de suivi' % name,
                                    botTag=bot_tag, create=True)
        totalPage = BotEditPage(wikipedia.getSite(),
                                u'Portail:{}/Total'.format(name),
                                create=True)
        self.listUpdateRobot = ListUpdateRobot(
            watchlistPage, 
            listName=u'* Portail:{}'.format(name),
            totalPage=totalPage,
            edit=edit and ('noedit' not in option),
            talkpages=True, link = ('nolink' not in option))
        self.iconName = iconName
        self.option = option

    def iconify(self, iconName=None):
        if iconName:
            self.iconName = iconName
        else:
            try:
                iconPage = wikipedia.Page(wikipedia.getSite(),
                                          u'Portail:%s/Icône' % self.name)
                self.iconName = noinclude_tag.expurge(iconPage.get())
            except:
                pass

    def listify(self):
        templist = []
        #wikipedia.output(u"Recherche du bandeau de portail %s" % self.name)
        try:
            template = wikipedia.Page(wikipedia.getSite(),
                                      u'Modèle:Portail %s' % self.name)
            #wikipedia.output(u'OK.')
        except wikipedia.NoPage:
            output = u"Bandeau introuvable avec le nom du portail."
            #return agreement(u"On continue ?", False)
            raise wikipedia.NoPage
        if template.isRedirectPage():
            #wikipedia.output(u"Recherche du titre correct du bandeau.")
            template = template.getRedirectTarget()
            #wikipedia.output(u"OK.")
        for pg in template.getReferences():
            if pg.namespace() == 0:
                templist.append(pg.title())
        #wikipedia.output(u'Liste constituée')
        self.listUpdateRobot.load(catlib.unique(templist))
        #wikipedia.output(u'Liste chargée')

class Project(wikipedia.Page):
    """
    Specialisation of class Page for "Project:" pages
    """
    def __init__(self, site, name, insite=None, portalNamesList=[],
                 portalEdit=True, option={}):
        wikipedia.Page.__init__(self, site, 'Project:'+name,
                                insite=insite) #, defaultNamespace = 4)
        if self.namespace() != 4:
            print self.namespace()
            raise ValueError(u'BUG: %s is not in the project namespace' % title)
        self.name = uppercase_first(name)
        self.portalsList = [Portal(wikipedia.getSite(),portalName,
                                   edit = portalEdit,
                                   option = option.get(portalName, []))
                            for portalName in portalNamesList]
        self.titlesList = []

    def maintenance(self, checklist=None):
        output(u"\n'''[[Projet:%s]]'''" % self.name)
        for portal in self.portalsList:
            portal.iconify()
            portal.listify()
            self.titlesList += portal.listUpdateRobot.list
            portal.listUpdateRobot.run()
        self.titlesList = catlib.unique(self.titlesList)
        self.totalUpdate()
        self.newArticlesUpdate()
        if checklist:
            self.nominationsListUpdate(checklist)

    def totalUpdate(self):
        totalPage = BotEditPage(wikipedia.getSite(),
                                u'Projet:%s/Total articles' % self.name,
                                create=True)
        totalPage.sectionUpdate(str(len(self.titlesList)))
        #output(u"Total : %s articles " % len(self.titlesList))

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
                sList.append(':[[Fichier:%s|12x24px|%s|link=Portail:%s]] '
                             % (portal.iconName, portal.name, portal.name)
                             + u' • '.join([u'[[%s]]' % title
                                            for title in newList]))
                #backupList += newList
            for title in portal.listUpdateRobot.deleted:
                if title not in self.titlesList:
                    deletedList.append(title)
        if deletedList:
            listString = (
                u'\n{{Moins2}} '
                + u' • '.join([u'[[%s]]' % title
                               for title in catlib.unique(deletedList)]))
        else:
            listString = ''
        if sList:
            listString += ('\n;{{subst:CURRENTDAY}}'
                           + ' {{subst:CURRENTMONTHNAME}}'
                           + ' {{subst:CURRENTYEAR}}\n'
                           + '\n'.join(sList))
        if listString:
            newArticlesPage = BotEditPage(wikipedia.getSite(),
                                          u'Projet:{}/Articles récents'.format(self.name),
                                          botTag=bot_tag, create=True)
            oldList = newArticlesPage.editContent().split('\n;')
            listString += '\n;'+'\n;'.join(oldList[1:10])
            newArticlesPage.sectionUpdate(
                listString,
                changeWarning=(
                    u"Mise à jour des "
                    + u"[[Projet:%s/Articles récents|articles récents]].".format(self.name)))

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
                    #title = lbranch_tag.expurge(empty_if_tag.expurge(
                    #   arg_tag.expurge(fusionTitle))).replace('|}}','').strip()
                    projectFusionList.append(
                        u'* %s ' % fusionTitle
                        + u'<small>([[Wikipédia:Pages à fusionner#'
                        + u'%s' % re.sub(linkP,r'\1',fusionTitle)
                        + u'|discussion]])</small>')
                    for titlebis in fusionList:
                        titlebis = uppercase_first(titlebis) #.strip()
                        try:
                            projectChecklistDict['PAF'].remove(titlebis)
                        except ValueError:
                            if u'{' not in titlebis:
                                missingTitlesList.append(titlebis)
                    break
        fusionWarning = ''
        if missingTitlesList:
            fusionWarning = (
                u"\nBandeau de fusion à vérifier pour : [[{}]].\n"
                    .format("]] • [[".join(missingTitlesList))
            )
        if projectChecklistDict['PAF']:
                # fusion list report generation : handling fusions props without comments
                
            pafList = [u'[[{}]]'.format(title)
             for title in projectChecklistDict['PAF']
            ]
            fusionWarning += (u"\nProposition de fusion sans discussion initiée pour : {}\n"
                              .format( u' • '.join(pafList))
        text = ''.join([u"[[Image:Icono consulta borrar.png|20px]] ",
                        u"'''Pages à supprimer'''",
                        u' [[Wikipédia:Pages à supprimer#Avertissements',
                        u'|(dernières demandes)]]\n',
                        '\n'.join([u'* {{a|1= {}}}'.format(title)
                                   for title in projectChecklistDict['PAS']]),
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
        nominationsPage = BotEditPage(wikipedia.getSite(),
                                      u'Projet:{}/Consultations'.format(self.name),
                                      botTag=bot_tag, create=True)
        #output(u"• [[Projet:%s/Consultations|Consultations]] " % self.name)
        nominationsPage.sectionUpdate(
            '\n'+text+'\n',
            changeWarning = (u"Mise à jour des "
                             + u"[[Projet:{}/Consultations|consultations]]."
                             .format(self.name)))

projects_list = [
    Project(wikipedia.getSite(), u'Mathématiques',
                     portalNamesList=[u'Mathématiques',
                                        #u'Algèbre nouvelle',
                                        u'Algèbre',
                                        u'Algorithmique',
                                        u'Analyse',
                                        u'Géométrie',
                                        u'Informatique théorique',
                                        u'Logique',
                                        u'Probabilités et statistiques',
                                        u'Arithmétique et théorie des nombres']),
    Project(wikipedia.getSite(), u'Alimentation et gastronomie',
                     portalNamesList=[u'Alimentation et gastronomie',
                                        u'Bière',
                                        #u'Café',
                                        u'Chocolat',
                                        u'Fromage',
                                        u'Pomme de terre',
                                        u'Vigne et vin',
                                        u'Whisky']),
    Project(wikipedia.getSite(), u'Économie',
                     portalNamesList = [u'Économie',
                                        u'Commerce',
                                        #u'Entreprises',
                                        u'Finance',
                                        u'Industrie',
                                        u'Management']),
    Project(wikipedia.getSite(), u'Littérature',
                     portalNamesList = [u'Littérature',
                                        u'Fantasy',
                                        u'Poésie',
                                        u'Polar',
                                        u'Science-fiction'],
                     option = {u'Littérature':['nolink']}),
    Project(wikipedia.getSite(), u'Nord-Pas-de-Calais',
                     portalNamesList = [u'Nord-Pas-de-Calais',
                                        u'Bassin minier du Nord-Pas-de-Calais',
                                        u'Flandres',
                                        u'Lille Métropole'])]

warnings_page = wikipedia.Page(wikipedia.getSite(),
                               u'Utilisateur:HyuBoT/Contrôle')

if __name__ == "__main__":
    entete = u"Opérations du ~~~~~.\n"
    nominations_checklist = NominationsChecklist()
    nominations_checklist.run()
    for project in projects_list:
        project.maintenance(checklist = nominations_checklist)
    if utf2ascii.unknownCharList:
        entete += (u"; Caractères non transcrits : {}.\n"
                   .format(u' – '.join([u"'{}' dans « [[{}]] »".format(c, text)
                                  for (c, text)
                                  in utf2ascii.unknownCharList])))
    try:
        warnings_page.put(entete
                          + u'\n'.join(warnings_list),
                          comment=u'Contrôle des opérations effectuées.')
    except:
        wikipedia.output(u"Erreur lors de l'édition du contrôle.")
    finally:
        wikipedia.stopme()
