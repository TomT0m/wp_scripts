#!/bin/bash
#
#   This file echoes a bunch of color codes to the 
#   terminal to demonstrate what's available.  Each 
#   line is the color code of one forground color,
#   out of 17 (default + 16 escapes), followed by a 
#   test use of that color on all nine background 
#   colors (default + 8 escapes).
#


#Black       0;30     Dark Gray     1;30
#Blue        0;34     Light Blue    1;34
#Green       0;32     Light Green   1;32
#Cyan        0;36     Light Cyan    1;36
#Red         0;31     Light Red     1;31
#Purple      0;35     Light Purple  1;35
#Brown       0;33     Yellow        1;33
#Light Gray  0;37     White         1;37

Black='0;30m'
Dark_Gray='1;30m'
Blue="0;34m" 
Light_Blue="1;34m"
Green='0;32m'
Light_Green="1;32m"
Cyan='0;36m'
Light_Cyan='1;36m'
Red='0;31m' 
Light_Red='1;31m';
Purpler='0;35m'
Light_Purpler="1;35m"
Brown="0;33m" 
Yellow='1;33m'
Light_Gray='0;37m' 
White='1;37m'


BG_Black='40m'
BG_='41m'
BG_='42m'
BG_='43m'
BG_Blue='44m'
BG_Purpler='45m'
BG_Light_Cyan='46m'
BG_White='47m'

T='gYw'   # The test text

function colors_by_num() {
	
	T='gYw'   # The test text
	echo -e "\n                 40m     41m     42m     43m     44m     45m     46m     47m";

	for FGs in '    m' '   1m' '  30m' '1;30m' '  31m' '1;31m' '  32m' \
           '1;32m' '  33m' '1;33m' '  34m' '1;34m' '  35m' '1;35m' \
           '  36m' '1;36m' '  37m' '1;37m';
  		do FG=${FGs// /}
  		echo -en " $FGs \033[$FG  $T  "
  		for BG in 40m 41m 42m 43m 44m 45m 46m 47m;
    			do echo -en "$EINS \033[$FG\033[$BG  $T  \033[0m";
  		done
  		echo;
	done
	echo
}

function echo_color() {
	local FG="$1"
	local msg="$2"

  	echo -en "\033[${FG}"
	echo -en "$EINS\033[${FG}\033[${BG_Light_Cyan}${msg}\033[0m";
	echo
	#echo
}

function colored_colors() {
	for x in $(colors) ;
		do echo_color "${!x}" "$x" ; echo
	done	
}

function colors () {
	echo Black Dark_Gray Blue Light_Blue Green Light_Green Cyan Light_Cyan Red Light_Red Purpler Light_Purpler Brown Yellow Light_Gray White 
}

function echo_n () {
	local n="$1"
	local string="$2"

	for x in $(seq 1 $n) ; do
		echo -n "$string"
	done
}


function colors_by_name () {
	local max_len=13
	echo -e $(colors) ;

	for FGs in $(colors) ;
	  do # FG=${FGs// /}
		FG=${!FGs}
		local Len=$(echo "$FGs" | wc -c)
 		echo_n $((max_len-Len)) " "
	  	echo -en " $FGs \033[$FG  $T  "
	  	for BG in 40m 41m 42m 43m 44m 45m 46m 47m;
	    		do echo -en "$EINS \033[$FG\033[$BG  $FGs  \033[0m";
	  	done
	  	echo;
	done
	echo
}
