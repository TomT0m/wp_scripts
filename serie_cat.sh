#!/bin/bash

# pywikidir="$(dirname $0)/pywiki/core/scripts/"

annee="$1"

export PATH="$PATH:$pywikidir"

wp listpages  -- -catr:'Category:${annees}_American_television_series' -lang:en -family:wikipedia 	| awk -F':' '{ print $2 }' | \
        while read serie_name ; do
		serie=$(echo $(echo "$serie_name"|awk -F'(' '{print $1}'));
            	page="$serie_name";

	    	echo -e "\n\n>>>>>>>>>>>>>>>>>>> ============================ <$serie> , <$page> =============================" 
			wp set_serie_labels -p "$page" "$serie";
        done
