#!/bin/bash

#Description: prepare a lua module for edition

source ./config

modulepath="$(modulename "${1}")"

if [ -L "$modulepath" ] ; then
	content=$(cat $modulepath)
	rm "$modulepath"
	echo "$content" >"$modulepath"
fi

ls "$modulepath"
if [ ! -f "$modulepath" ] ; then
	echo "module $1 do not exists, use './getmodule.sh $1' to download"
else 
	editor "$modulepath"
fi

colordiff "$modulepath" "$curversion_path/$1-"*

