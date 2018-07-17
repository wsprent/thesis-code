#! /usr/local/bin/bash

# We assume that the MTP files are at data/MTP/**
# The test cases are placed at data/tests/<series>/file

if [[ ! -z $1 ]]; then
    truncate=$1
else
    truncate=../mtp/truncate_instance.py
fi

# We want 35/50/70 node versions of the JMP series
for size in 35 50 70; do
    dir=tests/JMP-$size
    mkdir -p $dir
    edges=$[$size*3]
    for file in MTP/JMP/*; do
        [ -e "$file" ] || continue
        base=$(basename $file)

        if $truncate -f $file -n $size -e $edges > $dir/$base; then
            echo "truncated $file to $dir/$base"
        else
            echo "something went horribly wrong with $file"
            exit 1
        fi
    done
done

# For compleness sake, we also take the JMP full versions

cp MTP/JMP tests/JMP-FULL
