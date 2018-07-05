#! /usr/bin/env bash

CURDIR=$(pwd)
cd $TMPDIR

function dimacs() {
    name=$1
    mkdir -p $CURDIR/PCSTP/$name
    curl http://dimacs11.zib.de/instances/PCSPG-$name.zip -o PCSPG-$name.zip
    unzip PCSPG-$name.zip
    mv PCSPG-$name/* $CURDIR/PCSTP/$name    
}

dimacs JMP
dimacs CRR
dimacs PUCNU

