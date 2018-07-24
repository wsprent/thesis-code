#! /usr/bin/env python3
import sys
from gather_tests import (tprint,
                          multicol,
                          print_ending,
                          format_time,
                          format_obj,
                          format_gap,
                          get_max_cuts,
                          get_tests,
                          organize_tests)


def print_max_cut_table(series):
    cols = 5
    tprint("\multirow{2}{*}{Instance}", multicol(2, "$t(s)$"), "\multirow{2}{*}{$GAP$}", "\multirow{2}{*}{$OPT$}",
           line=False)
    tprint("", "MC-1", "MC-25", "", "")

    for sname, tests in series.items():
        tprint(lb=False)
        tprint("", multicol(cols-2, sname), "")
        names = sorted(tests.keys())
        for name in names:
            a, b = get_max_cuts(tests[name])
            tprint(name,
                   format_time(a.mean),
                   format_time(b.mean),
                   format_gap(max(a.gap, b.gap)),
                   format_obj(b.obj) if all((a.opt, b.opt)) else "N/A",
                   line=False)
        tprint("", lb=False)
    print_ending()


def main():
    timings_dir = sys.argv[1] if len(sys.argv) > 1 else "./timings"

    series = organize_tests(get_tests(timings_dir))

    print_max_cut_table(series)


if __name__ == "__main__":
    main()
