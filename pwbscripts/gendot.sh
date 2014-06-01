#!/bin/bash


(echo "digraph g { 
	node [ shape = none] 
	overlap=scale " ; grep -- "->" log \
| sed "s/\[\[fr:Catégorie://g" \
| sed 's/ -> /->/'\
| sed 's/ /_/g' \
| sed 's/\]\]//g'\
| sed 's/,/_/g'\
| sed 's/^\([0-9]\)/_\1/g'\
| sed 's/->\([0-9]\)/->\1/g'\
| sed "s/'/_/g" \
| sed "s/é/e/g" \
| sed "s/[()!/\+\.&:]/_/g" \
| sed "s/-\([^>]\)/\1/g" ; echo "}" )> cats.dot

dot -T pdf cats.dot > "cats_$(date).pdf"


