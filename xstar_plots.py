#!/usr/bin/env python3
import collections
import glob
import matplotlib
import re
from functools import reduce

import plot_styling as ps
from matplotlib import pyplot as plt
from shared_helpers import XStarData
from shared_helpers import MStarData
from shared_helpers import CBSData
from shared_helpers import AFSData

FileData = collections.namedtuple('FileData', ['filename',
                                               'agents',
                                               'iter',
                                               'trial',
                                               'seed'])
kTimeout = 1200


def filename_to_filedata(l):
    l_orig = l
    l = l.replace("_density_0.1", "")
    l = l.replace("_density_0.05", "")
    l = l.replace("_density_0.01", "")
    regex = r"[a-zA-Z_\/]*(\d\d\d|\d\d|\d)_iter_(\d\d\d|\d\d|\d)_trial_(\d\d\d|\d\d|\d)_seed_(\d\d\d\d\d\d|\d\d\d\d\d|\d\d\d\d|\d\d\d|\d\d|\d).result" # noqa
    matches = list(re.finditer(regex, l, re.MULTILINE))
    match = None
    try:
        match = matches[0]
    except:
        print(l)
        exit(-1)
    agents = int(match.group(1))
    itr = int(match.group(2))
    trial = int(match.group(3))
    seed = int(match.group(4))
    return FileData(l_orig, agents, itr, trial, seed)


def get_line(ls, string, t):
    string = string.strip()
    if string[-1] != ':':
        string += ':'
    fls = [l for l in ls if string in l]
    if len(fls) > 1:
        print(string, "is not unique")
    elif len(fls) < 1:
        print(string, "is not found")
    assert(len(fls) == 1)
    line = fls[0]
    line = line.replace(string, '').replace(':', '').strip()
    return t(line)


def get_total_first_plan_time(filename, timeout=kTimeout):
    ls = open(filename, 'r').readlines()
    if len(ls) == 0:
        return timeout
    time_individual_plan = get_line(ls, "time_individual_plan", float)
    time_first_plan = get_line(ls, "time_first_plan", float)
    return time_individual_plan + time_first_plan


def get_optimal_time_or_timeout(filename, timeout):
    ls = open(filename, 'r').readlines()
    if len(ls) == 0:
        return timeout
    if get_line(ls, "is_optimal", bool):
        return get_line(ls, "Total time", float)
    else:
        return timeout


def get_field(filename, field, t, default):
    ls = open(filename, 'r').readlines()
    if len(ls) == 0:
        return default
    return get_line(ls, field, t)


def get_ci(data, percentile):
    percentile = percentile / 100.0
    assert(percentile <= 1.0 and percentile > 0)
    data.sort()
    diff = (1.0 - percentile) / 2.0
    high_idx = int((1.0 - diff) * (len(data) - 1))
    mid_idx = int(0.5 * (len(data) - 1))
    low_idx = int(diff * (len(data) - 1))
    high = data[high_idx]
    mid = data[mid_idx]
    low = data[low_idx]
    return (high, mid, low)


def get_percentile(data, percentile):
    percentile = percentile / 100.0
    assert(percentile <= 1.0 and percentile > 0)
    data.sort()
    high_idx = int(percentile * (len(data) - 1))
    low_idx = 0
    high = data[high_idx]
    low = data[low_idx]
    return (high, low)


def add_to_dict(acc, e):
    lst = acc.get(e[0], [])
    lst.append(e[1])
    acc[e[0]] = lst
    return acc


idv_file_datas = \
    [filename_to_filedata(f) for f in glob.glob('datasave/xstar*.result')]
idv_file_datas = [e for e in idv_file_datas if e.agents <= 60]
agents_first_times_lst = \
    sorted([(d.agents, get_total_first_plan_time(d.filename))
            for d in idv_file_datas])
agents_optimal_times_lst = \
    sorted([(d.agents, get_optimal_time_or_timeout(d.filename, kTimeout))
            for d in idv_file_datas])
num_agents_in_window_optimal_times_lst = \
    sorted([(get_field(d.filename, "num_max_agents_in_window", int, None),
             get_optimal_time_or_timeout(d.filename, kTimeout)) for d in idv_file_datas
            if get_field(d.filename, "num_max_agents_in_window", int, None)
            is not None])
num_agents_in_window_first_times_lst = \
    sorted([(get_field(d.filename, "num_max_agents_in_window_first_iteration", int, None),
            get_total_first_plan_time(d.filename)) for d in idv_file_datas
            if get_field(d.filename, "num_max_agents_in_window_first_iteration", int, None) is not None])

ratio_file_datas = \
    [filename_to_filedata(f)
     for f in glob.glob('datasave/xstar_ratio_*.result') if "1200" not in f]
ratio_timeout_dict = {20: 300, 30: 450, 40: 600, 60: 900, 80: 1200}
ratio_agents_first_times_lst = \
    sorted([(d.agents, get_total_first_plan_time(d.filename))
            for d in ratio_file_datas])
ratio_agents_optimal_times_lst = \
    sorted([(d.agents, get_optimal_time_or_timeout(d.filename, kTimeout))
            for d in ratio_file_datas])

def read_from_file(name):  
    f = open("{}".format(name), 'r')
    data = eval(f.read())
    f.close()
    return data


def get_first_runtimes(data):
    return data.runtimes[0]


xstar_datas_density_01 = [read_from_file(f) for f in glob.glob('datasave/xstar_data_lst_*density0.01*')]
xstar_datas_density_01 = [x for lst in xstar_datas_density_01 for x in lst]
xstar_agents_first_times_density_01 = [(x.num_agents, x.runtimes[0]) for x in xstar_datas_density_01]
xstar_agents_optimal_times_density_01 = [(x.num_agents, x.runtimes[-1]) for x in xstar_datas_density_01]

cbs_datas_density_01 = [read_from_file(f) for f in glob.glob('datasave/cbs_data_lst_*density0.01*')]
cbs_datas_density_01 = [x for lst in cbs_datas_density_01 for x in lst]
cbs_agents_times_density_01 = [(x.num_agents, x.runtimes) for x in cbs_datas_density_01]

afs_datas_density_01 = [read_from_file(f) for f in glob.glob('datasave/afs_data_lst_*density0.01*')]
afs_datas_density_01 = [x for lst in afs_datas_density_01 for x in lst]
afs_agents_first_times_density_01 = [(x.num_agents, x.runtimes[0]) for x in afs_datas_density_01]
afs_agents_optimal_times_density_01 = [(x.num_agents, x.runtimes[-1]) for x in afs_datas_density_01]

mstar_datas_density_01 = [read_from_file(f) for f in glob.glob('datasave/mstar_data_lst_*density0.01*')]
mstar_datas_density_01 = [x for lst in mstar_datas_density_01 for x in lst]
mstar_agents_times_density_01 = [(x.num_agents, x.runtimes) for x in mstar_datas_density_01]

xstar_datas_density_05 = [read_from_file(f) for f in glob.glob('datasave/xstar_data_lst_*density0.05*')]
xstar_datas_density_05 = [x for lst in xstar_datas_density_05 for x in lst]
xstar_agents_first_times_density_05 = [(x.num_agents, x.runtimes[0]) for x in xstar_datas_density_05]
xstar_agents_optimal_times_density_05 = [(x.num_agents, x.runtimes[-1]) for x in xstar_datas_density_05]

cbs_datas_density_05 = [read_from_file(f) for f in glob.glob('datasave/cbs_data_lst_*density0.05*')]
cbs_datas_density_05 = [x for lst in cbs_datas_density_05 for x in lst]
cbs_agents_times_density_05 = [(x.num_agents, x.runtimes) for x in cbs_datas_density_05]

afs_datas_density_05 = [read_from_file(f) for f in glob.glob('datasave/afs_data_lst_*density0.05*')]
afs_datas_density_05 = [x for lst in afs_datas_density_05 for x in lst]
afs_agents_first_times_density_05 = [(x.num_agents, x.runtimes[0]) for x in afs_datas_density_05]
afs_agents_optimal_times_density_05 = [(x.num_agents, x.runtimes[-1]) for x in afs_datas_density_05]

mstar_datas_density_05 = [read_from_file(f) for f in glob.glob('datasave/mstar_data_lst_*density0.05*')]
mstar_datas_density_05 = [x for lst in mstar_datas_density_05 for x in lst]
mstar_agents_times_density_05 = [(x.num_agents, x.runtimes) for x in mstar_datas_density_05]

xstar_datas_density_1 = [read_from_file(f) for f in glob.glob('datasave/xstar_data_lst_*density0.1*')]
xstar_datas_density_1 = [x for lst in xstar_datas_density_1 for x in lst]
xstar_datas_density_1 = [x for x in xstar_datas_density_1 if int(x.num_agents) <= 60]
xstar_agents_first_times_density_1 = [(x.num_agents, x.runtimes[0]) for x in xstar_datas_density_1]
xstar_agents_optimal_times_density_1 = [(x.num_agents, x.runtimes[-1]) for x in xstar_datas_density_1]

cbs_datas_density_1 = [read_from_file(f) for f in glob.glob('datasave/cbs_data_lst_*density0.1*')]
cbs_datas_density_1 = [x for lst in cbs_datas_density_1 for x in lst]
cbs_datas_density_1 = [x for x in cbs_datas_density_1 if int(x.num_agents) <= 60]
cbs_agents_times_density_1 = [(x.num_agents, x.runtimes) for x in cbs_datas_density_1]

afs_datas_density_1 = [read_from_file(f) for f in glob.glob('datasave/afs_data_lst_*density0.1*')]
afs_datas_density_1 = [x for lst in afs_datas_density_1 for x in lst]
afs_datas_density_1 = [x for x in afs_datas_density_1 if int(x.num_agents) <= 60]
afs_agents_first_times_density_1 = [(x.num_agents, x.runtimes[0]) for x in afs_datas_density_1]
afs_agents_optimal_times_density_1 = [(x.num_agents, x.runtimes[-1]) for x in afs_datas_density_1]

mstar_datas_density_1 = [read_from_file(f) for f in glob.glob('datasave/mstar_data_lst_*density0.1*')]
mstar_datas_density_1 = [x for lst in mstar_datas_density_1 for x in lst]
mstar_datas_density_1 = [x for x in mstar_datas_density_1 if int(x.num_agents) <= 60]
mstar_agents_times_density_1 = [(x.num_agents, x.runtimes) for x in mstar_datas_density_1]

constant_density_agents = [20, 40, 80, 160, 320]

xstar_datas_density_const = [read_from_file(f) for f in glob.glob('datasave/xstar_data_lst_*density0.1*')]
xstar_datas_density_const = [x for lst in xstar_datas_density_const for x in lst]
xstar_datas_density_const = [x for x in xstar_datas_density_const if int(x.num_agents) in constant_density_agents]
xstar_agents_first_times_density_const = [(x.num_agents, x.runtimes[0]) for x in xstar_datas_density_const]
xstar_agents_optimal_times_density_const = [(x.num_agents, x.runtimes[-1]) for x in xstar_datas_density_const]

cbs_datas_density_const = [read_from_file(f) for f in glob.glob('datasave/cbs_data_lst_*density0.1*')]
cbs_datas_density_const = [x for lst in cbs_datas_density_const for x in lst]
cbs_datas_density_const = [x for x in cbs_datas_density_const if int(x.num_agents) in constant_density_agents]
cbs_agents_times_density_const = [(x.num_agents, x.runtimes) for x in cbs_datas_density_const]

afs_datas_density_const = [read_from_file(f) for f in glob.glob('datasave/afs_data_lst_*density0.1*')]
afs_datas_density_const = [x for lst in afs_datas_density_const for x in lst]
afs_datas_density_const = [x for x in afs_datas_density_const if int(x.num_agents) in constant_density_agents]
afs_agents_first_times_density_const = [(x.num_agents, x.runtimes[0]) for x in afs_datas_density_const]
afs_agents_optimal_times_density_const = [(x.num_agents, x.runtimes[-1]) for x in afs_datas_density_const]

mstar_datas_density_const = [read_from_file(f) for f in glob.glob('datasave/mstar_data_lst_*density0.1*')]
mstar_datas_density_const = [x for lst in mstar_datas_density_const for x in lst]
mstar_datas_density_const = [x for x in mstar_datas_density_const if int(x.num_agents) in constant_density_agents]
mstar_agents_times_density_const = [(x.num_agents, x.runtimes) for x in mstar_datas_density_const]

kRadiusTimeout = 300

def get_radius(filename):
    fr = filename.find("_xstar")+ 6;
    return int(filename[fr: fr+1])

def get_radius_first_runtime(filename):
    try:
        return float([l for l in open(filename, 'r').readlines() if "time_first_plan" in l][0].replace("time_first_plan: ", ""))
    except:
        return kRadiusTimeout

def get_radius_total_runtime(filename):
    try:
        return float([l for l in open(filename, 'r').readlines() if "Total time" in l][0].replace("Total time: ", ""))
    except:
        return kRadiusTimeout

xstar_datas_scale_radius = [(get_radius(f), get_radius_first_runtime(f), get_radius_total_runtime(f)) for f in glob.glob('datasave/xstar_grow_search_window*')]
xstar_radius_first_times = [(r, f) for r, f, t in xstar_datas_scale_radius]
xstar_radius_optimal_times = [(r, t) for r, f, t in xstar_datas_scale_radius]


def draw_timeout(timeout, xs, plt=plt):
    if type(timeout) is int:
        plt.axhline(timeout, color='black', lw=0.7, linestyle='--')
    elif type(timeout) is dict:
        ys = [timeout[x] for x in xs]
        plt.plot(xs, ys, linestyle='--',
                 color='black')

def plt_cis(agents_times_lst, title, timeout=None):
    agents_times_lst.sort()
    agents_to_times_dict = reduce(add_to_dict, agents_times_lst, dict())
    agents_to_100_bounds_lst = \
        [[k] + list(get_ci(v, 100)) for k, v in agents_to_times_dict.items()]
    agents_to_95_bounds_lst = \
        [[k] + list(get_ci(v, 95)) for k, v in agents_to_times_dict.items()]
    agents_to_90_bounds_lst = \
        [[k] + list(get_ci(v, 90)) for k, v in agents_to_times_dict.items()]
    agents_to_75_bounds_lst = \
        [[k] + list(get_ci(v, 75)) for k, v in agents_to_times_dict.items()]
    medians = []
    xs, hs, ms, ls = zip(*agents_to_100_bounds_lst)
    medians = list(ms)
    plt.plot(xs, ls, color=ps.color(0, 4), label="Max bounds")
    plt.plot(xs, hs, color=ps.color(0, 4))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(0, 4)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ms, ls = zip(*agents_to_95_bounds_lst)
    plt.plot(xs, ls, color=ps.color(1, 4), label="95% CI")
    plt.plot(xs, hs, color=ps.color(1, 4))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(1, 4)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ms, ls = zip(*agents_to_90_bounds_lst)
    plt.plot(xs, ls, color=ps.color(2, 4), label="90% CI")
    plt.plot(xs, hs, color=ps.color(2, 4))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(2, 4)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ms, ls = zip(*agents_to_75_bounds_lst)
    plt.plot(xs, ls, color=ps.color(3, 4), label="75% CI")
    plt.plot(xs, ms, color=ps.color(3, 4))
    plt.plot(xs, hs, color=ps.color(3, 4))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(3, 4)),
                     interpolate=True,
                     linewidth=0.0)
    plt.yscale('log')
    plt.ylabel("Time (seconds)")
    plt.xlabel("Number of agents")
    plt.xticks(xs)

    draw_timeout(timeout, xs)


def plt_95_ci(agents_times_lst, name, plt_idx, max_idx, timeout=None, show_y_axis=True):
    agents_times_lst.sort()
    agents_to_times_dict = reduce(add_to_dict, agents_times_lst, dict())

    agents_to_95_bounds_lst = \
        [[k] + list(get_ci(v, 95)) for k, v in agents_to_times_dict.items()]
    medians = []
    xs, hs, ms, ls = zip(*agents_to_95_bounds_lst)
    plt.plot(xs, ls, color=ps.color(plt_idx, max_idx), linestyle='--')
    plt.plot(xs, hs, color=ps.color(plt_idx, max_idx), linestyle='--')
    plt.plot(xs, ms, color=ps.color(plt_idx, max_idx), label="{} 95% CI".format(name))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(plt_idx, max_idx), 0.2),
                     interpolate=True,
                     linewidth=0.0)
    plt.yscale('log')
    if show_y_axis:
        plt.ylabel("Time (seconds)")
    plt.xlabel("Number of agents")
    plt.xticks(xs)

    draw_timeout(timeout, xs)


def plt_percentiles(agents_times_lst, title, timeout=None):
    agents_to_times_dict = reduce(add_to_dict, agents_times_lst, dict())
    agents_to_100_bounds_lst = \
        [[k] + list(get_percentile(v, 100))
         for k, v in agents_to_times_dict.items()]
    agents_to_95_bounds_lst = \
        [[k] + list(get_percentile(v, 95))
         for k, v in agents_to_times_dict.items()]
    agents_to_90_bounds_lst = \
        [[k] + list(get_percentile(v, 90))
         for k, v in agents_to_times_dict.items()]
    agents_to_75_bounds_lst = \
        [[k] + list(get_percentile(v, 75))
         for k, v in agents_to_times_dict.items()]
    agents_to_50_bounds_lst = \
        [[k] + list(get_percentile(v, 50))
         for k, v in agents_to_times_dict.items()]
    xs, hs, ls = zip(*agents_to_100_bounds_lst)
    plt.plot(xs, hs, color=ps.color(0, 5), label="Max bounds")
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(0, 5)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ls = zip(*agents_to_95_bounds_lst)
    plt.plot(xs, hs, color=ps.color(1, 5), label="95th percentile")
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(1, 5)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ls = zip(*agents_to_90_bounds_lst)
    plt.plot(xs, hs, color=ps.color(2, 5), label="90th percentile")
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(2, 5)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ls = zip(*agents_to_75_bounds_lst)
    plt.plot(xs, hs, color=ps.color(3, 5), label="75th percentile")
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(3, 5)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ls = zip(*agents_to_50_bounds_lst)
    plt.plot(xs, ls, color=ps.color(4, 5), label="50th percentile")
    plt.plot(xs, hs, color=ps.color(4, 5))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(4, 5)),
                     interpolate=True,
                     linewidth=0.0)
    plt.yscale('log')
    plt.ylabel("Time (seconds)")
    plt.xlabel("Number of agents")
    plt.xticks(xs)

    draw_timeout(timeout, xs)


############################
# Head to head comparisons #
############################
print("Head to head comparisons")

ps.setupfig()
plt_95_ci(xstar_agents_optimal_times_density_01, "X* Optimal", 0, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_01, "AFS Optimal", 1, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_01, "X* First", 2, 4, 1200)
plt_95_ci(afs_agents_first_times_density_01, "AFS First", 3, 4, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_afs_first_optimal_times_density_01")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_01, "X* First", 0, 2, 1200, False)
plt_95_ci(afs_agents_first_times_density_01, "AFS First", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_afs_first_times_density_01")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_01, "X* Optimal", 0, 2, 1200, False)
plt_95_ci(afs_agents_optimal_times_density_01, "AFS Optimal", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_afs_optimal_times_density_01")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_01, "X* First", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_01, "CBS First/Opt.", 1, 2, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_cbs_first_times_density_01")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_01, "X* Optimal", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_01, "CBS Optimal", 1, 2, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_cbs_optimal_times_density_01")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_01, "X* First", 0, 2, 1200, False)
plt_95_ci(mstar_agents_times_density_01, "M* First/Opt.", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_mstar_first_times_density_01")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_01, "X* Optimal", 0, 2, 1200, False)
plt_95_ci(mstar_agents_times_density_01, "M* Optimal", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_mstar_optimal_times_density_01")

ps.setupfig(halfsize=True)
plt_95_ci(cbs_agents_times_density_01, "CBS First/Opt.", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_01, "M* First/Opt.", 1, 4, 1200)
plt_95_ci(afs_agents_first_times_density_01, "AFS First", 2, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_01, "X* First", 3, 4, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_vs_all_first_times_density_01")

ps.setupfig(halfsize=True)
plt_95_ci(cbs_agents_times_density_01, "CBS Optimal", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_01, "M* Optimal", 1, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_01, "AFS Optimal", 2, 4, 1200)
plt_95_ci(xstar_agents_optimal_times_density_01, "X* Optimal", 3, 4, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_vs_all_optimal_times_density_01")

# ======================================

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_05, "X* Optimal", 0, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_05, "AFS Optimal", 1, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_05, "X* First", 2, 4, 1200)
plt_95_ci(afs_agents_first_times_density_05, "AFS First", 3, 4, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_afs_first_optimal_times_density_05")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_05, "X* First", 0, 2, 1200, False)
plt_95_ci(afs_agents_first_times_density_05, "AFS First", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_afs_first_times_density_05")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_05, "X* Optimal", 0, 2, 1200, False)
plt_95_ci(afs_agents_optimal_times_density_05, "AFS Optimal", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_afs_optimal_times_density_05")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_05, "X* First", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_05, "CBS First/Opt.", 1, 2, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_cbs_first_times_density_05")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_05, "X* Optimal", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_05, "CBS Optimal", 1, 2, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_cbs_optimal_times_density_05")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_05, "X* First", 0, 2, 1200, False)
plt_95_ci(mstar_agents_times_density_05, "M* First/Opt.", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_mstar_first_times_density_05")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_05, "X* Optimal", 0, 2, 1200, False)
plt_95_ci(mstar_agents_times_density_05, "M* Optimal", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_mstar_optimal_times_density_05")

ps.setupfig(halfsize=True)
plt_95_ci(cbs_agents_times_density_05, "CBS First/Opt.", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_05, "M* First/Opt.", 1, 4, 1200)
plt_95_ci(afs_agents_first_times_density_05, "AFS First", 2, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_05, "X* First", 3, 4, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_vs_all_first_times_density_05")

ps.setupfig(halfsize=True)
plt_95_ci(cbs_agents_times_density_05, "CBS Optimal", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_05, "M* Optimal", 1, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_05, "AFS Optimal", 2, 4, 1200)
plt_95_ci(xstar_agents_optimal_times_density_05, "X* Optimal", 3, 4, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_vs_all_optimal_times_density_05")

# ======================================

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_1, "X* Optimal", 0, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_1, "AFS Optimal", 1, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_1, "X* First", 2, 4, 1200)
plt_95_ci(afs_agents_first_times_density_1, "AFS First", 3, 4, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_afs_first_optimal_times_density_1")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_1, "X* First", 0, 2, 1200, False)
plt_95_ci(afs_agents_first_times_density_1, "AFS First", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_afs_first_times_density_1")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_1, "X* Optimal", 0, 2, 1200, False)
plt_95_ci(afs_agents_optimal_times_density_1, "AFS Optimal", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_afs_optimal_times_density_1")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_1, "X* First", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_1, "CBS First/Opt.", 1, 2, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_cbs_first_times_density_1")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_1, "X* Optimal", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_1, "CBS Optimal", 1, 2, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_cbs_optimal_times_density_1")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_1, "X* First", 0, 2, 1200, False)
plt_95_ci(mstar_agents_times_density_1, "M* First/Opt.", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_mstar_first_times_density_1")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_1, "X* Optimal", 0, 2, 1200, False)
plt_95_ci(mstar_agents_times_density_1, "M* Optimal", 1, 2, 1200, False)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_mstar_optimal_times_density_1")

ps.setupfig(halfsize=True)
plt_95_ci(cbs_agents_times_density_1, "CBS First/Opt.", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_1, "M* First/Opt.", 1, 4, 1200)
plt_95_ci(afs_agents_first_times_density_1, "AFS First", 2, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_1, "X* First", 3, 4, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_vs_all_first_times_density_1")

ps.setupfig(halfsize=True)
plt_95_ci(cbs_agents_times_density_1, "CBS Optimal", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_1, "M* Optimal", 1, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_1, "AFS Optimal", 2, 4, 1200)
plt_95_ci(xstar_agents_optimal_times_density_1, "X* Optimal", 3, 4, 1200)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_vs_all_optimal_times_density_1")


###########################################
# X* Only Agents vs Performance Breakdown #
###########################################
print("X* Only Agents vs Performance Breakdown")

ps.setupfig()
plt_cis(agents_first_times_lst, "Time to first solution", kTimeout)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_first_solution_ci")

ps.setupfig()
plt_cis(agents_optimal_times_lst, "Time to optimal solution", kTimeout)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_optimal_solution_ci")

ps.setupfig()
plt_percentiles(agents_first_times_lst, "Time to first solution", kTimeout)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_first_solution_percentile")

ps.setupfig()
plt_percentiles(agents_optimal_times_lst, "Time to optimal solution", kTimeout)
ps.grid()
ps.legend('ul')
ps.save_fig("xstar_optimal_solution_percentile")


def plt_window_agents_boxplot(num_agents_in_window_times_lst, title, timeout=None, set_y_label=True, min_y=None, max_y=None):
    # Build {agent : runtimes} dict
    num_agents_in_window_to_optimal_times_dict = \
        reduce(add_to_dict, num_agents_in_window_times_lst, dict())
    # Remove keys less than 2
    num_agents_in_window_to_optimal_times_dict = \
        {k: v for k, v in num_agents_in_window_to_optimal_times_dict.items()
         if k >= 2}
    # Fill in any missing count in the range with empty list
    max_key = max(num_agents_in_window_to_optimal_times_dict.keys())
    min_key = min(num_agents_in_window_to_optimal_times_dict.keys())
    num_agents_in_window_to_optimal_times_dict = \
        {e: num_agents_in_window_to_optimal_times_dict.get(e, []) for e in
         range(min_key, max_key + 1)}
    # Convert to list of (k, list(v)) pairs sorted by k
    keys_values = \
        [(k, sorted(v)) for k, v in
         sorted(num_agents_in_window_to_optimal_times_dict.items(),
                key=lambda kv: kv[0])]
    ks, vs = zip(*keys_values)
    flierprops = dict(marker='.', markersize=1)
    plt.boxplot(vs, notch=False, flierprops=flierprops)
    plt.gca().set_xticklabels(ks)
    plt.xlabel("Largest number of agents in window")
    if set_y_label:
        plt.ylabel("Time (seconds)")
    if min_y is not None:
        plt.ylim(bottom=min_y)
    if max_y is not None:
        plt.ylim(top=max_y)

    draw_timeout(timeout, None)


def plt_window_agents_hist(num_agents_in_window_times_lst, title, plt=plt, draw_y_label=True, xlabel="Largest number of agents in window"):
    # Build {agent : runtimes} dict
    num_agents_in_window_to_optimal_times_dict = \
        reduce(add_to_dict, num_agents_in_window_times_lst, dict())
    # Remove keys less than 2
    num_agents_in_window_to_optimal_times_dict = \
        {k: v for k, v in num_agents_in_window_to_optimal_times_dict.items()
         if k >= 2}
    # Fill in any missing count in the range with empty list
    max_key = max(num_agents_in_window_to_optimal_times_dict.keys())
    min_key = min(num_agents_in_window_to_optimal_times_dict.keys())
    num_agents_in_window_to_optimal_times_dict = \
        {e: num_agents_in_window_to_optimal_times_dict.get(e, []) for e in
         range(min_key, max_key + 1)}
    # Convert to list of (k, list(v)) pairs sorted by k
    k_vs = \
        [(k, len(v)) for k, v in
         num_agents_in_window_to_optimal_times_dict.items()]
    ks, vs = zip(*k_vs)
    plt.bar(ks, vs)
    if plt is matplotlib.pyplot:
        plt.xticks(ks)
        plt.xlabel(xlabel)
        plt.ylabel("Occurrences")
    else:
        plt.set_xticks(ks)
        plt.set_xlabel(xlabel)
        if draw_y_label:
            plt.set_ylabel("Occurrences")


######################################################
# Histogram and boxplot of window dimensions vs time #
######################################################
print("Histogram and boxplot of window dimensions vs time")

min_time_boxplot = min([t for a, t in num_agents_in_window_first_times_lst])
max_time_boxplot = max([t for a, t in num_agents_in_window_optimal_times_lst])
ps.setupfig(halfsize=True)
plt_window_agents_boxplot(num_agents_in_window_first_times_lst,
                          "Largest number of agents in window vs time to "
                          "first solution", kTimeout, min_y=min_time_boxplot,
                          max_y=max_time_boxplot)
plt.yscale('log')
ps.grid()
ps.save_fig("window_vs_time_to_first_boxplot")

ps.setupfig()
plt_window_agents_hist(num_agents_in_window_first_times_lst,
                       "Largest number of agents in window vs occurrences in "
                       "first solution")
plt.yscale('log')
ps.grid()
ps.save_fig("window_vs_time_to_first_hist")

ps.setupfig(halfsize=True)
plt_window_agents_boxplot(num_agents_in_window_optimal_times_lst,
                          "Largest number of agents in any window vs time to "
                          "optimal solution", kTimeout, False, min_y=min_time_boxplot,
                          max_y=max_time_boxplot)
plt.yscale('log')
ps.grid()
ps.save_fig("window_vs_time_to_optimal_boxplot")

ps.setupfig()
plt_window_agents_hist(num_agents_in_window_optimal_times_lst,
                          "Largest number of agents in window vs occurrences in "
                          "optimal solution")
plt.yscale('log')
ps.grid()
ps.save_fig("window_vs_time_to_optimal_hist")

f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
ps.setupfig(f)
ps.grid(ax1)
plt_window_agents_hist(num_agents_in_window_first_times_lst,
                       "Largest number of agents in window vs occurrences in "
                       "first solution", plt=ax1, xlabel="Largest number of agents in window\nfor first solution")
ax1.set_yscale('log')
ps.grid(ax2)

plt_window_agents_hist(num_agents_in_window_optimal_times_lst,
                       "Largest number of agents in window vs occurrences in "
                       "optimal solution", plt=ax2, draw_y_label=False, xlabel="Largest number of agents in window\nfor optimal solution")
ps.save_fig("window_vs_time_both_hist")


def plt_radius_vs_runtimes(data, printylabel, plt=plt, timeout=kRadiusTimeout):
    data_dict = reduce(add_to_dict, data, dict())
    for k in data_dict:
        data_dict[k].sort()
    radius_to_100_bounds_lst = \
        [[k] + list(get_ci(v, 100)) for k, v in sorted(data_dict.items())]
    radius_to_95_bounds_lst = \
        [[k] + list(get_ci(v, 95)) for k, v in sorted(data_dict.items())]
    radius_to_90_bounds_lst = \
        [[k] + list(get_ci(v, 90)) for k, v in sorted(data_dict.items())]
    radius_to_75_bounds_lst = \
        [[k] + list(get_ci(v, 75)) for k, v in sorted(data_dict.items())]
    xs, hs, ms, ls = zip(*radius_to_100_bounds_lst)
    plt.plot(xs, ls, color=ps.color(0, 4), label="Max bounds")
    plt.plot(xs, hs, color=ps.color(0, 4))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(0, 4)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ms, ls = zip(*radius_to_95_bounds_lst)
    plt.plot(xs, ls, color=ps.color(1, 4), label="95% CI")
    plt.plot(xs, hs, color=ps.color(1, 4))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(1, 4)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ms, ls = zip(*radius_to_90_bounds_lst)
    plt.plot(xs, ls, color=ps.color(2, 4), label="90% CI")
    plt.plot(xs, hs, color=ps.color(2, 4))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(2, 4)),
                     interpolate=True,
                     linewidth=0.0)
    xs, hs, ms, ls = zip(*radius_to_75_bounds_lst)
    plt.plot(xs, ls, color=ps.color(3, 4), label="75% CI")
    plt.plot(xs, ms, color=ps.color(3, 4))
    plt.plot(xs, hs, color=ps.color(3, 4))
    plt.fill_between(xs, ls, hs,
                     where=ls <= hs,
                     facecolor=ps.alpha(ps.color(3, 4)),
                     interpolate=True,
                     linewidth=0.0)
    if plt is matplotlib.pyplot:
        plt.yscale('log')
        if printylabel:
            plt.ylabel("Time (seconds)")
        plt.xlabel("Initial window $L_{\infty}$ radius")
        plt.xticks(xs)
    else:
        plt.set_yscale('log')
        if printylabel:
            plt.set_ylabel("Time (seconds)")
        plt.set_xlabel("Initial window $L_{\infty}$ radius")
        plt.set_xticks(xs)

    draw_timeout(timeout, xs, plt)


######################
# Density vs runtime #
######################
print("Density vs runtime")

ps.setupfig()
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 0, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_const, "AFS Optimal", 1, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 2, 4, 1200)
plt_95_ci(afs_agents_first_times_density_const, "AFS First", 3, 4, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_afs_first_optimal_times_density_const")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 0, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_const, "AFS Optimal", 1, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 2, 4, 1200)
plt_95_ci(afs_agents_first_times_density_const, "AFS First", 3, 4, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_afs_first_optimal_times_density_const_half")

ps.setupfig()
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 0, 2, 1200)
plt_95_ci(afs_agents_first_times_density_const, "AFS First", 1, 2, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_afs_first_times_density_const")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 0, 2, 1200, False)
plt_95_ci(afs_agents_first_times_density_const, "AFS First", 1, 2, 1200, False)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_afs_first_times_density_const_half")

ps.setupfig()
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 0, 2, 1200)
plt_95_ci(afs_agents_optimal_times_density_const, "AFS Optimal", 1, 2, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_afs_optimal_times_density_const")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 0, 2, 1200, False)
plt_95_ci(afs_agents_optimal_times_density_const, "AFS Optimal", 1, 2, 1200, False)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_afs_optimal_times_density_const_half")

ps.setupfig()
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_const, "CBS First/Opt.", 1, 2, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_cbs_first_times_density_const")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_const, "CBS First/Opt.", 1, 2, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_cbs_first_times_density_const_half")

ps.setupfig()
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_const, "CBS Optimal", 1, 2, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_cbs_optimal_times_density_const")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 0, 2, 1200)
plt_95_ci(cbs_agents_times_density_const, "CBS Optimal", 1, 2, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_cbs_optimal_times_density_const_half")

ps.setupfig()
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 0, 2, 1200)
plt_95_ci(mstar_agents_times_density_const, "M* First/Opt.", 1, 2, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_mstar_first_times_density_const")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 0, 2, 1200, False)
plt_95_ci(mstar_agents_times_density_const, "M* First/Opt.", 1, 2, 1200, False)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_mstar_first_times_density_const_half")

ps.setupfig()
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 0, 2, 1200)
plt_95_ci(mstar_agents_times_density_const, "M* Optimal", 1, 2, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_mstar_optimal_times_density_const")

ps.setupfig(halfsize=True)
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 0, 2, 1200, False)
plt_95_ci(mstar_agents_times_density_const, "M* Optimal", 1, 2, 1200, False)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_mstar_optimal_times_density_const_half")

ps.setupfig()
plt_95_ci(cbs_agents_times_density_const, "CBS First/Opt.", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_const, "M* First/Opt.", 1, 4, 1200)
plt_95_ci(afs_agents_first_times_density_const, "AFS First", 2, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 3, 4, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_vs_all_first_times_density_const")

ps.setupfig(halfsize=True)
plt_95_ci(cbs_agents_times_density_const, "CBS First/Opt.", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_const, "M* First/Opt.", 1, 4, 1200)
plt_95_ci(afs_agents_first_times_density_const, "AFS First", 2, 4, 1200)
plt_95_ci(xstar_agents_first_times_density_const, "X* First", 3, 4, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_vs_all_first_times_density_const_half")

ps.setupfig()
plt_95_ci(cbs_agents_times_density_const, "CBS Optimal", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_const, "M* Optimal", 1, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_const, "AFS Optimal", 2, 4, 1200)
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 3, 4, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_vs_all_optimal_times_density_const")

ps.setupfig(halfsize=True)
plt_95_ci(cbs_agents_times_density_const, "CBS Optimal", 0, 4, 1200)
plt_95_ci(mstar_agents_times_density_const, "M* Optimal", 1, 4, 1200)
plt_95_ci(afs_agents_optimal_times_density_const, "AFS Optimal", 2, 4, 1200)
plt_95_ci(xstar_agents_optimal_times_density_const, "X* Optimal", 3, 4, 1200)
ps.grid()
ps.legend('br')
ps.save_fig("xstar_vs_all_optimal_times_density_const_half")

ps.setupfig(halfsize=True)
plt_radius_vs_runtimes(xstar_radius_first_times, True)
ps.grid()
ps.legend('ul')
ps.save_fig("radius_first_times")

ps.setupfig(halfsize=True)
plt_radius_vs_runtimes(xstar_radius_optimal_times, False)
ps.grid()
#ps.legend('ul')
ps.save_fig("radius_optimal_times")

print("TODO: FIX")
exit(0)

# f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
# ps.setupfig(f)
# ps.grid(ax1)
# plt_radius_vs_runtimes(radius_30_first_times_lst, True, plt=ax1)
# ps.legend('ul', plt=ax1)

# ps.grid(ax2)
# plt_radius_vs_agents(radius_30_optimal_times_lst, False, plt=ax2)
# # ps.legend('ul')
# ps.save_fig("radius_30_first_optimal_times")
