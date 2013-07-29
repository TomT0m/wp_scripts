#! /usr/bin/python
# -*- coding: UTF-8 -*-
"""
#Description: Déplace les annonces de proposition de suppression de la page Projet:Informatique vers la page d'annonces
"""

import re, logging
from functools import total_ordering

import wikipedia as pywikibot
import mwparserfromhell


# Constants

ANNOUNCE_DEL_TMPL = "Annonce proposition suppression"
ANNOUNCE_FUSION_TMPL = "Annonce fusion d'articles"

# utilitary classes

@total_ordering
class Date(object):
	""" A french (very) simple date object, comparable and that's it, 
	assumes dates are corrects 
	
	>>> a = Date('1', 'janvier', 2013)
	>>> b = Date('1', 'janvier', 2014)
	>>> a < b
	True
	"""
	MOIS = u" janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(u" ")
	REV_MOIS = None 

	def __init__(self, jour, mois, annee):
		if not Date.REV_MOIS:
			Date.REV_MOIS = { self.MOIS[x]:x for x in range(1, 13)}
		self._jour = int(jour)
		self._mois = self.REV_MOIS[mois]
		self._annee = int(annee)

	def __eq__(self, other):
		return self.jour == other.jour and self.mois == other.mois and self.annee == other.annee

	def __lt__(self, other):
		return self.annee < other.annee or (
			self.annee == other.annee and self.mois < other.mois or (
				self.mois == other.mois and self.jour < other.jour))
	def __str__(self):
		res = u"{:2d} {} {:4d}".format(self.jour, self.MOIS[self.mois], self.annee)
		return res
	
	def __repr__(self):
		res = "{:2d} {} {:4d}".format(self.jour, self.MOIS[self.mois], self.annee)
		return res

	@property
	def mois(self):
		""" Mois """
		return self._mois
	
	@property
	def annee(self):
		""" année """
		return self._annee
	@property
	def jour(self):
		""" jour """
		return self._jour

def extract_date(text):
	u""" Returns a date object if text seems to countain a date textual description,
	None otherwide 
	
	
	>>> extract_date("ZRezsdfsertzer")
	
	>>> extract_date("10 janvier 2042")
	10 janvier 2042

"""
	for line in text.split("\n"):
		mois = Date.MOIS
		re_mois = u"{}".format(u"|".join(mois))
		match = re.search(u"({jour}) ({mois}) ({annee})".format(mois = re_mois, 
							jour = u"[0-9]{1,2}",
							annee = u"[0-9]{4}"),line)
		if match:
			return Date(match.group(1), match.group(2), match.group(3))
	return None


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
	newpage = re.sub(del_pattern, '', text, flags = re.MULTILINE)


	logging.debug(u"(taille en octets) : Supprimé {} - nouvelle : {}, ancienne {}, différence {}: ".format(del_sum, 
						     len(newpage), 
						     len(text), 
						     del_sum-(len(text) - len(newpage))))
	
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
	match = re.findall("\[\[(.*?)\]\]", title)
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
	expected = unicode(section.filter_wikilinks(matches = u"Wikipédia:Pages à fusionner#")[0])
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
	
	sections = parsed.get_sections([2], matches = u"Les articles .*? sont proposés à la fusion")
	
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
	
	(preamble, following ) = old_text.split( sep_preamble, 1)
	(section_annonces, rest) = following.split( sep_end, 1 )

	# prétraitement des annonces : création d'une liste de couple (template, Date)
	announces_lines = section_annonces.split(u"\n")
	
	dated_old_announces = [ (text, extract_date(text)) 
			for text in announces_lines if text != u""]
	
	# tri par date
	sorted_announces = sorted( dated_old_announces + dated_new_announces, 
			   key = lambda (_, date): date, reverse = True)

	# création de la section finale

	new_section = u"\n".join([ text for text, _ in sorted_announces])

	return preamble + sep_preamble + u"\n" + new_section + u"\n" + sep_end + rest


class PageStatus:
	""" Status object """
	def __init__(self, page):
		self.page = page
		self._cached_content = None
		self.edit_comment = u""
		self._original_content = None
		self.modified = False

	def get_content(self):
		""" cached access to page content """
		if not self._cached_content:
			self._cached_content = self.page.get(get_redirect = True)
			self._original_content = self._cached_content

		return self._cached_content
	
	def set_content(self, new_text, comment):
		""" setter for content, without writing"""
		self._cached_content = new_text
		if self.edit_comment != "":
			self.edit_comment += u"; " + comment
		else:
			self.edit_comment = comment

		self.modified = new_text != self._original_content

	def save(self):
		""" saves the current content on server """
		self.page.put(self._cached_content, comment = self.edit_comment)

	def is_proposed_to_deletion(self):
		""" try to guess if there is a deletion proposition related to this page"""
		
		re_bandeau = re.compile(u"{{(suppression|à supprimer)}}", re.IGNORECASE)
		re_pas_closed = re.compile(u"{{Article (supprimé|conservé)", re.IGNORECASE)

		if self.page.exists():
			
			nom_discussion_suppression = "Discussion:" + self.page.title() + "/Suppression"
			
			content = self.get_content()
			has_status = re_bandeau.search(content)

			if not has_status:
				discussion_suppression = get_page(nom_discussion_suppression)
				res = re_pas_closed.search(discussion_suppression.get(get_redirect = True))
				
				if not res: 
					# inconsistent state :
					# TODO: treat
					pywikibot.output("État incohérent entre la page et la page de suppression")
					return True
				else: 
					return False
			return True
		return False

	def is_proposed_to_fusion(self):
		""" try to guess if there is a deletion proposition related to this page"""

		return u'{{à fusionner|' in self.get_content()

	def fusion_with(self):
		"""get the list of article titles which are supposed to be fusioned with this one"""
		parsed = mwparserfromhell.parse(self.get_content())
		for tmpl in parsed.filter_template():
			if tmpl.name == u"à fusionner":
				print(tmpl)

	def show_diff(self):
		""" show our changes """
		if self._cached_content:
			pywikibot.showDiff(self._original_content, self._cached_content)

def get_page_status(pagename):
	""" Returns a page status object 
	>>> get_page_status("Plop").page
	Page{[[fr:Plop]]}
	"""
	site = pywikibot.getSite("fr")
	page = pywikibot.Page(site, pagename)

	return PageStatus(page)


# writing functions

def projects_maintenance(projects, options):
	""" Function launching maintenance for all projects """
	for project in projects:
		# TODO: log
		
		pywikibot.log("Project : " + project.project_name)
		
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
		status = get_page_status(article_title)
		if status.is_proposed_to_deletion():
			pywikibot.output("* still opened")
		else:
			if "fait" not in announce:
				announce.add(2, u"fait")
	return unicode(parsed)


def get_page(name, namespace = None):
	""" get a Page in frwiki """
	site = pywikibot.getSite("fr")

	if namespace:
		return pywikibot.Page(site, name, defaultNamespace = namespace)
	
	return pywikibot.Page(site, name)

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
	logging.info(u"Before : {} ; After {} ; expected around {}".format(len(discussion_text),
							    len(new_discussion_text),
							    len(discussion_text) - len(articles) * 1200))
	logging.info(u"Articles extraits")
	for elem  in articles :
		(nom, date) = elem
		logging.info(u"Date d'annonce : {} ; Article à supprimer : {}".format(date, nom))
	
	# insertions des annonces extraites dans la page d'annonce
	
	dated_new_announces = [ (format_del_announce(date, name), date) 
			for name, date in articles]
	new_announces_text = insert_new_announces(announces_text, dated_new_announces)

	# mise à jour de l'état des annonces #
	new_announces_text = deletion_prop_status_update(new_announces_text)
	
	
	comment = u"Déplacements vers [[{}|la page d'annonces]]".format(announces_pagename)
	announce_comment = u"proposition(s) de suppression déplacée(s) depuis [[{}|La page de discussion]]"\
				.format(discussion_pagename)
	
	project.discussion_page.set_content(new_discussion_text, comment)
	project.announce_page.set_content(new_announces_text, announce_comment) 


def format_fusion_props(articles, section, date):
	""" format a fusion proposition """
	debut = u"{{Annonce fusion d'article|" + unicode(date) + u'|[[{}|Proposition de fusion]] entre '.format(section)
	suite = ""
	if len(articles) > 2:
		suite = u", ".join(u'[[{}]]'.format(articles[3:]))
	msg = debut + suite + u'[[' + articles[1] + u']]' + u" et [["+ articles[0] + ']]'

	return msg

def fusion_prop_maintenance(project):
	""" Testing """
	logging.info("gestion des propositions de fusion ...")
	(fusion_prop_list, new_d_text) = extract_fusion_props(project.discussion_page.get_content())
	
	if len(fusion_prop_list) > 0:
		dated_new_announces = [ (format_fusion_props(*elem), elem[2] ) for elem in fusion_prop_list ]
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
	options = ArgumentParser()

	options.add_argument('-s', '--simulate', action='store_true', 
		    help = "don't save changes", dest = "simulate")
	options.add_argument('-t', '--test', action='store_true', 
		    help = "run tests", dest = "test")
	options.add_argument('-p', '--page', 
		    help = "run tests", metavar="PAGE", dest = "page",
		    default = "Projet:Informatique")
	options.add_argument('-v', '--verbose', action = 'store_true',
		    help = "show debugging messages", dest = "debug")	
	return options



class ProjectParameters(object):
	""" Project parameters storage class, stores :
		* project name
		* parameters pages names : Announces, discussion pagename.
	"""
	def __init__(self, 
	      project_name, 
	      wiki_basename, 
	      announce_pagename=None, 
	      discussion_pagename=None
	     ):
		self.wiki_basename = wiki_basename
		self.project_name = project_name
		self._announce_pagename = announce_pagename
		self._discussion_pagename = discussion_pagename
		
		self._discussion = None
		self._announce = None

	@property
	def announce_pagename(self):
		""" Getter for announce pagename property """
		if self._announce_pagename:
			return self._announce_pagename
		else:
			return self.wiki_basename + "/Annonces"

	@property
	def discussion_pagename(self):
		""" get discussion pagename """
		if self._discussion_pagename:
			return self._discussion_pagename
		else:
			return "Discussion {}".format(self.wiki_basename)
	
	@property
	def discussion_page(self):
		""" get discussion page object (last version if we modified on the program) """
		if not self._discussion:
			self._discussion = get_page_status(self.discussion_pagename)
		return self._discussion

	@property
	def announce_page(self):
		""" get our announce_page object """

		if not self._announce:
			self._announce = get_page_status(self.announce_pagename)
		return self._announce


PROJETS = [
	ProjectParameters("Informatique", "Projet:Informatique"),
]


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
		return len([ line for line in text.split("\n")  
	      			if "==" in line ])
	def test_real(self):
		""" Real World extraction """
		text = FULL_TEST
		num_titles = self.count_titles(text)
		(articles, new_text) = extract_full_del_props(text)
		new_num_titles = self.count_titles(new_text)
		self.assertEqual(num_titles , len(articles)+new_num_titles)

def test():
	""" unittest launching : 
		* TestCases from unittest module, 
		* docstring tests
	"""
	import doctest
	doctest.testmod()
	unittest.main(argv=[sys.argv[0]])

def main():
	""" Main function"""
	opt_parse = create_options()
	opts = opt_parse.parse_args()
	if opts.debug:
		logging.basicConfig(level = logging.DEBUG)
	if opts.test:
		test()
	else:
		# paramètres par defaut : "Projet:Informatique", False
		projects_maintenance(PROJETS, opts)


####
####
#### Tests samples

SAMPLE_TEXT = """
==Plop==
Bidou


== L'article Jean-Daniel Fekete est proposé à la suppression ==

{| align="center" title="{{((}}subst:avertissement suppression page{{!}}page{{))}}" border="0" cellpadding="4" cellspacing="4" style="border-style:none; background-color:#FFFFFF;"
|  | [[Image:Icono consulta borrar.png|64px|Page proposée à la suppression]]
|  |Bonjour,
|
|  L’article « '''{{Lien à supprimer|1=Jean-Daniel Fekete}}''' » est proposé à la suppression ({{cf.}} [[Wikipédia:Pages à supprimer]]). Après avoir pris connaissance des [[Wikipédia:Critères d'admissibilité des articles|critères généraux d’admissibilité des articles]] et des [[:Catégorie:Wikipédia:Admissibilité des articles|critères spécifiques]], vous pourrez [[Aide:Arguments à éviter lors d'une procédure de suppression|donner votre avis]] sur la page de discussion '''[[Discussion:Jean-Daniel Fekete/Suppression]]'''.
|
|  Le meilleur moyen d’obtenir un consensus pour la conservation de l’article est de fournir des [[Wikipédia:Citez vos sources|sources secondaires fiables et indépendantes]]. Si vous ne pouvez trouver de telles sources, c’est que l’article n’est probablement pas admissible. N’oubliez pas que les [[Wikipédia:Principes fondateurs|principes fondateurs]] de Wikipédia ne garantissent aucun droit à avoir un article sur Wikipédia.
|  |}

[[Utilisateur:Linan|Linan]] ([[Discussion utilisateur:Linan|d]]) 3 janvier 2013 à 13:26 (CET)

==Bidou==
Yeah
"""

FULL_TEST = """{{/En-tête}}
== pose de bandeau de portails ==

Bonjour. Dans le cadre de l'amélioration du [[Portail:Logiciel]], j'ai modifié les bandeaux de portail d'un certain nombre d'articles en rapport avec des logiciels (paquets, fonctionalités, notions du marché du logiciel,personnalités, entreprises, etc). J'ai appliqué la [[WP:BDP|règle de proximité]] qui veut que seul le portail le plus proche du sujet soit mentionné: logiciel libre, Internet, programmation, logiciel, etc. Notamment en application de la règle de proximité, le bandeau ''portail de l'informatique'' a été retiré d'articles déjà attachés à des sous-portails (logiciel libre, Internet, ...) et dont le sujet n'a pas une importance historique en informatique (logiciels, personnalités). Des contributeurs apparemment ne sont pas du même avis et recouvrent sans avertissement mes modifications. Parmi les articles concernés, il y a :
# [[Ulrich Drepper]] - personnalité dans le monde du libre, pas notoire dans l'histoire de l'informatique. 
# [[Eclipse (logiciel)]] - environnement de développement notoire en dehors des habitués du libre, appliqué l'[[WP:BDP|exception de pertinence]] et placé le bandeau ''portail du logiciel''.
# [[Open Source]], type de licence, pertinent pour le portail du logiciel, appliqué l'[[WP:BDP|exception de pertinence]].
# [[Red Hat]], la société, pas d'importance historique en informatique. importance pour l'économie du secteur informatique uniquement (logiciel en particulier).
# [[Messagerie instantanée]] - type de logiciel. Pas une notion technique d'informatique.
--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 3 septembre 2012 à 11:29 (CEST)
: J’avoue que j’ai du mal à me passionner pour le sujet du périmètre des portails, que je considère comme un sujet loin d’être prioritaire. Mais je suis pas sur que le précédent lien ait été présenté ici (ce qui me semble essentiel vu que tous les portails s’y rattachent : [[Portail:Logiciel/Évaluation]] - peut être qu’il aurait fallu faire cette discussion avant les modifs ) Après sur l’importance respective de tel ou tel dans tel domaine, ça m’a l’air tellement subjectif et difficilement sourcable que j’ai pas trop envie de m’impliquer [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 3 septembre 2012 à 12:29 (CEST)

:J'ai juste rajouté le portail « programmation informatique » à l'article « Ulrich Drepper » ; sinon ça me va. Amicalement — [[Utilisateur:Arkanosis|Arkanosis]] <sup>[[Discussion Utilisateur:Arkanosis|✉]]</sup> 4 septembre 2012 à 02:52 (CEST)

:C'est pas à voir au cas par cas avec tes contradicteurs, Silex6, plutôt que ici ? Sinon, tes modifications informatique|logiciel libre => logiciel libre sont une bonne application du principe de proximité des portails, rien à redire. Dans le cas de Red Hat, je comprends sans doute mal la question, mais il me semble que cette société a une grande importance historique. --[[Utilisateur:MathsPoetry|MathsPoetry]] ([[Discussion utilisateur:MathsPoetry|d]]) 4 septembre 2012 à 07:25 (CEST)
::Ma remarque est que je ne pense pas que RedHat a révolutionné la technologie informatique, tout au plus la société a été un moteur notable de l'économie du logiciel.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 4 septembre 2012 à 14:45 (CEST)
::: Hum. Elle est quand même entre autres à l'origine du système de paquetages RPM, utilisé par la moitié des distributions Linux. En faisant le choix de GNOME contre KDE, elle a causé beaucoup de tort à ce dernier. Etc. --[[Utilisateur:MathsPoetry|MathsPoetry]] ([[Discussion utilisateur:MathsPoetry|d]]) 4 septembre 2012 à 15:21 (CEST)

== [[Extended file system]], [[ext2]], [[ext3]], [[ext4]] ==
<small>recopié depuis [[Wikipédia:Pages à fusionner]]</small>

Le code source des trois versions est certainement très différent, mais ce n'est pas le sujet des articles. Quelles sont les différences fonctionnelles, les améliorations apportées, et les liens historiques entre ces 4 produits ? En l'état c'est difficile à voir parce que chaque article couvre des sujets différents: l'article ext2 parle de ext3, un autre article parle des limitations techniques, et le dernier est juste un titre. Si je reprends l'exemple de XP, Vista et W7, chaque produit a une charte graphique différente et des fonctionnalités différentes. De plus il y a un article chapeau [[Microsoft Windows]] qui retrace l'histoire de cette famille de produits. Etant donné que les sources ne manquent pas, je n'ai rien contre le maintien de 4 articles. Est-ce qu'un article chapeau qui retrace l'histoire de cette famille de systèmes de fichiers est envisageable pour compléter les 4 articles détaillés ?.

PS, soit dit en passant, les différences fonctionnelles entre des systèmes de fichiers soit généralement plus subtiles que celles entre des interfaces utilisateur.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 4 septembre 2012 à 10:02 (CEST)
: Non, les différences fonctionnelles sont énormes, c'est plus que trois "versions" d'un même produit. Je suis d'accord qu'en l'état actuel des articles, c'est désastreux, et que le volume à cette date justifierait la fusion. Mais je pense que les PàF sont comme les PàS, on agit plus en fonction du ''potentiel'' des articles que de leur état actuel.
: C'est idiot, j'ai écrit un article très détaillé sur le sujet dans un ouvrage technique, mais j'en ai cédé les droits lorsqu'il a été publié, je ne peux donc pas le reprendre tel quel. Pour remettre ces quatre articles d'équerre il faudrait que je réécrive complètement ma propre prose, ce qui est complètement stupide et surtout, je n'y aurais aucun plaisir.
: Pourquoi les différences fonctionnelles seraient-elles plus frappantes dans une interface utilisateur ? J'ai un peu de mal à saisir, un logiciel est plus que la somme de ses menus. --[[Utilisateur:MathsPoetry|MathsPoetry]] ([[Discussion utilisateur:MathsPoetry|d]]) 4 septembre 2012 à 10:47 (CEST)
::Chaque système de fichier a sa propre structure physique, dans le cas de ext2, ext3 et ext4 la structure a changé, quel est la nature de ces changements ? quels sont les apports de ces changements ? ce sont des choses techniques plus difficiles à expliquer que le fait que la charte graphique a été changée pour être plus attrayante et à la mode. Je constate qu'il existe un article [[comparaison des systèmes de fichiers]] mais celui-ci se limite à citer les noms, les auteurs et les années de parution des systèmes de fichiers.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 4 septembre 2012 à 11:57 (CEST)
::: Ces questions sont légitimes et les articles devront y répondre (en bref : ext3 est un SDF journalisé, pas ext2 ; ext4 alloue plusieurs blocs de façon indivisible, contrairement à ses prédécesseurs). Le fait qu'ils ne le fassent pas correctement actuellement ne justifie pas à mon avis la fusion. --[[Utilisateur:MathsPoetry|MathsPoetry]] ([[Discussion utilisateur:MathsPoetry|d]]) 4 septembre 2012 à 12:27 (CEST)

== L'article Acquéreur est proposé à la suppression ==

{| align="center" title="{{((}}subst:avertissement suppression page{{!}}page{{))}}" border="0" cellpadding="4" cellspacing="4" style="border-style:none; background-color:#FFFFFF;"
| [[Image:Icono consulta borrar.png|64px|Page proposée à la suppression]]
|Bonjour,

L’article « '''{{Lien à supprimer|Acquéreur}}''' » est proposé à la suppression ({{cf.}} [[Wikipédia:Pages à supprimer]]). Après avoir pris connaissance des [[Wikipédia:Critères d'admissibilité des articles|critères généraux d’admissibilité des articles]] et des [[:Catégorie:Wikipédia:Admissibilité des articles|critères spécifiques]], vous pourrez [[Aide:Arguments à éviter lors d'une procédure de suppression|donner votre avis]] sur la page de discussion '''[[Discussion:Acquéreur/Suppression]]'''.

Le meilleur moyen d’obtenir un consensus pour la conservation de l’article est de fournir des [[Wikipédia:Citez vos sources|sources secondaires fiables et indépendantes]]. Si vous ne pouvez trouver de telles sources, c’est que l’article n’est probablement pas admissible. N’oubliez pas que les [[Wikipédia:Principes fondateurs|principes fondateurs]] de Wikipédia ne garantissent aucun droit à avoir un article sur Wikipédia.
|}

[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 6 septembre 2012 à 23:15 (CEST)

== Encore des propositions de fusion ==

{| align="center" title="<nowiki>{{subst:Avertissement fusion|page 1|page 2|page 3|page 4|page 5|page 6|signature}}</nowiki>" border="0" cellpadding="4" cellspacing="4" style="border: 2px solid #000000; background-color: #ffffff"
|-
| [[Image:Emblem-important.svg|45px|alt=|link=]]
| style="text-align:center; font-size:larger; font-weight:bold;" | [[Ghostscript]] et [[GNU Ghostscript]] sont proposés à la fusion
|-
| [[Image:Merge-arrows.svg|45px|alt=|link=]]
| La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#Ghostscript et GNU Ghostscript]].<br /><!--
--><small>La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].<br /><!--
-->[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 7 septembre 2012 à 12:56 (CEST)</small>
|}
{| align="center" title="<nowiki>{{subst:Avertissement fusion|page 1|page 2|page 3|page 4|page 5|page 6|signature}}</nowiki>" border="0" cellpadding="4" cellspacing="4" style="border: 2px solid #000000; background-color: #ffffff"
|-
| [[Image:Emblem-important.svg|45px|alt=|link=]]
| style="text-align:center; font-size:larger; font-weight:bold;" | [[sudo]], [[gksu]] et [[kdesu]] sont proposés à la fusion
|-
| [[Image:Merge-arrows.svg|45px|alt=|link=]]
| La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#sudo et gksu et kdesu]].<br /><!--
--><small>La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].<br /><!--
-->[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 7 septembre 2012 à 12:56 (CEST)</small>
|}
{| align="center" title="<nowiki>{{subst:Avertissement fusion|page 1|page 2|page 3|page 4|page 5|page 6|signature}}</nowiki>" border="0" cellpadding="4" cellspacing="4" style="border: 2px solid #000000; background-color: #ffffff"
|-
| [[Image:Emblem-important.svg|45px|alt=|link=]]
| style="text-align:center; font-size:larger; font-weight:bold;" | [[GmailFS]] et [[Gmail Drive]] sont proposés à la fusion
|-
| [[Image:Merge-arrows.svg|45px|alt=|link=]]
| La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#GmailFS et Gmail Drive]].<br /><!--
--><small>La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].<br /><!--
-->[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 7 septembre 2012 à 12:56 (CEST)</small>
|}
{| align="center" title="<nowiki>{{subst:Avertissement fusion|page 1|page 2|page 3|page 4|page 5|page 6|signature}}</nowiki>" border="0" cellpadding="4" cellspacing="4" style="border: 2px solid #000000; background-color: #ffffff"
|-
| [[Image:Emblem-important.svg|45px|alt=|link=]]
| style="text-align:center; font-size:larger; font-weight:bold;" | [[GNU Compiler Collection]], [[GNAT]], [[GNU D Compiler]] et [[GCJ]] sont proposés à la fusion
|-
| [[Image:Merge-arrows.svg|45px|alt=|link=]]
| La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#GNU Compiler Collection et GNAT et GNU D Compiler et GCJ]].<br /><!--
--><small>La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].<br /><!--
-->[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 7 septembre 2012 à 12:56 (CEST)</small>
|}
: J’ai pas eu de réponse pour ma proposition de faire un modèle d’annonce de suppression discret, mais je réitère quand même pour faire un modèle d’annonce de proposition de fusion discret {{clin}}. [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 7 septembre 2012 à 13:14 (CEST)
:: Bien vu. Je pense aussi qu'il n'est pas nécessaire de laisser traîner des annonces de fusion ou de suppression une fois que les discussions sont closes. Je constate toutefois que les dernières tentatives de supprimer des annonces obsolètes ont été révoquées: [http://fr.wikipedia.org/w/index.php?title=Discussion_Projet:Informatique&diff=82761336&oldid=82761326].--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 7 septembre 2012 à 13:26 (CEST)

== article à revoir - [[Gnus]] ==

Bonjour. est-ce que quelqu'un peut regarder l'article [[Gnus]] qui accumule les bandeaux: controverse de neutralité, guide pratique, et absence de sources secondaires.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 11 septembre 2012 à 10:41 (CEST)
== article à revoir [[Google Chrome OS]] ==
Bonjour. cet article comporte un bandeau ''événement à venir'' placé il y a plus de deux ans. est-ce toujours d'actualité ?--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 11 septembre 2012 à 12:58 (CEST)

== Mamoune Lahlou ==

Bonjour {{sourire}}

Je sollicite l'avis du projet quand à l’admissibilité de ce pirate informatique qui semble très connu dans le monde du Warez. 

Son brouillon est visible [[Utilisateur:Warezscene/Brouillon|ici]], et d'autres éléments de références ont été apportés [[Utilisateur:Warezscene/Brouillon#Mamoune Lahlou|ici]].

De mon point de vue, il semble admissible. Mais les sources sont insuffisantes. 

Cordialement. --[[Utilisateur:Superjuju10|Superjuju10]] <sup>&#91;[[Discussion utilisateur:Superjuju10|'''''Contacter la Aubline''''']]&#93;</sup>, le 12 septembre 2012 à 16:45 (CEST)
:Excellente question ! Une recherche google confirme que le nom de Mamoune Lahlou est connu sur les réseaux sociaux (notamment linked in, Facebook et Twitter) est-ce toujours la même personne, ou y a-il des homonymes ? je n'ai pas vérifié. Maintenant si je regarde le contenu du brouillon, je constate des sources de fiabilité douteuse (des blogs), et des pages de sites de warez qui parlent de Mr Hero. par contre je n'ai pas trouvé son vrai nom dans les sources et je n'ai pas trouvé de page centrée sur le sujet de ''la personne'' de Mr Hero. En absence de telles informations, ce brouillon est inédit...--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 12 septembre 2012 à 17:33 (CEST)
::PS: voila une source intéressante: un inteview à MrHero, administrateur de oleoo.com, [http://www.undernews.fr/interviews/warez-interview-mrhero-administrateur-doleoo.html] Dans cet article paru en décembre 2010, l'administrateur (''MrHero'', marocain, dont le vrai nom n'est pas mentionné) dit avoir 26 ans. Or le brouillon lui donne 21 ans.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 12 septembre 2012 à 19:05 (CEST)
:::Bonjour la compagnie
:::comme je l'ai déjà précisé, les interviews sont bidon : peut être que ce dernier a menti pour ne pas avoir affaire avec les autorités
:::en ce qui concerne l'identité de la personne c'est simple : sur son compte facebook il y a 2 adresse emails qui prouvent qu'il s'agit bien de GRIZZLY admin@projetcw.org et admin@warez-bb.org même chose pour son compte sur linkedin je pense 
:::c'était depuis son profil sur facebook que j'ai récupéré ses infos personnelles : nationalité,age, etc...
:::Soyez logiques un peu ! ce n'est pas un inventeur ni un écrivain, c'est un pirate informatique, donc il est normal que ne puissions pas trouver beaucoup de références à son sujet. et puis il est vachement connu sur internet, je ne cherche pas a prouver l'improuvable puisque notre gars a réellement existé et existe encore  {{sourire}} <br>--[[Utilisateur:warezscene|warezscene]] ([[Discussion utilisateur:warezscene|d]]) 12 septembre 2012 à 19:43 (CEST)
::::Les pirates informatiques ne sont pas dispensés de sources {{clin}}. Et Wikipédia fonctionne selon ce principe de connaissances vérifiables et neutres. 
::::Le plus simple Warezscene est de continuer votre brouillon en prenant soin de bien [[Aide:Présentez vos sources|présentez vos sources]]. Cordialement. --[[Utilisateur:Superjuju10|Superjuju10]] <sup>&#91;[[Discussion utilisateur:Superjuju10|'''''Contacter la Aubline''''']]&#93;</sup>, le 12 septembre 2012 à 20:50 (CEST)

::::@warezscene: je cite {{citation|La vérifiabilité n'est pas la vérité : nos opinions personnelles sur la nature vraie ou fausse des informations n'ont aucune importance dans Wikipédia}} c'est une [[WP:V|règle de Wikipédia]]. Une information est digne de figurer dans Wikipédia du moment que celle-ci peut être tirée d'une source de qualité (webzine, article de presse, ouvrage écrit, ...) En l'occurence l'interview l'est. Si il s'avère que l'affirmation comme quoi cet interview est bidon peut être tirée d'une source, alors rien n'empêche de la mettre dans l'article de Wikipédia. Pour ce qui est du manque d'information, c'est logique en effet, vu qu'un pirate (comme n'importe quel bandit) agit dans l'ombre. Dans ces conditions un article à son sujet se limitera à ce qui été écrit à son sujet: très peu de choses - un interview, un rapport de police, un article de presse. Je rajouterais que les articles qui sont le fruit de [[WP:TI|recherches personnelles]] sur un sujet sont interdits dans Wikipédia.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 12 septembre 2012 à 21:52 (CEST)


@silex: je suis complètement d'accord avec vous en ce qui concerne les opinions personnelles, mais il faut que vous sachiez qu'il s'agit pas de mon opinion perso personnelle puisque les profils de la personne prouvent bel et bien que c'est lui le fameux GRIZZLY et qu'il a 21 ans actuellement, de nationalité marocaine, etc ... <br>
autre source ou le nom de mamoune Lahlou est cité : 
[https://encyclopediadramatica.se/Warez-bb#Origins ici] --[[Utilisateur:warezscene|warezscene]]
:Celle-ci me paraît moyennement fiable :p [[Utilisateur:Zandr4|Zandr4]]<sup><small>&#91;[[Discussion Utilisateur:Zandr4|Kupopo ?]]&#93;</small></sup> 13 septembre 2012 à 08:30 (CEST)
::@warezscene: Merci de signer les messages. Une page Facebook est à mon avis une source d'information fiable concernant une personne du moment que les informations source ont été écrites par la personne elle-même. Dans mon message précédent, je parlait de l'affirmation que l'interview est bidon: est-ce que cette information provient d'une source officielle ? ou s'agit-il de oui-dires écrits sur un blog ? Et puis concernant cette nouvelle source: un wiki écrit par des bénévoles, qui ressemble étrangement à Wikipédia, c'est pas vraiment le genre de source qui permet d'améliorer la fiabilité du contenu de Wikipédia.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 13 septembre 2012 à 09:29 (CEST)

:@Silex : j'ai relu l'interview de MrHero sur undernews, tout est juste sauf la date de naissance, c'est une magouille pour ne pas pas se faire gauler, sinon je demande l'aide des autres afin de rédiger l'article final puisque nous avons suffisamment d'informations sur notre gars {{sourire}} --[[Utilisateur:warezscene|warezscene]]
::Qu'est-ce qui permet d'affirmer que {{citation|c'est une magouille pour ne pas pas se faire gauler}}, y-a-il un démenti officiel ? l'âge n'est pas le même que sur le profil Facebook ? en l'absence de démenti, tout ce qui peut être mentionné sur l'article Wikipédia est que son âge diffère selon les sources.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 13 septembre 2012 à 16:36 (CEST)
:
:: Donc tu peux personnellement attester de l’exactitude des informations. Mais es-tu fiable ou même authentifiable ? Parce qu’en temps que simple contributeur, on est en plein dans le travail inédit et en admettant l’interview comme source, le seul truc qu’on peut sourcer c’est qu’il tenait un site de téléchargement, et c’est tout. Pour le reste c’est assez obscur et spécialisé, voire soupsçonnable de conflit d'intérêt dans des guerres entre hackers, donc la fiabilité est quand même pour le moins discutable. Le flou entretenu par la nature pas forcément très légale avec pignon sur rue des activités, et dans lequel on aime bien se faire mousser, n’arrange rien pour la fiabilité des informations ... en plus c’est pas trop le travail des wikipediens de vérifier que bidule est bien machin ... on est quand même loin de quelqu'un qui a été biographié comme [[Kevin Mitnick]].  [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 13 septembre 2012 à 16:52 (CEST)
:::Totalement d'accord avec vous !! bon pourriez-vous m'aider à compléter mon brouillon svp ? --[[Utilisateur:warezscene|warezscene]]

:Pour ceux qui n'auraient pas remarqué, la page a été ajoutée à l'espace encyclopédique ici [[MrHero]].--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 14 septembre 2012 à 11:27 (CEST)
:: C’est comment dire … prématuré ? L’admissibilité n’est pas démontrée, et l’auteur n’a pas du tout tenu compte des remarques et s’est contenté de supprimer les bandeaux sans rien changer d’autres … La démarche du brouillon était appréciable, par contre si c’est pour n’en rien faire d’intéressant, c’était pas la peine. [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 14 septembre 2012 à 11:47 (CEST)
::: oulaa !! je l'ai pas encore terminé voyons !! et puis a la place de me supprimer la page contentez-vous de m'aider. je suis un novice ici [[Utilisateur:warezscene|warezscene]]
:::: Le principal souci c’est l’admissibilité et la possibilité de sourcer de manière fiable ou pas les différentes affirmations de l’article. Ce qui est problématique de part le sujet même de l’article. Je suis tout disposé à aider, mais j’ai peur que sans sources fiables il ne soit pas possibles de faire grand chose sur wikipedia, selon les principes fondateurs du projet. Faudrait d’abord (faire) publier une biographie par exemple {{clin}}. ''Les confessions d’un pirate'', mais ça doit être probablement déja pris comme titre /o\. [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 14 septembre 2012 à 14:10 (CEST)

::::@warezscene: Je constate que quelqu'un a supprimé l'article de l'encyclopédie, (et je n'y suis pour rien). Je vous conseille de commencer par rechercher des sources (pages web, rapports écrits, vidéos, ...) au sujet de cette personne, et d'en extraire toutes les informations pertinentes, puis de les mettre dans une page de brouillon, affin de voir si il y a de quoi remplir une page, ou pour le moins un paragraphe.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 14 septembre 2012 à 14:22 (CEST)
:::::@Silex6: c'est déjà fait mais quelqu'un a supprimé la page .... mon brouillon est visible [[Utilisateur:Warezscene/Brouillon|ici]]     --  [[Utilisateur:warezscene|warezscene]]
:::::: pour les références :

* {{en}} https://encyclopediadramatica.se/Warez-bb (c'est ici ou son véritable nom est révélé ainsi que dans les réseaux sociaux)
* {{fr}} http://www.undernews.fr/warez-telechargement/le-fondateur-et-administrateur-de-warez-bb-se-retire-definitivement.html  (c'est ici ou il est annoncé qu'il a quitté le warez )
* {{en}} http://oleoobiz.wordpress.com/. ( pas mal d'articles sur MrHero)
* {{fr}} http://www.zataz.com/news/17222/Oleoo_-warezn-arrestation_-police.html. ( la fermeture d'oleoo ex-zone-warez )
* {{fr}} http://www.zataz.com/news/13438/ca-balance-dans-le-warez.html (divers informations sur le détournement d'argent etc ... )
* {{fr}}http://www.facebook.com/mamounelahlou (son compte sur facebook)
votre aide serait la bienvenue; et merci d’éviter de supprimer quoi que ce soit
:Voila ce qu'on peut extraire de la première source: Le site Warez-BB a démarré en 2005. Il a été créé par ''Grizzly'', et fusionné avec ''ProjectW'', également créé par Grizzly. Le vrai nom de Grizzly est Mamoune Lahlou. Warez-BB, maintenu par un groupe d'amis, a été plus tard vendu à ''Coolquer''. Le site permet le partage de fichiers avec [[RapidShare]]. Il contient des jeux, des applications, des films, de la musique, des eBooks et des OS. Il y a 3.5 millions d'utilisateurs inscrits. Je rajouterais que le contenu de cette source est à prendre avec des pincettes, étant donné le ton plus satirique que pédagogique, témoin: cette phrase {{citation| Legend has it that posting on Warez-BB systematically decreases your penis size}}.
:Concernant la deuxième source, le ton est nettement plus neutre. Les informations intéressantes sont: Grizzly, fondateur de Warez-BB, de ProjectW et BayW (trois sites warez de renommée mondiale) se retire. Dans un court message laissé sur les forums, il déclare {{citation|on est maintenant en 2012, les temps ont changé, Internet me dégoute, je n'ai pas envie de finir ma vie en prison. Je cède ma place à 3ch0 au 1er avril 2012}}.
:La troisième source parle de MrHero, son associé Sagat et de Oleoo, et dit {{citation|notre Amine tente le tout pour le tout}}. Amine, est-ce [[Amine (prénom)|son prénom]] ? En tout cas les noms de MrHero et Sagat ne figurent pas dans les deux premières sources, et les noms de Grizzly, ProjectW, Warez-BB, ou Mamoune Lahlou ne figurent pas dans la troisième. est-ce la même personne ? A part ça, l'article dénonce une arnaque: des usagers payent pour obtenir un avantage - la réponse dans les 24 heures. Selon la source, l'administrateur s'absente parfois durant un mois entier sans avertissement. Phénomène déja rencontré sur le site zone-warez, selon l'auteur. Je rajouterais que ce texte date de 2008, et ne reflète pas forcément la situation actuelle.
:La quatrième source relate la fermeture de Oleoo, et est datée de juin 2008. D'après la source le site est hébergé aux Pays-Bas, compt 200'000 membres, et son administrateur est MrHero, du Maroc. La source cite le nom de Sagat, et les actions de la police française. Tout comme la source précédente, pas de mention de Grizzly ou Mamoune Lahlou.
--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 16 septembre 2012 à 08:53 (CEST)
== Propositions fusion ==
{| align="center" title="<nowiki>{{subst:Avertissement fusion|page 1|page 2|page 3|page 4|page 5|page 6|signature}}</nowiki>" border="0" cellpadding="4" cellspacing="4" style="border: 2px solid #000000; background-color: #ffffff"
|-
| [[Image:Emblem-important.svg|45px|alt=|link=]]
| style="text-align:center; font-size:larger; font-weight:bold;" | [[Multimedia Fusion]], [[Multimedia Fusion 2]] et [[Multimedia Fusion 2 Developer]] sont proposés à la fusion
|-
| [[Image:Merge-arrows.svg|45px|alt=|link=]]
| La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#Multimedia Fusion et Multimedia Fusion 2 et Multimedia Fusion 2 Developer]].<br /><!--
--><small>La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].<br /><!--
-->[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 27 septembre 2012 à 18:50 (CEST)</small>
|}
{| align="center" title="<nowiki>{{subst:Avertissement fusion|page 1|page 2|page 3|page 4|page 5|page 6|signature}}</nowiki>" border="0" cellpadding="4" cellspacing="4" style="border: 2px solid #000000; background-color: #ffffff"
|-
| [[Image:Emblem-important.svg|45px|alt=|link=]]
| style="text-align:center; font-size:larger; font-weight:bold;" | [[iLife]] et [[iLife 06]] sont proposés à la fusion
|-
| [[Image:Merge-arrows.svg|45px|alt=|link=]]
| La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#iLife et iLife 06]].<br /><!--
--><small>La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].<br /><!--
-->[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 27 septembre 2012 à 18:50 (CEST)</small>
|}
{| align="center" title="<nowiki>{{subst:Avertissement fusion|page 1|page 2|page 3|page 4|page 5|page 6|signature}}</nowiki>" border="0" cellpadding="4" cellspacing="4" style="border: 2px solid #000000; background-color: #ffffff"
|-
| [[Image:Emblem-important.svg|45px|alt=|link=]]
| style="text-align:center; font-size:larger; font-weight:bold;" | [[The Games Factory 2]] et [[The Games Factory]] sont proposés à la fusion
|-
| [[Image:Merge-arrows.svg|45px|alt=|link=]]
| La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#The Games Factory 2 et The Games Factory]].<br /><!--
--><small>La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].<br /><!--
-->[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 28 septembre 2012 à 10:39 (CEST)</small>
|}
{| align="center" title="<nowiki>{{subst:Avertissement fusion|page 1|page 2|page 3|page 4|page 5|page 6|signature}}</nowiki>" border="0" cellpadding="4" cellspacing="4" style="border: 2px solid #000000; background-color: #ffffff"
|-
| [[Image:Emblem-important.svg|45px|alt=|link=]]
| style="text-align:center; font-size:larger; font-weight:bold;" | [[Pascal (langage)]] et [[Pastel (langage de programmation)]] sont proposés à la fusion
|-
| [[Image:Merge-arrows.svg|45px|alt=|link=]]
| La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#Pascal (langage) et Pastel (langage de programmation)]].<br /><!--
--><small>La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].<br /><!--
-->[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 28 septembre 2012 à 14:53 (CEST)</small>
|}
{| align="center" title="<nowiki>{{subst:Avertissement fusion|page 1|page 2|page 3|page 4|page 5|page 6|signature}}</nowiki>" border="0" cellpadding="4" cellspacing="4" style="border: 2px solid #000000; background-color: #ffffff"
|-
| [[Image:Emblem-important.svg|45px|alt=|link=]]
| style="text-align:center; font-size:larger; font-weight:bold;" | [[compilateur Java]] et [[Java (langage)]] sont proposés à la fusion
|-
| [[Image:Merge-arrows.svg|45px|alt=|link=]]
| La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#compilateur Java et Java (langage)]].<br /><!--
--><small>La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].<br /><!--
-->[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 28 septembre 2012 à 14:54 (CEST)</small>
|}

== [[Juzzle]] ==

Bonjour, est-ce quelqu'un peut regarder l'article [[Juzzle]] qui accumule les bandeaux: ébauche, à sourcer, à wikifier et orphelin.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 27 septembre 2012 à 18:17 (CEST)

== L'article Kleioscope est proposé à la suppression ==

{| align="center" title="{{((}}subst:avertissement suppression page{{!}}page{{))}}" border="0" cellpadding="4" cellspacing="4" style="border-style:none; background-color:#FFFFFF;"
| [[Image:Icono consulta borrar.png|64px|Page proposée à la suppression]]
|Bonjour,

L’article « '''{{Lien à supprimer|Kleioscope}}''' » est proposé à la suppression ({{cf.}} [[Wikipédia:Pages à supprimer]]). Après avoir pris connaissance des [[Wikipédia:Critères d'admissibilité des articles|critères généraux d’admissibilité des articles]] et des [[:Catégorie:Wikipédia:Admissibilité des articles|critères spécifiques]], vous pourrez [[Aide:Arguments à éviter lors d'une procédure de suppression|donner votre avis]] sur la page de discussion '''[[Discussion:Kleioscope/Suppression]]'''.

Le meilleur moyen d’obtenir un consensus pour la conservation de l’article est de fournir des [[Wikipédia:Citez vos sources|sources secondaires fiables et indépendantes]]. Si vous ne pouvez trouver de telles sources, c’est que l’article n’est probablement pas admissible. N’oubliez pas que les [[Wikipédia:Principes fondateurs|principes fondateurs]] de Wikipédia ne garantissent aucun droit à avoir un article sur Wikipédia.
|}

28 septembre 2012 à 13:16 (CEST)[[Utilisateur:Patrick Rogel|Patrick Rogel]] ([[Discussion utilisateur:Patrick Rogel|d]])

== Rappel des annonces ==

Je reviens à la charge, je vois qu’il existe carrément une sous page du projet dédiées aux annonces qui ont tendance à innonder la PDD du projet ... j’ai rajouté un cadre sur la PDD pour le rappeler.
J’aimerai vos avis pour savoir pourquoi il n’est pas actuellement utilisé. Quelques hypothèses
* Manque de visibilité ? vous aviez oublié son existence / ne saviez pas qu’il existe.
* Il n’y a personne pour le maintenir.
* La page du projet est trop fouillie, ne mets pas en valeur les informations et est à l’abandon.
* Les instructions pour les procédures de propositions ne mentionnent pas ces espaces spécialisé dans les projets et indiquent de laisser un message sur la PDD.
Ça ennuie quelqu’un si on déplace les annonces qui sont actuellement sur la PDD du projet dans cette sous page ?
[[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 1 octobre 2012 à 13:23 (CEST)
:: J'ai ouvert une discussion sur le bistro, concernant les annonces [[Wikipédia:Le Bistro/29 septembre 2012#L'utilité de conserver les bandeaux dans les pages de discussion]]. Certains espaces de discussion ont une page dédiée aux annonces échues.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 1 octobre 2012 à 18:17 (CEST)

== [[AgoraLib]] ==

Bonjour. Est-ce que quelqu'un peut regarder l'article [[AgoraLib]], j'ai un doute sur l'admissibilité du sujet, et le caractère encyclopédique du contenu (très détaillé, peu synthétique et pas sourcé).--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 2 octobre 2012 à 12:13 (CEST)

== classification des logiciels ==

Bonjour, j'ai comparé la manière de classifier les logiciels dans les publications, et celle de Wikipédia.

Dans les publications (exemple: comparatifs de logiciels), les logiciels sont typiquement classifiés en fonction de la fonctionnalité [http://www.xbitlabs.com/news/graphics/display/20100721214110_Computer_Graphics_Market_Will_Exceed_150_Billion_in_2013_Jon_Peddie_Research.html] [http://lcolumbus.files.wordpress.com/2011/06/saas-forecast-from-h1-2011-update1.jpg], de la plateforme et du prix [http://www.intomobile.com/2010/02/24/research-android-market-hosts-highest-proportion-of-free-apps/]. La classification ''libre / propriétaire'' se retrouve principalement dans les sites militants du libre, et est souvent complètement ignorée des autres publications [http://www.lilux.lu/].

Si je regarde la manière dont les logiciels sont classifiés dans la Wikipédia francophone, je constate une omniprésence de la classification ''libre / propriétaire''. Non seulement la caractéristique libre / propriétaire est citée d'entrée de jeu dans les premières lignes de l'article (sujet qui a déja été débattu ici), elle se retrouve également comme critère de classification dans les palettes [[Modèle:Palette Systèmes de gestion de base de données|exemple ici]], les [[Liste des logiciels SIG|listes]], et la section ''liens internes'' [http://fr.wikipedia.org/w/index.php?title=OpenFOAM&oldid=83230434].--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 2 octobre 2012 à 13:37 (CEST)
: On peut prendre d’autres exemples, par exemple un tout petit site [http://www.01net.com/telecharger/linux/] ou le type de licence est un des critère primaire de filtrage proposé sur la recherche. Ton constat me parait discutable et pas démontré du tout, un simple point de vue différent en somme. Sinon tu veux en venir ou, concrêtement ? [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 2 octobre 2012 à 14:08 (CEST)
:: Le but n'est pas de relancer le troll concernant la mention ''libre'' dans les articles, mais force est de constater que la classification des logiciels dans la Wikipédia reflète bien souvent celle d'un arbre avec un tronc coupé en deux: 1 - libre,  2 - propriétaire, un découpage fréquent dans les sites militants, et rare en dehors. L'exemple que tu cite est intéressant, il s'agit d'un moteur de recherche multi-critères, et le premier critère qui est proposé (qui reflète le tronc), est celui de la plateforme. La licence n'est proposée qu'en troisième position, et il n'y a pas deux, mais cinq choix différents.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 2 octobre 2012 à 14:45 (CEST)
::: La classification est probablement à discuter au cas par cas en fonction des circonstances … mais le critère libre ou pas à une certaine importance assez facilement sourcable de nos jours, un exemple récent : [http://www.silicon.fr/edito-ayrault-oracle-salesforce-79057.html la circulaire Hérault sur l’utilisation du logiciel libre dans l’administration]. Des sociétés comme google ou microsoft, quand elles éditent des logiciels libres, communiquent largement sur cette caractéristique. Ce critère a une importance indéniable dans le monde du logiciel aujourd’hui. J’en veux pour preuve la requête <code>"logiciel libre" OR "open source"</code> sur google actualité, qui est riche, il y a des sans exagérer des centaines d’articles qui mentionnent le sujet rien que sur le mois dernier ... et pas sur des sites libristes en l’occurence. Un autre exemple, la classification effectuée par le Journal du net sur ses "réseaux sociax d’entreprise" : http://www.journaldunet.com/solutions/reseau-social-d-entreprise/. On y retrouve une partie "réseaux sociaux opensource", sur un site absolument pas dédié à l’opensource ou au libre, je ne pense pas qu’il soit très difficile de trouver d’autres exemples. Dans l’actualité toujours, regarde les intervenants à cette conférence adossée à l’[[Open World Forum]] - une conférence pas toute petite dédiée au sujet -[http://www.silicon.fr/open-cio-summit-gouvernance-experiences-disic-et-cigref-78976.html] Auchan, Lagardère, Safran, qui visiblement ne sont pas insensibles à ce critère. On a largement dépassé le stade des critères de notoriété pour rentrer dans le stade du phénomène de société là. Largement de quoi pour wikipedia acter de l’importance du critère (au cas par cas toujours {{clin}}). Encore un exemple : jimmy Wales qui vient expliquer ce que sont les logiciels libres au Meddef [http://www.zdnet.fr/blogs/l-esprit-libre/logiciel-libre-1-business-open-world-forum-brevets-degeneres-wikipedia-explique-au-medef-jaspersoft-et-big-data-39783065.htm]. Le medef pouvant difficilement être taxé d’endroit grouillant de libristes ou même d'informaticiens …  [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 2 octobre 2012 à 15:48 (CEST)
:::: ''libre'' ou ''open source'' sont des catégories de logiciels notoires, pour lesquelles il existe des manifestations, des sites dédiés, des groupes d'utilisateur et des sympathisants. Je constate que cette catégorie est peu mise en avant, voire totalement ignorée dans les comparatifs ou les recueils de logiciels (exemple: les publications de [[Gartner]] group), ainsi que les publications concernant des techniques et des applications, alors qu'elle a une forte visibilité sur la Wikipédia. N'est-ce pas une contradiction ?--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 2 octobre 2012 à 16:21 (CEST)
::::: [http://www.gartner.com/technology/core/products/research/topics/openSource.jsp] C’est l’un des 20 ''topics'' de Gartner justement ... j’avoue que je ne suis pas très convaincu par tes exemples. Dans le bandeau "base de données", il y a déja une classification évidente, il regroupe des bases de données. Le regroupement libre / pas libre est secondaire. D’ailleurs la majorité des autres bases citées sont libres sans ce que ce soit signalé. Enfin déja rien que sur ce sujet il y a pléthore de produit, on a aussi besoin de critères pour les choisir, c’est largement problématique. Le bandeau équivalent sur en: par exemple ne cite pas de logiciels (il y en a un pour les types de dbb, pas sur les moteurs). L’appoche  [[en:Comparison_of_relational_database_management_systems]] est intéressante puisqu’elle limite l’arbitraire du choix et laisse le lecteur choisir ce qui l’intéresse ... sur la palette, il y a surement beaucoup à dire et la discussion est déja en cours (depuis sa création en fait) sur la PDD, cf. [[Discussion_modèle:Palette_Systèmes_de_gestion_de_base_de_données]]. Sur [[Liste_des_logiciels_SIG]] le moindre des problème est la classification libre / propriétaire, elle m’a l’air inutilisable et très peu informative en l’état. [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 2 octobre 2012 à 17:24 (CEST)
:::::: Si on regarde en détail la palette SGBD, dans wp:en il y a un modèle [[:en:Template:Database]], qui est orienté autour des notions relatives aux bases de données et propose différentes pages de comparaison, ce qui est beaucoup plus intéressant qu'une classification fixe. Cette classification est de plus arbitraire (les SGBD se déclinent en relationnel, objet, embarqué, client/serveur et spatial) la remarque datant de 2008, qui se trouve dans la page de discussion de la palette est pertinente, mais n'a visible pas trouvé beaucoup d'échos...--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 2 octobre 2012 à 22:06 (CEST)
::::::: Le vrai problème c’est qu'il n’y a plus grand monde d’actif sur ce projet :) [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 2 octobre 2012 à 22:40 (CEST)
:Je me bats contre la mise en avant arbitraire de cette distinction par rapport à d'autres lorsque cela n'a pas lieu d'être (''cf.'' précédentes discussions sur cette même page) que l'on retrouve dans les trois derniers exemples que tu mentionnes.
:Dans les catégories où cette distinction est faite ''en même temps que d'autres'', mon avis est moins tranché. Le fait que la classification ait un côté militant ne remet pas en cause celui qu'elle soit largement répandue dans un milieu important. Ceci dit, il est toujours plus précis, d'indiquer les ''licences'' qui concernent le logiciel. « Libre » devrait être essentiellement une catégorie parente des licences dites « libres », ce qui permet de s'autoriser des catégories « libre selon X » et de lever toute ambiguïté sur le terme.
:Amicalement — [[Utilisateur:Arkanosis|Arkanosis]] <sup>[[Discussion Utilisateur:Arkanosis|✉]]</sup> 3 octobre 2012 à 16:19 (CEST)
:: Il n’y a plus vraiment de problème depuis assez longtemps sauf cas vraiment particuliers, la définition de logiciel libre est assez consensuselle et même rentrée dans certains dictionnaire, àmha. A mon avis les problèmes de neutralité ne sont pas vraiment dans l’expression "logiciel libre" mais de nos jour plus dans des articles comme [[Spotify]] ou on trouve "skype est un logiciel privateur", expression assez récente et pour le coup beaucoup moins consensuelle issue directement de la FSF qui reflète très bien son point de vue militant. [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 3 octobre 2012 à 16:55 (CEST)
:::On est d'accord ; le problème à souligner ici est de séparer les logiciels selon cette <u>seule</u> caractéristique (d'un côté les « libre », de l'autre les « pas libre ») ou d'indiquer cette <u>seule</u> caractéristique (« libre », « propriétaire ») entre parenthèses, quand un tas d'autres auraient été aussi (peu) pertinentes pour séparer ou commenter une liste.
:::Après, je n'aime pas l'emploi de « libre » pour son imprécision (soyons clair, à l'oral, selon le contexte, je ne dois pas l'employer beaucoup moins que la plupart des libristes — mais à l'écrit, c'est différent), mais c'est un autre sujet (quoique ça pose tout de même une granularité très particulière sur le vaste éventail de licences tant libres que propriétaires — d'où ma préférence pour des hiérarchies de catégories qui n'imposent pas une granularité plutôt qu'une autre). — [[Utilisateur:Arkanosis|Arkanosis]] <sup>[[Discussion Utilisateur:Arkanosis|✉]]</sup> 3 octobre 2012 à 17:28 (CEST)
:::: Sur wikipedia, il n’y a pas vraiment d’imprécision, on parle tout le temps de [[logiciel libre]] avec le lien vers l’article qui va bien. C’est une expression à part entière. Enfin peut être qu’on devrait parler de [[logiciel]] [[logiciel libre|libre]]. [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 3 octobre 2012 à 18:06 (CEST)
:::::Ben si : « logiciel libre » n'est pas aussi précis que « logiciel sous licence MIT/Expat » ou « logiciel sous licence AGPLv3 ». Le lien vers l'article va éventuellement faire comprendre au lecteur que justement, la notion de logiciel libre est très vaste, mais elle ne l'aidera pas à savoir quels sont les droits et devoirs qu'il a pour le logiciel bien précis qui l'intéresse (mis à part ce qu'on pourrait appeler un « dénominateur commun » très insuffisant dans beaucoup de cas). — [[Utilisateur:Arkanosis|Arkanosis]] <sup>[[Discussion Utilisateur:Arkanosis|✉]]</sup> 3 octobre 2012 à 19:08 (CEST)
:::::: C’est bien plus informatif en première approximation, on connaît plus facilement la notion de logiciel libre qui dégrossis pas mal que toutes les licences possibles et imaginables et leur détail. Un utilisateur par exemple n’est pas franchement impacté par la différence entre la GPL et une BSD, seul le contributeur pourra l’être. Si je te dis "sous licence CeCill" par exemple, tu sais du premier coup d’oeil de quoi il s’agit ?  [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 3 octobre 2012 à 19:30 (CEST)
:Bonjour, aujourd'hui j'ai deux autres exemples qui me tombent sous la main: [http://fr.wikipedia.org/w/index.php?title=Winamp&oldid=81918969 Winamp], Wikipédia met en avant le caractère ''non libre'' du logiciel, alors que les sites ou il peut être téléchargé (exemple ici [http://www.01net.com/telecharger/windows/Multimedia/lecteurs_audio_mp3_cd/fiches/27470.html]) mettent en avant le caractère ''gratuit'' du produit. Le deuxième exemple c'est la liste des [[serveur d'applications]] arbitrairement coupée en deux sections (1: libre, 2: propriétaire). Alors que dans cette source [http://books.google.ch/books?id=0VEEAAAAMBAJ&pg=PA108&lpg=PA108&dq=application+servers&source=bl&ots=fKGZf9FfIh&sig=NnUhxjbOoiRj35lHHg4ZiBEmKwM&hl=fr&sa=X&ei=BWVtUL-zMeqL4gTv9IHIDA&ved=0CGkQ6AEwCTgK#v=onepage&q=application%20servers&f=false] et celle-ci [http://books.google.ch/books?id=SazD_hoEDfcC&pg=PA125&lpg=PA125&dq=application+servers&source=bl&ots=fEERvlbf0Q&sig=eFUxhtZdy9YNBEz1U2hG8ZgDZVE&hl=fr&sa=X&ei=72ZtUN_mDcfZtAaNhYGgCg&ved=0CDgQ6AEwADgU#v=onepage&q=application%20servers&f=false] il y a un comparatif basé sur les fonctionnalités et les technologies prises en charge.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 4 octobre 2012 à 12:25 (CEST)

== Annonce proposition fusion ==

{{Annonce fusion d'article|2 octobre 2012|[[Wikipédia:Pages à fusionner#Licence_.28juridique.29_et_Licences_d.27exploitation_des_.C5.93uvres_de_l.27esprit|Procédure de fusion]] sur [[Licence (juridique)]] et [[Licences d'exploitation des œuvres de l'esprit]]}}

== Actu : Nouvel algorithme SHA-3 ==

Bonjour, le [[NIST]] vient de désigner l’algorithme qui deviendra [[SHA-3]], ce sera {{Lien|Keccak}}. À traduire sans doute. C’est une nouvelle fonction de hachage cryptographique basé sur le principe des fonction éponges : http://sponge.noekeon.org/. De ce que j’ai lu il a été sélectionné pour les nouveautés de ses bases mathématiques par rapport à ses prédécesseur {{Lien|SHA-2}} qui rendent peu probable qu’une nouvelle attaque touche les deux familles d’algorithmes à la fois. [[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 3 octobre 2012 à 15:34 (CEST)

PS: j’ai déja posté ce message chez les matheux et chez les cryptographes

== Ne faudrait-il pas fusionner [[Logiciel Libre]] et [[open source]] ? ==

Les deux notions sont équivalentes dans bien des cas, notamment la définition qui ne diverge que pour des détails que d’aucun (moi) qualifieraient de broutilles. Ne gagnerait-on pas à fusionner ces deux articles et à expliquer les divergences entre les deux mouvements dans cet article ?
La différence que j’y vois c’est que quand on parle d’open source, on parle plus du mouvement qui va avec. Ne devrait-on pas différencier le mouvement des logiciels ?
Je pose la question.
[[Utilisateur:TomT0m|TomT0m]] ([[Discussion utilisateur:TomT0m|d]]) 3 octobre 2012 à 18:12 (CEST)
:Je ne pense pas, la différence est probablement plus philosophique (qu'est ce qu'on met en avant ?) et sociologique (qui s'identifie aux libre ou à l'open source) mais la différence existe et je ne vois pas l'interêt de fusionner (les articles peuvent se citer mutuellement dans les sections ''article connexe''). --[[Utilisateur:PierreSelim|PierreSelim]] <sup><small>&#91;[[Discussion_utilisateur:PierreSelim|let discussion = fun _ ->]]&#93;</small></sup> 16 octobre 2012 à 15:38 (CEST)
::L'expression open source fait référence à un modèle de développement, alors que libre fait référence à l'utilisation que l'on peut faire des logiciels ou de leur code source. Il y a bien sûr une intersection entre les deux ensembles, mais je pense justement qu'il y a pas mal de confusion entre les deux expressions. Je pense donc qu'il ne faut pas fusionner ! Au contraire il faudrait bien expliquer la différence. [[Utilisateur:Shiningfm|Shiningfm]] ([[Discussion utilisateur:Shiningfm|d]]) 8 novembre 2012 à 13:20 (CET)
::: C’est bien subtil et pas si clair comme différence. Libre et open source qualifient tous les deux un logiciel, avant tout. En fait il y a confusion un peu partout. Parle t’on du mouvement du libre et du mouvement open source ? Cela dit tu as raison {{citation|Open source is a development method for software that harnesses the power of distributed peer review and transparency of process.}} d’après l’OSI. Maintenant les articles passent plus de temps à expliquer les différences et les rapports entre les deux que les concepts sous jascents qui relèvent quand même en grande partie du troll. Maintentant quand on regarde la définition Open-source, ça parle des caractéristique du logiciel et de son code. Pour la définition de logiciels libre, pareil, on parle du logiciel et de son code, et les deux définitions ne sont que subtilement différentes qui gagneraient question factorisation à être expliquées dans un seul article. — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 8 novembre 2012 à 23:11 (CET)
::::Je ne trouve pas ça si subtil. Effectivement les deux concepts vont parler des logiciels et de leur code source, mais l'analyse se fait sur des axes différents. Open source veut dire que le logiciel est '''développé''' par une communauté (en tout cas potentiellement). En gros le processus de développement utilisera des outils pour gérer les différentes contributions. Alors que le logiciel libre garantit certains usages que l'on pourra faire du logiciel. Donc à mon avis ce n'est pas seulement une question de "mouvement". Si on fait un parallèle avec un wiki, les pages sont "open source" car chacun peut ajouter sa pierre à l'édifice. Mais ça ne veut pas dire que le contenu de la page sera obligatoirement sous licence libre. Sinon oui tu as raison il y a énormément de troll sur le sujet ! Et je ne suis d'ailleurs pas tellement d'accord avec l'introduction de l'article open source. Il faudrait certainement revoir ces deux articles, mais en s'attendant à une guéguerre d'édition... [[Utilisateur:Shiningfm|Shiningfm]] ([[Discussion utilisateur:Shiningfm|d]]) 9 novembre 2012 à 00:07 (CET)
::::: ce qu’il faut surtout c’est des références fiables et faisant autorité plutôt que du ''je suis pas d’accord'' {{clin}}. Pour moi ce sont deux facettes d’une même pièce qui ne s’accordent pas vraiment de facade pour des raisons de désaccord politique ouphilosophique mais qui ne sont essentiellement pas vraiment d différentes.  — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 9 novembre 2012 à 11:50 (CET)
:::::: En y regardant de près tu as peut être raison. Je vois sur le site de l'OSI que {{citation|Open source doesn't just mean access to the source code. The distribution terms of open-source software must comply with the following criteria:}} avec des critères vraiment proches de la définition de la FSF ([http://www.gnu.org/philosophy/free-sw.html]). Pour moi qu'un logiciel soit open-source c'était seulement la manière dont il est développé. Ca ne semble pas être le cas ! Il n'y a d'ailleurs sûrement pas de tentative de récupération de l'expression open source car l'OSI est fondée en 1998.
:::::: Bref les concepts semblent vraiment similaires. Mais du coup quel titre pour une fusion ? (si elle a lieu) [[Utilisateur:Shiningfm|Shiningfm]] ([[Discussion utilisateur:Shiningfm|d]]) 9 novembre 2012 à 14:19 (CET)
::::::: FLOSS ou FOSS semblerait être un bon compromis pour un nommage pour la fusion, après ce n’est peut être pas la dénomination la plus courante. — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 10 décembre 2012 à 19:19 (CET)
{{citation|Free software is a social movement, while Open source is a method for developing software}} c'est écrit dans cette source [http://books.google.ch/books?id=75KT6GdcWbYC&printsec=frontcover&dq=software&source=bl&ots=s43gAyTW4i&sig=l1YjbnROQ7Gbtsyb3O3JsyiFAZ4&hl=fr&sa=X&ei=eX92UNefJo_bsgaDvoHoAw&ved=0CGIQ6AEwBzgU#v=onepage&q=software&f=false] à la page 8. Concernant la fusion, les deux concepts sont déja fusionnés en dehors de Wikipédia, sous la dénomination ''FOSS'' (toujours selon la même source).[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 9 novembre 2012 à 18:37 (CET)
: Il y a même un article [[Free/Libre Open Source Software]] sur la wp francophone. — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 10 décembre 2012 à 19:19 (CET)

== [[:Catégorie:Logiciel éducatif libre]] ==

Bonjour, cette catégorie avait été supprimée en 2009 lors de la réorganisation des catégories concernant les logiciels, parce que redondante avec [[:Catégorie:Logiciel éducatif]] et [[:Catégorie:Logiciel sous licence libre]] (voir [[Discussion Projet:Informatique/2009#Catégories logiciel]]). Elle a été re-créée cette semaine par un nouveau venu.

L'auteur, pas très locace, se défend en disant que la catégorie existe dans d'autres éditions de wikipédia, notamment espagnol, italien, et portugais. En examinant l'historique des catégories dans les autres langues, je m’aperçoit qu'elles ont été créées tout récemment, par le même auteur que sur wp:fr...

* [http://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Logiciel_%C3%A9ducatif_libre français]
* [http://es.wikipedia.org/wiki/Categor%C3%ADa:Software_educativo_libre espagnol]
* [http://pt.wikipedia.org/wiki/Categoria:Software_educacional_livre portugais]
* [http://it.wikipedia.org/wiki/Categoria:Software_libero_per_l%27educazione italien]

Alors, amélioration bienvenue, ou tentative de spam ?--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 8 octobre 2012 à 13:14 (CEST)
: C’est une question intéressante, je n’ai pas d’avis tranché immédiatement ... Quelques réflexions, il y a plusieurs points de vue possibles
:# La politique globale de classification : la redondance est avéré, c’est clairement l’intersection entre les logiciels libres et les logiciels éducatifs. De manière générale, ne pas faire les combinaisons de toutes les sous catégorie possible est un point de vue qui se défend. D'un autre côté est-ce qu’il existe une politique claire du point de vue de la classification sur wikipedia ? Je n’ai jamais creusé la question je dois dire. L’avantage des catégories c’est qu’on peut en créer autant qu’on veut.
:# D'un point de vue pratique, en supposant qu’on fasse la chasse aux redondances : quelqu’un qui voudrait trouver l’ensemble des logiciels libres éducatif pourrait le faire, le moteur de recherche propose une directive "incategory" qui permettrait de calculer l’intersection en faisant incategory:"logiciel libre" and incategory":logiciel éducatif. Ça n’a cependant pas l’air de bien marcher, cette directive à l’air capricieuse, et ce n’est de toute façon pas vraiment à la portée d’un néophyte ou d’un simple utilisateur de l’encyclopédie. Cette remarque est valable pour n’importe quel croisement de catégorie.
:# Si on considère que la redondance n’est pas rédhibitoire et que l’avantage du système de catégorisation de wikipedia, c’est qu’on peut ajouter plusieurs catégories à un article, il faut décider si cette catégorie en particulier est pertinente. Elle pourrait à la fois être une sous catégorie de logiciel libre et de logiciel éducatif. Une recherche google {{Google|logiciel libre éducatif}} permet de découvrir que des gens sont intéressés par ce type de logiciels en particulier, par exemple [http://www.tice.ac-versailles.fr/logicielslibres/ l’académie de Versaille y consacre une page]. 
:# D’un point de vue pratique toujours, la catégorie [[:Catégorie:Logiciel sous licence libre|logiciels sous licence libre]] englobe beaucoup de logiciel, il ne semble pas absurde de la découper en sous catégorie pour s’y retrouver. Dans ce cas une sous catégorie "logiciels éducatifs sous licence libre" n’est pas idiote. Ça implique que cette sous catégorie soit aussi une sous catégorie de "logiciel éducatif", ce qui pourrait être source de conflit ici. Je vois pas d’autre solution à part éventuellement à ce qu’un logiciel se retrouve à la fois dans une catégorie et une de ses sous catégorie, ce qui viole par contre une règle de base. Ou alors ne pas catégoriser "logiciel libre éducatif" comme sous catégorie de "logiciel éducatif". 
:— [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 8 octobre 2012 à 16:08 (CEST)
::Il n'existe pas à ma connaissance ''une'', mais ''deux'' politiques de catégorisations: par tags et par découpage du savoir (voir [[Projet:Catégories/Réflexions]]). Depuis 2009,les catégories des logiciels sont du style ''par tag'', ce qui permet de résoudre des problèmes comme les logiciels multi-licences, multi-plateformes ou multi-fonctions. Comme indiqué dans les réflexions, {{citation|Les catégories par tag sont un moyen de navigation très pratique à travers les articles ; de plus, il permettent d'opérer des recherches croisées (?). Mais leur souplesse se paie par des catégories sur-peuplées qui ne distinguent pas l'essentiel de l'accessoire.}}
::Ensuite que la catégorie ''logiciel sous licence libre'' ainsi que ces sous-catégories contient un grand nombre d'article, ça me parait normal, étant donné qu'elle couvre 90% du contenu du portail du logiciel libre (2600 articles), dans le cadre de la réorganisation de 2009, différentes sous-catégories ont été faites pour classifier les logiciels en fonction de la licence (GPL, MPL, Apache, ...). Aujourd'hui il y a encore 350 articles qui ne sont pas placés dans les sous-catégories. quels sont ces articles ? sont-ils mal classés ? manque-il une sous-catégorie ? à voir de plus près. En attendant j'ai placé le bandeau ''à diffuser'' sur cette catégorie.
::Cette nouvelle catégorie va à l'encontre de la politique de catégorisation par tags. Une des règles d'admissibilité des catégories est qu'une catégorie corresponde à un champ notoire du savoir, ce qui est le cas (les logiciels éducatifs libres sont un sujet d'intérêt).--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 8 octobre 2012 à 16:51 (CEST)
::: [[Wikipédia:Conventions_sur_les_catégories#Recommandations]] {{citation|Nombre d'articles : Il est recommandé, quand c'est possible et pertinent, de réorganiser dans des sous-catégories les catégories surpeuplées (c'est à dire qui possèdent plusieurs centaines d'entrées), sauf s'il n'y a pas potentiellement un nombre significatif d'articles à y faire figurer. A l'inverse, il est recommandé de ne pas créer de catégorie s'il n'y a pas potentiellement une dizaine d'articles à y mettre.}}. À part ça je ne vois pas trop ou il est fait mention de cette politique de classement "par tag". Tu as des liens un peu plus précis à ce sujet ? Je n’en ai pour l’instant vu mention nulle part. — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 8 octobre 2012 à 17:04 (CEST)
::: Précision sur la question sur le classement par tag des logiciels : c’est indiqué quelque part sur le projet ou les recommandation du projet ? si ça été fait en quatimini sur la pdd du projet informatique on ne peut pas trop reprocher à un nouveau venu de ne pas être au courant, je ne le suis par exemple pas du tout. — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 8 octobre 2012 à 17:18 (CEST)
::: Complément d'infos : le bug sur les recherches dans les catégories croisées n’est toujours pas fermé … [https://bugzilla.wikimedia.org/show_bug.cgi?id=5244] en pratique ça ne m’a pas l’air très pratiquable de croiser les tages sur médiawiki en l’état actuel des choses, c’est à prendre en compte. — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 8 octobre 2012 à 17:21 (CEST)
:::: Voir [[Projet:Catégories/Réflexions#L'opposition entre index et découpage]] concernant la classification par tags. A part ca il est vrai que l'arborescence des catégories informatique est très peu documentée (pas du tout ?).--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 8 octobre 2012 à 17:54 (CEST)
::::: Ça n’est pas vraiment une politique de wikipedia, c’est une définition sur une page dédiée à la réflexion sur la classification de Wikipedia (un peu en sommeil mais fort pertinente et intéressante) qui n’a pour l’instant pas donnée lieux à décision ni à manière de faire précise. En outre un système par tag peut parfaitement cohabiter avec un autre genre de classification, et n’est pas ce qui est de plus pratique à utiliser avec les outils actuels de mediawiki.
::::: Bilan de mon avis à ce stade de la discussion : cette catégorie me semble à la fois admissible d’après les critères de notoriété et recommandée par les politiques de classification de wikipedia (pour éviter les catégories trop grosses). On a aussi besoin de discuter sur la classification des logiciel, (en  collaboration avec le [[projet:Catégorie]] ?) et de documenter un peu tout ça. A noter aussi que la discussion n’est pas forcément très urgente puisque la mise en place de wikidata (l’anné prochaine théoriquement) devrait modifier singulièrement les choses sur les possibilités de mettre des étiquettes sur les articles, c’est fait pour ajouter des métadonnées ... — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 8 octobre 2012 à 18:24 (CEST)
:::::: Cette réflexion est à mon avis une recherche et une observation des politiques de classement par catégories qui, de manière informelle, sont déjà appliquées sur Wikipédia. C'est tout à fait informel, et il n'y a aucune décision sur le sujet. Sinon d'accord avec le fait qu'il vaut peut-être mieux attendre la mise en place de wikidata pour aviser.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 8 octobre 2012 à 19:41 (CEST)

== un problème de suppression des éléments dans mon PC ==

Bonjour à tous!!!

Aidez-moi pour avoir la solution: j'avais eu un problème à mon PC, il se plantait quand je travaillais, j'ai donc été obligé de faire une nouvelle réinstallation de Windows. Mais les anciens programmes et installation ne sont pas détruits. Quand je fais une recherche pour le nettoyage de mon disque, je voie des fichier et documents que j’aimerais les supprimés mais l'accès à ces fichiers et documents sont refusés. 

La deuxième choses : mon lecteur de CD s'ouvre tout seule et refuse de fermer ? 

Alors qu'est-ce que je dois faire pour résoudre mes problèmes ? Aidez-mois chers amis.
: mauvais endroit pour poser cette question, on ne fait pas de support informatique, on discute de la présentation des articles consacrés à l’informatique sur wikipedia. — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 9 novembre 2012 à 16:36 (CET)

== Les logiciels en français de [[Newton OS]] ==
Bonjour. Je suis en train de créer l'article "[[Newton OS]]". J'ai voulu rajouter les noms des logiciels embarqués par défaut mais je ne les ai trouvés quand anglais !! Malgré de longues recherches... Quelqu'un peut il m'aider ??
--[[Utilisateur:Adler92190|Adler92190]] ([[Discussion utilisateur:Adler92190|d]]) 9 novembre 2012 à 13:53 (CET)
:Et pourquoi une liste de logiciels en anglais ne serait pas valable ? Les noms sont certainement les mêmes dans l'édition en français.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 9 novembre 2012 à 18:59 (CET)
: D’accord, d'accord, c'est ce que je vais faire.
Merci, --[[Utilisateur:Adler92190|Adler92190]] ([[Discussion utilisateur:Adler92190|d]]) 12 novembre 2012 à 16:30 (CET)

== Proposition pour classer les ébauches ==

Il s'agirait de parcourir les pages étant dans la catégorie [[:Catégorie:Matériel informatique]] ou ses sous-catégories directes ainsi que les pages en ébauches <nowiki>{{ébauche|informatique}}</nowiki> et de transformer cette ébauche en ébauche matériel informatique. Cette dernière catégorie ne comprenant pour l'instant que 6 pages alors que la catégorie informatique en contient plus de 4000. '''JR''' <small>[[Discussion_utilisateur:Jrcourtois|(disc)]]</small> 10 novembre 2012 à 14:48 (CET)

== [[Windows 8]] ==

Bonjour. Vous pourriez revoir le style de l'article?--[[Spécial:Contributions/86.201.13.189|86.201.13.189]] ([[Discussion utilisateur:86.201.13.189|d]]) 10 novembre 2012 à 22:34 (CET)
: Qu'entendez-vous précisément par ''style'' ? --[[Utilisateur:Franz53sda |Franz53sda]] <sup><small>[[Discussion Utilisateur:Franz53sda|le 22 à Asnières]]</small></sup> 10 novembre 2012 à 22:48 (CET)
::{{citation|la dernière version du système d'exploitation Windows commercialisée depuis ''le 26 octobre 2012''}}, il y a des petites choses à actualiser, je suppose. Un bandeau est déjà présent pour avertir les rédacteurs.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 10 novembre 2012 à 22:51 (CET)
:::Et aussi le sourcer.--[[Spécial:Contributions/86.201.13.189|86.201.13.189]] ([[Discussion utilisateur:86.201.13.189|d]]) 10 novembre 2012 à 22:56 (CET)
:::: Donc ce n'est pas le « ''style'' » qui est en question. Merci pour les précisions et bonnes contributions. --[[Utilisateur:Franz53sda |Franz53sda]] <sup><small>[[Discussion Utilisateur:Franz53sda|le 22 à Asnières]]</small></sup> 10 novembre 2012 à 23:40 (CET)
::::: Vous pourriez sourcer aussi? Moi aussi, j'essaye de mon côté.--[[Spécial:Contributions/86.201.13.189|86.201.13.189]] ([[Discussion utilisateur:86.201.13.189|d]]) 11 novembre 2012 à 00:41 (CET)
:::::: Je suis peu versé en la matière, ma question portait sur ce que vous entendiez par « ''style'' » ; sinon, on peut avoir des sources secondaires (indispensables pour enrichir une page, c'est juste) qui valent ce qu'elles valent : [http://lexpansion.lexpress.fr/high-tech/les-7-grandes-nouveautes-de-windows-8_353053.html ici], [http://techno.lapresse.ca/nouvelles/logiciels/201211/09/01-4592097-windows-8-une-evolution-materielle-et-logicielle.php là], [http://www.journaldunet.com/developpeur/technos-net/windows-8-multi-terminal-et-multiplate-forme-1112.shtml là] où [http://www.leparisien.fr/espace-premium/actu/le-windows-8-debarque-avec-des-innovations-fortes-26-10-2012-2266671.php là] ; désolé si ce que je vous indique est trop généraliste, mais les sources ne manquent assurément pas, bonnes contributions ; --[[Utilisateur:Franz53sda |Franz53sda]] <sup><small>[[Discussion Utilisateur:Franz53sda|le 22 à Asnières]]</small></sup> 11 novembre 2012 à 00:56 (CET)
::::::: Vous pourriez sourcer l'articlet l'améliorer?--[[Spécial:Contributions/86.201.13.189|86.201.13.189]] ([[Discussion utilisateur:86.201.13.189|d]]) 11 novembre 2012 à 15:19 (CET)
:::::::: Je viens de sourcer.--[[Spécial:Contributions/86.201.13.189|86.201.13.189]] ([[Discussion utilisateur:86.201.13.189|d]]) 11 novembre 2012 à 18:13 (CET)
::::::::: Et vous avez bien fait d'ajouter vous-même ce que vous estimez profitable pour l'encyclopédie : [[Wikipédia:N'hésitez pas !]] ; --[[Utilisateur:Franz53sda |Franz53sda]] <sup><small>[[Discussion Utilisateur:Franz53sda|le 22 à Asnières]]</small></sup> 11 novembre 2012 à 18:44 (CET)

== informatique  ==

bonjour;
je prepare une licence et j'ai des problemes avec l'informatique et l'automatisme en fait du visuel basic et je suis un peut perdu j'aimerais avoir quelque bases ,ou des petit exo simple detailler pour comprendre le principe.Merci ma boite mail est : ''(supprimé pour vous protéger)''
:Wikipédia est une encyclopédie et donc ne dispense pas d'exercice, c'est son projet frère Wikiversité qui tient ce rôle : [[v:Visual Basic]]. [[Utilisateur:JackPotte|JackPotte]] ([[Discussion utilisateur:JackPotte|<font color="#FF6600">$</font>♠]]) 11 novembre 2012 à 14:41 (CET)

== projet informatique  ==

comment faire un projet informatique ? est des idée des projets

: Wikipédia est une encyclopédie et ne dispense donc pas de conseils. Vous pouvez néanmoins consulter [[Chef_de_projet#Chef_de_projet_informatique]]. Vous gagneriez aussi à apprendre la grammaire, on ne vous comprend qu'en essayant de deviner ce que vous voulez dire, et en informatique comme ailleurs, la communication est une des clés du succès. --[[Utilisateur:MathsPoetry|MathsPoetry]] ([[Discussion utilisateur:MathsPoetry|d]]) 1 décembre 2012 à 20:23 (CET)

== [[Component Object Model]] et sujets voisins ==

Bonjour, en travaillant sur le sourçage de l'article [[Component Object Model]], j'ai constaté une grande confusion sur les différents sujets connexes [[OLE]], [[ActiveX]], [[DCOM]], [[COM+]], [[Microsoft Transaction Server|MTS]].... Une confusion qui se retrouve jusque dans la littérature sur le sujet. Si ca intéresse quelqu'un d'y mettre en peu d'ordre ? j'ai commencé à faire le tri en ajoutant des paragraphes d'intro sur ces sujets dans la section ''Produits connexes'' de [[Component Object Model]].--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 6 décembre 2012 à 23:32 (CET)

== Admissibilité de [[Contexts and Dependency Injection]] ==

Un avis sur l'admissibilité de [[Contexts and Dependency Injection]] ? Merci pour votre aide, cela ne mérite peut-être pas une PàS. Cordialement, [[Utilisateur:Linan|Linan]] ([[Discussion utilisateur:Linan|d]]) 10 décembre 2012 à 13:22 (CET)
:Vu la couverture littéraire, ca me semble admissible [https://www.google.ch/#hl=fr&safe=off&q=context+and+dependency+injection+cdi&bpcl=39650382&um=1&ie=UTF-8&tbo=u&tbm=bks&source=og&sa=N&tab=wp&ei=iRLGULSRBcyN4gS6-oHYDA&bav=on.2,or.r_gc.r_pw.r_qf.&fp=9180f1b5bfa7ff09&biw=1366&bih=662]. Par contre ce n'est pas un plug-in, comme indiqué en intro, mais une [[interface de programmation]].--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 10 décembre 2012 à 17:54 (CET)
::Ok, ça me va bien comme avis. Merci et bonne continuation ! [[Utilisateur:Linan|Linan]] ([[Discussion utilisateur:Linan|d]]) 10 décembre 2012 à 18:39 (CET)
: C'est peut être admissible, par contre c'est un peu vide et d'intérêt encylopédique pas terrible (amha), ce serait pas mieux dans [[J2EE]] ? Ou [[injection de dépendance]] dont l’intérêt est certain. — [[Utilisateur:TomT0m|TomT0m]] <sup>&#91;[[Discussion Utilisateur:TomT0m|bla]]&#93;</sup> 10 décembre 2012 à 19:28 (CET)
::Tout à fait. En l'état l'article n'est pas digne d'intérêt. Est-il préférable de proposer la fusion avec le sujet principal [[J2EE]] ?--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 14 décembre 2012 à 23:33 (CET)

== Fusion Windows 8/Blue ==

Vous en pensez quoi?--[[Utilisateur:Mwabw2|Mwabw2]] ([[Discussion utilisateur:Mwabw2|d]]) 14 décembre 2012 à 23:24 (CET)

== Infusion "langage informatique" dans "langage de programmation" ? ==

Bonjour,
j'ai quelque difficulté à comprendre l'intérêt de séparer les langages informatiques des langages de programmation. Dans la présentation, les premiers ne sont pas forcément Turing-complets, alors que les deuxièmes le sont. Mais ce n'est peut-être pas le critère principal ? Veut-on séparer les langages d'interrogation ou de spécification des autres ?

En cherchant sur les articles dans d'autres langues, je vois que la séparation en deux pages n'est pratiquement faite nulle part ailleurs. Je pense que l'absorption de "langage informatique" dans "langage de programmation" serait une bonne chose. Cordialement --[[Utilisateur:ManiacParisien|ManiacParisien]] ([[Discussion utilisateur:ManiacParisien|d]]) 19 décembre 2012 à 08:43 (CET)
:Un langage informatique ne sert pas forcément à programmer, contrairement à un langage de programmation. Maintenant, après avoir recherché des sources pour l'article [[langage de programmation]], je constate que les ouvrages qui parlent de langages informatiques sous un autre angle que celui de la programmation sont peu nombreux voire inexistants, j'ai par conséquent des doutes sur le potentiel d'évolution de l'article [[langage informatique]], et un moyen de faire face à ce problème serait de fusionner les deux articles.--[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 19 décembre 2012 à 20:00 (CET)
:: Pour info, sur WP en, il y avait une page [http://en.wikipedia.org/w/index.php?title=Computer_language&oldid=244096708 Computer Language] (similaire à [[langage informatique]]) différente de [[en:Programming language|programming language]] qui a été transformée en redirection en 2008 suite à une discussion. Pour ce qui me concerne, c'est une erreur de la WP anglophone qui y a perdu au change (même si la page originale était à réécrire) car les deux concepts sont différents (l'un englobe l'autre mais pas l'inverse): il y a des fondements théoriques solides pour justifier cette distinction. [[Utilisateur:Bublegun|Bublegun]] ([[Discussion utilisateur:Bublegun|d]]) 19 décembre 2012 à 20:02 (CET)
:::Tout à fait d'accord, pour donner un exemple évident, HTML n'est PAS un langage de programmation. [[Utilisateur:Xentyr|Xentyr]] ([[Discussion utilisateur:Xentyr|d]]) 21 décembre 2012 à 12:54 (CET)

== admissibilité [[Agile Alliance]] (décembre 2012) ==

Pour info, en page de [[Discussion:Agile_Alliance#Admissibilit.C3.A9_.28d.C3.A9cembre_2012.29|Discussion : Agile Alliance (Admissibilité)]] --[[Utilisateur:Eliane Daphy|dame éliane]] <sup>&#91;[[Discussion Utilisateur:Eliane Daphy|¿quoi donc ?]]&#93;</sup> 22 décembre 2012 à 16:31 (CET)

== L'article Jean-Daniel Fekete est proposé à la suppression ==

{| align="center" title="{{((}}subst:avertissement suppression page{{!}}page{{))}}" border="0" cellpadding="4" cellspacing="4" style="border-style:none; background-color:#FFFFFF;"
| [[Image:Icono consulta borrar.png|64px|Page proposée à la suppression]]
|Bonjour,

L’article « '''{{Lien à supprimer|1=Jean-Daniel Fekete}}''' » est proposé à la suppression ({{cf.}} [[Wikipédia:Pages à supprimer]]). Après avoir pris connaissance des [[Wikipédia:Critères d'admissibilité des articles|critères généraux d’admissibilité des articles]] et des [[:Catégorie:Wikipédia:Admissibilité des articles|critères spécifiques]], vous pourrez [[Aide:Arguments à éviter lors d'une procédure de suppression|donner votre avis]] sur la page de discussion '''[[Discussion:Jean-Daniel Fekete/Suppression]]'''.

Le meilleur moyen d’obtenir un consensus pour la conservation de l’article est de fournir des [[Wikipédia:Citez vos sources|sources secondaires fiables et indépendantes]]. Si vous ne pouvez trouver de telles sources, c’est que l’article n’est probablement pas admissible. N’oubliez pas que les [[Wikipédia:Principes fondateurs|principes fondateurs]] de Wikipédia ne garantissent aucun droit à avoir un article sur Wikipédia.
|}

[[Utilisateur:Linan|Linan]] ([[Discussion utilisateur:Linan|d]]) 3 janvier 2013 à 13:26 (CET)

== Projet info théorique ==

Bonjour,

le [[Projet:Informatique théorique]] existe depuis peu. Je ne suis pas un spécialiste de ce genre de page donc c'est plutôt rachitique pour l'instant. Si vous êtes intéressés, vous êtes les bienvenus ! En espérant que cela "dynamise" un peu le portail.

Bien cordialement,

--[[Utilisateur:Roll-Morton|Roll-Morton]] ([[Discussion utilisateur:Roll-Morton|d]]) 4 janvier 2013 à 14:15 (CET)

== articles problématiques : [[modèle (informatique)]] / [[schéma conceptuel]] ==

Bonjour,

J'ai constaté en passant par l'article [[schéma conceptuel]] que celui-ci regroupait plusieurs notions, dont des notions informatiques. Or, dans la page de discussion, plusieurs messages critiquaient la manière dont la partie informatique était traitée (voir remettaient en cause sa place à cet endroit), sans qu'aucune modification n'ait été faite par la suite... Je viens donc vous mettre au courant. 
Il s'agit de savoir si la description donnée sur la page est correcte, complète, pertinente ; s'il serait nécessaire de rediriger vers un article existant plus crédible ou de dissocier la page (pour avoir un article traitant spécifiquement de l'aspect informatique du ''« schéma conceptuel »''), ..?

Qui plus est, je constate que la page [[modèle (informatique)]] n'est pas terrible non plus. Regardez notamment les liens interlangues qui ne m'ont pas l'air pertinents. Si quelqu'un pouvait rediriger vers quelque chose de mieux ou améliorer globalement l'article, ça serait cool.

Globalement, je constate qu'il y a beaucoup d'articles (en anglais aussi) qui reprennent des termes comme ''« modèle »'' ou ''« schéma »'' dans le cadre informatique, sans que ça soit toujours clair s'ils sont synonymes ou non, s'ils sont bien définis parmi les spécialistes, etc. Je ne me sens pas forcément capable d'identifier les conflits, problèmes de traduction et ambiguïtés propres au domaine-même.

Merci d'avance à ceux qui se pencheront sur le sujet! -- [[Utilisateur:Gerfaut|Gerfaut]] ([[Discussion utilisateur:Gerfaut|d]]) 11 janvier 2013 à 17:40 (CET)
: Bien vu, c’est assez brouillon en l’état. Je pense que le schéma conceptuel, en informatique, est équivalent à un modèle, au sens large. Cependant un modèle n’est pas forcément un schéma ou un diagramme. La page [[Modèle (informatique)]] ne pourra pas vraiment être autre chose qu’une page d’homonymie, tant le terme est utilisé un peu partout, que ce soir pour la [[modélisation des données]], ou les modèles de calculs en info théorique, en passant par tout ce que vous voulez.
: En ce qui concerne la bonne traduction pour Modèle, il faut aller la chercher [[:en:Model|ici]] ou [[:en:Conceptual model|là]], voire [[:en:Pattern (disambiguation)|là bas]], et bon courage (pour résumer, y’en a pas une qui corresponde simplement à Modèle dans un contexte informatique). —[[Utilisateur:Fulax|Fulax]] ([[Discussion utilisateur:Fulax|d]]) 11 janvier 2013 à 20:06 (CET)
Bonjour. <br>
En effet, bon courage pour essayer de "synthétiser" la notion de "schéma conceptuel" dans le domaine des "techniques" ou des "méthodes" d'analyse et de programmation de problèmes informatiques. <br>
Au cours des années 70, 80 et au début des années 90, cette "notion" et ces "méthodes" étaient très à la mode. Notamment dans le cades de l’application de la [[Merise (informatique)|méthode Merise]] pour l'analyse des données (tant fonctionnelle qu'organique) pour une représentation dans une [[base de données relationnelle]] (ou autre). Ces "concepts/méthodes" avaient bien pris en France dans le domaine de la Gestion en informatique. Un peu moins aux US où d’autres méthodes d'analyse étaient utilisées. Les schémas (conceptuels, organiques, de programmation,...) étaient très tendance à l'époque. Quelques livres, études, thèses... en ces domaines aussi.  Que reste-t-il de tout cela ? Beaucoup d'ouvrages universitaires, quelques [[Société pour l'informatique industrielle|SII]] qui ont bien "surfé" sur le truc pour le vendre, quelques belles applications dans le monde de la Gestion des entreprises,... Qu'en dire en 2013 ? A mon avis, pas grand chose. Juste un courant, comme il en a tant existé dans l'histoire de l'informatique et comme il en existera toujours. <small>(j'aime à répéter que l'informatique n'est pas une science, juste un ensemble de techniques)</small>. Essayer d'en faire un article WP, personnellement, je ne m'y aventurerai point. --[[Utilisateur:Kootshisme|Kootshisme]] ([[Discussion utilisateur:Kootshisme|d]]) 11 janvier 2013 à 21:13 (CET)

== L'article Pixlr Editor est proposé à la suppression ==

{| align="center" title="{{((}}subst:avertissement suppression page{{!}}page{{))}}" border="0" cellpadding="4" cellspacing="4" style="border-style:none; background-color:#FFFFFF;"
| [[Image:Icono consulta borrar.png|64px|Page proposée à la suppression]]
|Bonjour,

L’article « '''{{Lien à supprimer|1=Pixlr Editor}}''' » est proposé à la suppression ({{cf.}} [[Wikipédia:Pages à supprimer]]). Après avoir pris connaissance des [[Wikipédia:Critères d'admissibilité des articles|critères généraux d’admissibilité des articles]] et des [[:Catégorie:Wikipédia:Admissibilité des articles|critères spécifiques]], vous pourrez [[Aide:Arguments à éviter lors d'une procédure de suppression|donner votre avis]] sur la page de discussion '''[[Discussion:Pixlr Editor/Suppression]]'''.

Le meilleur moyen d’obtenir un consensus pour la conservation de l’article est de fournir des [[Wikipédia:Citez vos sources|sources secondaires fiables et indépendantes]]. Si vous ne pouvez trouver de telles sources, c’est que l’article n’est probablement pas admissible. N’oubliez pas que les [[Wikipédia:Principes fondateurs|principes fondateurs]] de Wikipédia ne garantissent aucun droit à avoir un article sur Wikipédia.
|}

[[Utilisateur:Linan|Linan]] ([[Discussion utilisateur:Linan|d]]) 12 janvier 2013 à 21:12 (CET)

== L'article Test On Software Applications est proposé à la suppression ==

{| align="center" title="{{((}}subst:avertissement suppression page{{!}}page{{))}}" border="0" cellpadding="4" cellspacing="4" style="border-style:none; background-color:#FFFFFF;"
| [[Image:Icono consulta borrar.png|64px|Page proposée à la suppression]]
|Bonjour,

L’article « '''{{Lien à supprimer|1=Test On Software Applications}}''' » est proposé à la suppression ({{cf.}} [[Wikipédia:Pages à supprimer]]). Après avoir pris connaissance des [[Wikipédia:Critères d'admissibilité des articles|critères généraux d’admissibilité des articles]] et des [[:Catégorie:Wikipédia:Admissibilité des articles|critères spécifiques]], vous pourrez [[Aide:Arguments à éviter lors d'une procédure de suppression|donner votre avis]] sur la page de discussion '''[[Discussion:Test On Software Applications/Suppression]]'''.

Le meilleur moyen d’obtenir un consensus pour la conservation de l’article est de fournir des [[Wikipédia:Citez vos sources|sources secondaires fiables et indépendantes]]. Si vous ne pouvez trouver de telles sources, c’est que l’article n’est probablement pas admissible. N’oubliez pas que les [[Wikipédia:Principes fondateurs|principes fondateurs]] de Wikipédia ne garantissent aucun droit à avoir un article sur Wikipédia.
|}

[[Utilisateur:Linan|Linan]] ([[Discussion utilisateur:Linan|d]]) 14 janvier 2013 à 22:24 (CET)

== L'article ISOGRAD est proposé à la suppression ==

{| align="center" title="{{((}}subst:avertissement suppression page{{!}}page{{))}}" border="0" cellpadding="4" cellspacing="4" style="border-style:none; background-color:#FFFFFF;"
| [[Image:Icono consulta borrar.png|64px|Page proposée à la suppression]]
|Bonjour,

L’article « '''{{Lien à supprimer|1=ISOGRAD}}''' » est proposé à la suppression ({{cf.}} [[Wikipédia:Pages à supprimer]]). Après avoir pris connaissance des [[Wikipédia:Critères d'admissibilité des articles|critères généraux d’admissibilité des articles]] et des [[:Catégorie:Wikipédia:Admissibilité des articles|critères spécifiques]], vous pourrez [[Aide:Arguments à éviter lors d'une procédure de suppression|donner votre avis]] sur la page de discussion '''[[Discussion:ISOGRAD/Suppression]]'''.

Le meilleur moyen d’obtenir un consensus pour la conservation de l’article est de fournir des [[Wikipédia:Citez vos sources|sources secondaires fiables et indépendantes]]. Si vous ne pouvez trouver de telles sources, c’est que l’article n’est probablement pas admissible. N’oubliez pas que les [[Wikipédia:Principes fondateurs|principes fondateurs]] de Wikipédia ne garantissent aucun droit à avoir un article sur Wikipédia.
|}

[[Utilisateur:Linan|Linan]] ([[Discussion utilisateur:Linan|d]]) 14 janvier 2013 à 22:25 (CET)

== Les articles [[Jasper]] et [[Jasper (informatique)]] sont proposés à la fusion ==
[[Image:Merge-arrows.svg|60px|left|Proposition de fusion en cours.]]

La discussion a lieu sur la page [[Wikipédia:Pages à fusionner#Jasper et Jasper (informatique)]]. La procédure de fusion est consultable sur [[Wikipédia:Pages à fusionner]].

[[Utilisateur:Silex6|Silex6]] ([[Discussion utilisateur:Silex6|d]]) 25 juillet 2013 à 12:23 (CEST)

"""


ANNOUNCES_SAMPLE = u"""<noinclude>[[Catégorie:Projet:Informatique|Annonces]]</noinclude>
<center>[{{fullurl:Projet:Informatique/Annonces|action=edit}} Annoncer quelque chose] — [{{fullurl:Projet:Informatique/Annonces|action=watch}} Suivre les modifications]</center>
<center>{{article détaillé|contenu=Archives Annonces: [[Discussion Projet:Informatique/2012/Annonces|2012]] - [[Discussion Projet:Informatique/2013/Annonces|2013]]}}</center>
<noinclude>== Annonces ==</noinclude>
<!------------------------------- Rajouter ci-dessous la dernière annonce ----------->
{{Annonce proposition suppression|nom=PagePlus|12 février 2013}}
{{Annonce proposition suppression|nom=First Assistant| 8 février 2013}}
{{Annonce proposition suppression|nom=GrayMatter Recruitment| 7 février 2013}}
{{Annonce proposition suppression|nom=Doorgets|5 février 2013}}
{{Annonce proposition suppression|nom=Java et logiciel libre|4 février 2013}}
{{annonce fusion d'article|28 janvier 2013|[[Visualisation de données]] et [[Représentation graphique]] et [[Représentation graphique de données statistiques]] sur [[Wikipédia:Pages_à_fusionner#Visualisation_de_donn.C3.A9es_et_Repr.C3.A9sentation_graphique_et_Repr.C3.A9sentation_graphique_de_donn.C3.A9es_statistiques|cette page]]}}
{{Annonce proposition suppression|nom=Decostock|26 janvier 2013}}
{{Annonce proposition suppression|nom=Turaz|26 janvier 2013}}
{{Annonce proposition suppression|nom=Medias Sociaux Academy|25 janvier 2013}}
{{Annonce proposition suppression|nom=DigDash|25 janvier 2013}}
{{Annonce proposition suppression|nom=Prodware Innovation & Design|25 janvier 2013}}
{{Annonce proposition suppression|nom=Gironde Logiciels Libres|21 janvier 2013}}
{{Annonce proposition suppression|nom=Twago|20 janvier 2013}}
{{annonce fusion d'article|12 janvier 2013|[[Linguistique informatique]] et [[Traitement automatique du langage naturel]] [[Wikipédia:Pages_à_fusionner#Linguistique_informatique_et_Traitement_automatique_du_langage_naturel|ici]]}} 
{{annonce fusion d'article|12 janvier 2013|proposition fusion [[Agent logiciel]] et [[Agent (informatique)]] [[Wikipédia:Pages_à_fusionner#Agent_logiciel_et_Agent_.28informatique.29|ici]] }}
{{Annonce proposition suppression|nom=Jean-Daniel Fekete| 3 janvier 2013}}
<noinclude>
<!------------------------------- Ci-dessous les modèles d'annonces ------------>

== Modèles d'annonce ==

<div style="width:97%; padding:5px">
{| border="0" style="background-color:inherit; font-size:smaller;"
! scope="col"| <u>type d'annonce</u>
! scope="col"| <u>apparence</u>
! scope="col"| <u>code à insérer</u>
! scope="col"| <u>modèle</u>
|
{{!}}-----
{{!}} ''actualités''
{{!}} {{Annonce actualités|31|texte}}
{{!}} <tt><nowiki>{{Annonce actualités|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} ''discussion ''
{{!}} {{Annonce discussion|30|texte}}
{{!}} <tt><nowiki>{{Annonce discussion|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} ''à vérifier''
{{!}} {{Annonce à vérifier|29|texte}}
{{!}} <tt><nowiki>{{Annonce à vérifier|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} ''à surveiller''
{{!}} {{Annonce à surveiller|28|texte}}
{{!}} <tt><nowiki>{{Annonce à surveiller|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''débats''' ou '''sondages'''
{{!}} {{Annonce vote|27|texte&nbsp;&nbsp;}}
{{!}} <tt><nowiki>{{Annonce vote|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''prises de décision'''
{{!}} {{Annonce prise de décision|26|texte}}
{{!}} <tt><nowiki>{{Annonce prise de décision|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''demandes de suppression d'articles'''
{{!}}<div> 
* {{Annonce proposition suppression |25 |nom=Plog }}
ou
* {{Annonce proposition suppression |25 |nom=Plog|traité }}</div>
{{!}}
* <tt><nowiki>{{Annonce proposition suppression |</nowiki>''date''<nowiki> |</nowiki>nom=''article'' <nowiki> }}</nowiki></tt>
ou
* <tt><nowiki>{{Annonce proposition suppression |</nowiki>''date''<nowiki> |</nowiki>nom=''article'' <nowiki>|traité }}</nowiki></tt>
{{!}} {{m|Annonce proposition suppression}}
{{!}}-----
{{!}} '''annonce de fusion d’articles'''
{{!}} {{Annonce fusion d'article|date|[[Lien annonces sur wp:fusion]] entre [[article 1]] et [[article 2]]}}
{{!}} <tt><nowiki>{{Annonce fusion d'article|date|[[Lien annonces sur wp:fusion]] entre [[article1]] et [[article2]]}}</nowiki>
{{!}} {{m|Annonce fusion d'article}}
{{!}}-----
{{!}} '''nouveaux participants''' au portail
{{!}} {{Annonce utilisateur|24|texte}}
{{!}} <tt><nowiki>{{Annonce utilisateur|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''[[Wikipédia:Articles de qualité|articles de qualité]]'''
{{!}} {{Annonce article de qualité|23|texte}}
{{!}} <tt><nowiki>{{Annonce article de qualité|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''[[Wikipédia:bon article|bon article]]'''
{{!}} {{Annonce bon article|22|texte}}
{{!}} <tt><nowiki>{{Annonce bon article|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''modèles''' spécialisés
{{!}} {{Annonce modèle|21|texte}}
{{!}} <tt><nowiki>{{Annonce modèle|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''images''' pour le projet
{{!}} {{Annonce image|20|texte}}
{{!}} <tt><nowiki>{{Annonce image|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''champagne'''
{{!}} {{Annonce champagne|38|texte}}
{{!}} <tt><nowiki>{{Annonce champagne|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{!}} '''travail''' ou '''chantier'''
{{!}} {{Annonce travail|19|texte}}
{{!}} <tt><nowiki>{{Annonce travail|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''atelier'''
{{!}} {{Annonce atelier|18|texte}}
{{!}} <tt><nowiki>{{Annonce atelier|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} '''traduction'''
{{!}} {{Annonce traduction|17|texte}}
{{!}} <tt><nowiki>{{Annonce traduction|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}} ''autres ...''
{{!}} {{Annonce divers|16|texte}}
{{!}} <tt><nowiki>{{Annonce divers|</nowiki>''jour du mois''<nowiki>|</nowiki>''texte''<nowiki>}}</nowiki></tt>
{{!}}-----
{{!}}}
<center><u>Remarque :</u> Voir aussi les [[:Catégorie:Modèle d'annonce|autres modèles d'annonce spécifiques]].</center></div></noinclude>
"""


if __name__ == "__main__":
	main()
