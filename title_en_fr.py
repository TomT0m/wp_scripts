#! /usr/bin/python
#encoding: utf-8
"""
#Description: takes an english title and translates it into french
"""

from pywikidata.wikidata import api 
import sys

def main():
	""" main """
	title = sys.argv[1]

	item = api.getItemByInterwiki ("enwiki", title )
	print("getting item {} for title {} ".format(item, title))

	#for label in item.labels:
	#	print(item.labels[label]) 

	print(item.labels["fr"])

if __name__ == "__main__":
	main()

