#! /usr/bin/python
#coding: utf-8
"""
Annonces des processus de fusion en cours pour un projet

#Description: Extraire les articles d'informatique faisant l'objet d'une procédure de fusion


"""

import catlib, wikipedia

def create_lister():
	""" factory function for an iterator on a 
	"""
	already_listed = set()
	
	class Counter(object):
		""" stupid boxing class"""
		def __init__(self):
			self.subcat_d = 0
	
	plop = Counter()

	
	def all_articles(cat):
		""" plop """
		already_listed.add(cat)
		queue = []
		queue.append(cat)
		while len(queue) > 0:
			cat = queue.pop()
			for article in cat.articles():
				if article not in already_listed:
					already_listed.add(article)
					yield article
		
			for subcat in cat.subcategories():
				print("{} -> {}".format(cat, subcat))
				if subcat not in already_listed:
					already_listed.add(subcat)
					queue.append(subcat)
	
		# wikipedia.output(u'\nARTICLES:')
	return all_articles

def main():
	""" main function """
	cat = catlib.Category(site="fr", title = "Informatique")

	bidou = create_lister()
	for art in bidou(cat):
		print("========================", art)

if __name__ == "__main__":
	main()

