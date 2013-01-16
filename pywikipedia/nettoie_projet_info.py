#! /usr/bin/python
# -*- coding: UTF-8 -*-
"""
#Description: Déplace les annonces de proposition de suppression de la page Projet:Informatique vers la page d'annonces
"""

from __future__ import unicode_literals
import re, logging
from functools import total_ordering

import wikipedia



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
	def __repr__(self):
		return u"{:2d} {} {:4d}".format(self.jour, self.MOIS[self.mois], self.annee)

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

def extract_announces(text):
	""" Takes wikicode, returns a pair 
	([(title(str), Date)*], newtext)
	"""
	pattern = u"""(== L'article {} est proposé à la suppression ==$\n^(.*$\n^)*?.*{}){}"""
	articles = []
	del_sum = 0
	
	end_marker = "((CET.*)|(?=^==))"
	new_msg_marker = ".*$(\n^==|(?!\n^.)|(?!\n))"

	for article in re.finditer(pattern.format(u'(.*)', end_marker, new_msg_marker), text, re.MULTILINE):
		date = extract_date(article.group(1))
		articles.append((article.group(2), date))
		del_sum += len(article.group(0))
	
		logging.info(" Article : {} (annoncé le {})".format(article.group(2), date))
		logging.info(" Annonce : \n'''{}'''".format(article.group(1)))
	
	del_pattern = pattern.format('.*', end_marker, new_msg_marker)
	newpage = re.sub(del_pattern, '', text, flags = re.MULTILINE)


	logging.debug("(taille en octets) : Supprimé {} - nouvelle : {}, ancienne {}, différence {}: ".format(del_sum, 
						     len(newpage), 
						     len(text), 
						     del_sum-(len(text) - len(newpage))))
	
	return (articles, newpage)

def format_del_announce(date, article_name):
	""" returns a mediawiki template text for a deletion announce"""
	return u"{{Annonce proposition suppression|nom=" +\
		article_name+u"|"+\
		repr(date)+ u"}}"

def insert_new_announces(old_text, to_del_list):
	""" Creates a text with to_del_list announces inserted at timely sorted"""
	
	
	# découpage en utilisant les marqueurs de la section annonces dans la page
	

	sep_preamble = "------->"
	sep_end = "<noinclude>"
	
	(preamble, following ) = old_text.split( sep_preamble, 1)
	(section_annonces, rest) = following.split( sep_end, 1 )

	# prétraitement des annonces : création d'une liste de couple (template, Date)
	announces_lines = section_annonces.split("\n")
	
	dated_old_announces = [ (text, extract_date(text)) 
			for text in announces_lines if text != ""]
	dated_new_announces = [ (format_del_announce(date, name), date) 
			for name, date in to_del_list]
	
	# tri par date
	sorted_announces = sorted( dated_old_announces + dated_new_announces, 
			   key = lambda (_, date): date, reverse = True)

	# création de la section finale

	new_section = "\n".join([ text for text, _ in sorted_announces])

	return preamble + sep_preamble + new_section + sep_end + rest

def deletion_prop_maintenance(base_name, simulate = False):
	""" Real Action """

	# Récupération des données #
	
	pagename = u"Discussion {}".format(base_name)
	announces_pagename = "{}/Annonces".format(base_name)

	site = wikipedia.getSite("fr")
	
	
	discussion_page = wikipedia.Page(site, pagename, defaultNamespace = "Discussion")
	discussion_text = discussion_page.get(get_redirect = True)

	announces_page = wikipedia.Page(site, announces_pagename)
	announces_text = announces_page.get(get_redirect = True )
	
	# Traitements #

	# récupération des annonces noyées dans la PDD
	#
	(articles, new_discussion_text) = extract_announces(discussion_text)

	# stats sur le diff entre page générée et page originale
	logging.info("Before : {} ; After {} ; expected around {}".format(len(discussion_text),
							    len(new_discussion_text),
							    len(discussion_text) - len(articles) * 1200))
	logging.info("Articles extraits")
	for elem  in articles :
		(nom, date) = elem
		logging.info(u"Date d'annonce : {} ; Article à supprimer : {}".format(date, nom))
	
	# insertions des annonces extraites dans la page d'annonce
	new_announces_text = insert_new_announces(announces_text, articles)
	print("> Diff des Annonces <\n")
	wikipedia.showDiff(announces_text, new_announces_text)
	
	print("> Diff PDD <\n")
	wikipedia.showDiff(discussion_text, new_discussion_text)
	
	# Sauvegarde éventuelle #
	if not simulate:
		discussion_page.put(new_discussion_text)
		announces_page.put(new_announces_text)

from argparse import ArgumentParser

def create_options():
	""" Script option parsing """
	options = ArgumentParser()

	options.add_argument('-s', '--simulate', action='store_false', 
		    help = "don't save changes", dest = "simulate")
	options.add_argument('-t', '--test', action='store_true', 
		    help = "run tests", dest = "test")
	options.add_argument('-p', '--page', 
		    help = "run tests", metavar="PAGE", dest = "page",
		    default = "Projet:Informatique")
	
	return options


#############################################################
# testing

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
import unittest
import sys

class Test(unittest.TestCase):
	""" Test cases : test of deletion proposition extraction"""
	def test_extraction(self):
		""" Simple test """
		text = SAMPLE_TEXT
		(articles, new_text) = extract_announces(text)
		self.assertTrue("Feteke" not in new_text)
		(nom, date) = articles[0]
		self.assertEqual(nom, "Jean-Daniel Fekete")
		self.assertEqual(date, Date(3, "janvier", 2013))
	
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
	
	if opts.test:
		test()
	else:
		# paramètres par defaut : "Projet:Informatique", False
		deletion_prop_maintenance(opts.page, opts.simulate)

if __name__ == "__main__":
	main()

