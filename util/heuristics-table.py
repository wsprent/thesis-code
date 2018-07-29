#! /usr/bin/env python3
import sys
from gather_tests import (tprint,
                          multicol,
                          print_ending,
                          format_time,
                          format_times,
                          format_obj,
                          format_gap,
                          get_heuristics,
                          get_tests,
                          organize_tests)


def print_heuristics_table(series):
    cols = 5
    tprint("\multirow{2}{*}{Instance}", multicol(2, "$t(s)$"), "\multirow{2}{*}{$GAP$}", "\multirow{2}{*}{$OPT$}",
           line=False)
    tprint("", "Gurobi", "Custom", "", "")

    for sname, tests in series.items():
        tprint(lb=False)
        tprint("", multicol(cols-3, sname), "", "")
        names = sorted(tests.keys())
        for name in names:
            a, b = get_heuristics(tests[name], mc=25)
            tprint(name,
                   *format_times(a, b),
                   format_gap(max(a.gap, b.gap)),
                   format_obj(a, b),
                   line=False)
        tprint("", lb=False)
    print_ending()


def main():
    timings_dir = sys.argv[1] if len(sys.argv) > 1 else "./timings"

    series = organize_tests(get_tests(timings_dir))

    print_heuristics_table(series)


if __name__ == "__main__":
    main()
