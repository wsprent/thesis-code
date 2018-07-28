#! /usr/bin/env bash

if [[ -z $1 ]]; then
    echo "no args"
    exit 1
fi

name=$1

util/${name}-table.py timings/ > ~/repos/final-boss/report/${name}-table.tex && cat ~/repos/final-boss/report/${name}-table.tex
