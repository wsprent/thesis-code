#! /usr/bin/env python3

import sys
import os
import operator

from functools import reduce

ST = {"2": "OPT", "9": "TIMEOUT"}


class TestCase(object):

    _time = None
    _var = None

    heuristics = None
    max_cuts = None

    def __init__(self, runs, path):

        self.opt = True
        self.n = len(runs)

        times = []

        self.V = runs[0][0] if reduce(operator.__eq__, (n for n, *_ in runs)) else None
        self.E = runs[0][1] if reduce(operator.__eq__, (m for _, m, *_ in runs)) else None

        self.bound = float("inf")
        for n, m, st, t, b, v in runs:

            self.obj = v
            self.bound = min(self.bound, b)

            if st != "OPT":
                self.opt = False

            times.append(t)

        self.times = times

        # xxxx/timings/series-size-keys

        exploded = path.split("/")

        series_with_keys, test = exploded[exploded.index("timings")+1:]

        # Extract options and series

        exploded = series_with_keys.split("-")

        self.series = "-".join(exploded[:2])

        for opt in exploded[2:]:

            if opt.startswith("MC"):
                self.max_cuts = int(opt[2:])
            elif opt == "h":
                self.heuristics = False
            elif opt == "h+":
                self.heuristics = True

        # Extract Name

        exploded = test.split(".")
        stp = exploded.index("stp")

        self.name = ".".join(exploded[:stp])

    @property
    def mean(self):
        if self._time is not None:
            return self._time

        self._time = sum(self.times) / self.n
        return self.mean

    @property
    def var(self):
        if self._var is not None:
            return self._var

        self._var = sum((t - self.mean)**2 for t in self.times) / self.n
        return self.var


def read_test(path):
    runs = []
    with open(path) as f:
        for line in f:
            n, m, st, t, b, v = line.split()

            runs.append((int(n), int(m), ST[st], float(t), float(b), float(v)))

    return TestCase(runs, path)


def get_tests(path):
    for dirpath, dirnames, filenames in os.walk(path):
        tests = [f for f in filenames if "stp" in f]

        if len(tests) == 0:
            continue

        for testp in tests:
            yield read_test(os.path.join(dirpath, testp))


def organize_tests(tests):
    series = {}
    for test in tests:

        if test.series not in series:
            series[test.series] = {}

        series_dict = series[test.series]
        if test.name not in series_dict:
            series_dict[test.name] = []
        series_dict[test.name].append(test)

    return series


def tprint(*args, line=True, lb=True, **kwargs):
    hline = "\\hline" if line else ""
    lb = " \\\\" if lb else " "
    end = lb + hline + "\n"
    print(*args, sep=" & ", end=end, **kwargs)


def multicol(n, s):
    return "\multicolumn{{{}}}{{|c|}}{{{}}}".format(n, s)


def get_max_cuts(tcs):

    for t in tcs:
        if not t.heuristics:
            continue
        if t.max_cuts == 10:
            ten = t
        elif t.max_cuts == 50:
            fifty = t
        elif t.max_cuts == 150:
            onefifty = t
    return ten, fifty, onefifty


def format_time(t):
    return "${:.5g}$".format(t)


def format_obj(t):
    return "${:.2f}$".format(t)


def print_max_cut_table(series):

    cols = 5
    tprint("\multirow{2}{*}{Instance}", multicol(3, "$t(s)$"), "\multirow{2}{*}{$OPT$}",
           line=False)
    tprint("", "MC-10", "MC-50", "MC-150", "")

    for sname, tests in series.items():
        tprint(lb=False)
        tprint("", multicol(cols-2, sname), "")
        names = sorted(tests.keys())
        for name in names:
            a, b, c = get_max_cuts(tests[name])
            tprint(name,
                   format_time(a.mean),
                   format_time(b.mean),
                   format_time(c.mean),
                   format_obj(c.obj) if all((a.opt, b.opt, c.opt)) else "N/A",
                   line=False)
        tprint("", lb=False)
    print("""
%%%
%%% Local Variables:
%%% TeX-master: "report"
%%% reftex-default-bibliography: ("lit.bib")
%%% End:
    """)


def main():
    timings_dir = sys.argv[1] if len(sys.argv) > 1 else "./timings"

    series = organize_tests(get_tests(timings_dir))

    print_max_cut_table(series)



if __name__ == "__main__":
    main()
