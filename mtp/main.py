#! /usr/bin/env python3

import networkx as nx
import gurobipy as grb
import numpy as np

import argparse
import itertools

from pcst_fast import pcst_fast

from stp import load_mtp

DESCRIPTION = """
 Solves an instance of the MTP using Gurobi Python.
"""

BIG_INT = np.iinfo(np.int64).max
BIG_FLOAT = np.finfo(np.float64).max
EPSILON = 10**(-9)
MAX_CUTS = 1


def main():
    parser = argparse.ArgumentParser(description=DESCRIPTION)

    parser.add_argument('mtp', help='The MTP instance as a stp file')

    args = parser.parse_args()

    g, int_only = load_mtp(args.mtp)


if __name__ == '__main__':
    main()
