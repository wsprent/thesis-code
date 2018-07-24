#! /usr/local/bin/bash

# We assume that the MTP files are at data/MTP/**
# The test cases are placed at data/tests/<series>/file

if [[ ! -z $1 ]]; then
    truncate=$1
else
    truncate=../mtp/truncate_instance.py
fi

function trunc() {
    dir=$1

    file=$2
    [ -e "$file" ] || continue
    mkdir -p $dir
    base=$(basename $file)
    
    if $truncate -f $file -n $3 -e $4 > $dir/$base; then
        echo "truncated $file to $dir/$base"
    else
        echo "something went horribly wrong with $file"
        exit 1
    fi
}

# 100 -> 65 400 -> 85

for file in MTP/JMP/K100*.stp; do
    trunc "tests/JMP-60" $file 60 120
done

for file in MTP/JMP/K400*.stp; do
    trunc "tests/JMP-80" $file 80 170
done

# For completeness sake, we also take the JMP 100 full versions
# mkdir -p tests/JMP-100
# cp MTP/JMP/*100* tests/JMP-100
