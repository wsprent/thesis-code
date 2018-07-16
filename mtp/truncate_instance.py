#! /usr/bin/env python3

import networkx as nx
import gurobipy as grb
import numpy as np

import random
import sys
import argparse
import itertools

import mtp
from stp import load_mtp, write_stp


DESCRIPTION = """
 Converts an STP PCSTP instance to a MTP instance using various methods:
 --
"""
INF = float('inf')


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument("-f", help="The mtp instance as a stp file")
    parser.add_argument("--nodes", "-n", help="Desired number of nodes", type=int)
    parser.add_argument("--edges", "-e", help="Desired number of edges", type=int)

    args = parser.parse_args()

    if args.f is not None:
        with open(args.f) as fp:
            g, int_only = load_mtp(fp)
    else:
        g, int_only = load_mtp(sys.stdin)

    gp = mtp.truncate(g, args.nodes, args.edges)
    write_stp(gp)


if __name__ == "__main__":
    main()
