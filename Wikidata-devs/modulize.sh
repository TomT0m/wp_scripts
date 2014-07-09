#!/bin/bash

#Description: prepare edit environment 

source ./config

for module in ${stub_path}/*.lua ; do
	ln -sf "$module" "Module:$(basename $module .lua).lua" 
done

#for module in ${curversion_path}/*.lua ; do
#	ln -s "$module" "${testenv_path}/Module:$(basename $module .lua).lua"
#done

for module in $(cat module_list) ; do
	echo_color "$White" "modulizing module <$module> ..."
	./getmodule.sh "$module"
done
