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

        self.gap = max((self.obj - self.bound) / self.obj, 0)
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
            elif opt == "s":
                self.strengthen = False
            elif opt == "s+":
                self.strengthen = True

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


def format_time(tc, lim=-float("inf")):
    num = "{:.5g}".format(tc.mean)
    if not tc.opt:
        num = "\\mathit{" + num + "}^*"
    elif tc.mean <= lim:
        num = "\\mathbf{" + num + "}"
    return "$" + num + "$"


def format_times(*args):
    minarg = min(args, key=lambda tc: tc.mean)
    return map(lambda x: format_time(x, minarg.mean), args)


def format_obj(*tc):
    for t in tc:
        if t.opt:
            return "${:.2f}$".format(t.obj)
    return "$\\mathit{:.2f}^*$".format(min(tc, key=lambda x: x.obj).obj)


def format_gap(g):
    string = "{:.2%}".format(g)
    if g < 10e-6:
        string = "\\mathbf{" + string + "}"
    return ("$" + string + "$").replace("%", "\\%")


def multicol(n, s):
    return "\multicolumn{{{}}}{{|c|}}{{{}}}".format(n, s)


def print_ending():
    print("""
%%%
%%% Local Variables:
%%% TeX-master: "report"
%%% reftex-default-bibliography: ("lit.bib")
%%% End:
    """)


def get_max_cuts(tcs):

    for t in tcs:
        if t.heuristics or t.strengthen:
            continue
        if t.max_cuts == 0:
            zero = t
        elif t.max_cuts == 1:
            one = t
        elif t.max_cuts == 25:
            tf = t
    return zero, one, tf


def get_heuristics(tcs, mc):

    for t in tcs:
        if not t.max_cuts == mc and not t.strengthen:
            continue
        if t.heuristics:
            plus = t
        else:
            minus = t
    return minus, plus


def get_strengthen(tcs, mc):
    for t in tcs:
        if t.heuristics or not t.max_cuts == mc:
            continue
        if t.strengthen:
            plus = t
        else:
            minus = t
    return minus, plus
