#!/bin/bash

# pywikidir="$(dirname $0)/pywiki/core/scripts/"

if [ "$1" == '-c' ] ; then
	category="$2"
else
	annees="$1"
	category="Category:${annees}s_American_television_series" 
fi

export PATH="$PATH:$pywikidir"

function title {
    echo -en "\033]2;$1\007"
}

label=$(echo $category | cut -d":" -f2-)
title "$label"

#LOG_SERIES_WITH_

wp listpages  -- "-catr:$category" -lang:en -family:wikipedia 	| awk -F':' '{ print $2 }' | \
	while read serie_name ; do
		serie=$(echo $(echo "$serie_name"|awk -F'(' '{print $1}'));
		
		meta=""
		if [[ "$serie_name" == *\(* ]] ; then
	    		
			meta="$(echo "$serie_name" | cut -d'(' -f2- )"
			
			#what's into the parenthesis
		fi

		if [[ -z $meta || "$meta" == *TV* || "$meta" == *[sS]eries* ]] ; then
			
			page="$serie_name";
		
			title "$serie (${label})"
	    	
			journal_log "Doing article $page" "cmd=$0 $*" "article=$serie" --codefile "$0" 
			
			echo -e "\n\n>>>>>>>>>>>>>>>>>>> ============================ <$serie> , <$page>, <$meta> =============================" 
				wp set_serie_labels -p "$page" "$serie";
		else
			echo -e "\n>>>>>Skipping $page (<$meta> did not pass)\n"
			journal_log "Skipping, do not match: <$page>" "cmd=$0 $*" "article=$serie"  --codefile "$0"
		fi
	done
