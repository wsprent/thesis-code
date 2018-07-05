#! /usr/bin/env bash

if [[ ! -z $1 ]]; then
    convert=$1
else
    convert=../mtp/convert.py
fi

for file in PCSTP/*/*; do
    [ -e "$file" ] || continue

    ending=$(echo $file|cut -d'/' -f2-)
    folders=$(dirname $ending)
    mkdir -p MTP/$folders
    if $convert $file > MTP/$ending; then
        echo "converted $file to MTP/$ending"
    else
        echo "something went horribly wrong with $file"
        exit 1
    fi
    
done
    
