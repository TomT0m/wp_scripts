#!/bin/bash

#Description: Generate testcase page from a list of template testcases
echo "{|width=100%
|+testcase table
||-
|! Now 
|! Sandbox version 
||}
"

echo "
<!-- generated with a script findable on https://github.com/TomT0m/wp_scripts  / wp_scripts/gen_testcases.sh 

From the list of calls findable on this page (one example call per line)

-->
"

while read line ; do
	 cat <<EOF 
{|width=100% class="wikitable" style="table-layout: fixed;"
|+ $(echo "$line"|sed "s/{{/{{tlp|/")
|-
| $line
| $(echo "$line"|sed "s@|@/sandbox|@")
|}
EOF
done

