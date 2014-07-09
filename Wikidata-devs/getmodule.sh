#!/bin/bash

#Description: Downloads a Mediawiki Lua module ($1 : modulename ;$2 : mediawiki site)

source ./config

site="test.wikidata.org"
module="$1"


if [ ! -z "$2" ] ; then
	site="$2"
fi

if [ ! -f ./jsawk ] ; then
	curl -s -L http://github.com/micha/jsawk/raw/master/jsawk > jsawk
	chmod +x jsawk
fi


apiurl="https://${site}/w/api.php?action=query"
moduleapi="${apiurl}&titles=Module:${module}"

revision=$(curl -s "${moduleapi}&indexpageids&format=json" | ./jsawk 'return this.query.pageids[0]')

revisionfile_path="${curversion_path}/${module}-${revision}.lua"
modulelocalname="$(modulename "$1")"

# if we don't have last revision yet, then download it and replace old one.

if [ ! -e "${revisionfile_path}" ] ; then 
	
	if [ -e ${curversion_path}/${module}-*.lua ] ; then 
		mv ${curversion_path}/${module}-*.lua ${oldversions_path}
	fi

	curl -s "http://${site}/w/index.php?action=raw&title=Module:${module}" > ${revisionfile_path}
	
	if [ -L "${modulelocalname}" ] ; then
		ln -sf ${revisionfile_path} "${modulelocalname}"
	fi
fi

# recreation if deleted

if [ ! -e "${modulelocalname}" ] ; then
	ln -sf ${revisionfile_path} "${modulelocalname}"
fi


