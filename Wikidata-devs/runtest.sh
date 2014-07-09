#!/bin/bash


#Description : launches tests on currently edited modules

source config

cd "$testenv_path"

for x in ../*.lua ; do
	ln -sf "$x"
done

for x in "${testcases_path}"/*.lua ; do
	if [ -f "$x" ] ; then
		lua $x
	fi
done

