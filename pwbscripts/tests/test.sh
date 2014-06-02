#! /bin/bash 

export PATH="$PATH:./bash"
PACK_PATH="$(dirname "$(realpath "${0}")")/../.."

cd ..

tests_dir="tests/"

args=("$@")

export PYTHONPATH="${PYTHONPATH}:${PACK_PATH}"
export PWBSCRIPTS_CONFFILE="${PATH_PACK}/pwbscripts/projects.yaml"

echo $PYTHONPATH

if [ "$#" == "0" ] ; then
	trial -r gi "$tests_dir"/test*.py
else
	tests=("$@")
	args=()
	for index in ${!tests[*]}; do
		args[$index]="$tests_dir/${tests[$index]}"
	done
	trial -r gi "${args[@]}"
fi
