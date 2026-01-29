from typing import List, Optional
from enum import Enum
from dataclasses import dataclass

import numpy as np
import pandas
from matplotlib import pyplot as plt
from matplotlib.collections import PatchCollection, LineCollection
from matplotlib.patches import Rectangle, Patch

ENGINE_BASE = 0x00000
JOB_BASE    = 0x00100
TASK_BASE   = 0x10000

class ProfileCode(Enum):
    PROFILER_VERSION           = 0xffffffffffffffff

    ENGINE_LAUNCH              = 0  + 0x00000
    ENGINE_START               = 1  + 0x00000
    ENGINE_RUN                 = 2  + 0x00000
    ENGINE_STOP                = 3  + 0x00000
    ENGINE_COMPLETE            = 4  + 0x00000
    ENGINE_SHUTDOWN            = 5  + 0x00000
    ENGINE_EXIT                = 6  + 0x00000
    ENGINE_ERROR               = 7  + 0x00000
    ENGINE_ABORT               = 8  + 0x00000

    JOB_CREATE                 = 0  + 0x00100
    JOB_CLEARANCE              = 1  + 0x00100
    JOB_GENERATE_SCAN          = 2  + 0x00100
    JOB_GENERATE_STROBE        = 3  + 0x00100
    JOB_ACQUIRE_DISPATCH_BEGIN = 4  + 0x00100
    JOB_ACQUIRE_DISPATCH_END   = 5  + 0x00100
    JOB_ACQUIRE_JOIN           = 6  + 0x00100
    JOB_PROCESS_DISPATCH_BEGIN = 7  + 0x00100
    JOB_PROCESS_DISPATCH_END   = 8  + 0x00100
    JOB_FORMAT_JOIN            = 9  + 0x00100
    JOB_RECYCLE                = 10 + 0x00100

    TASK_ACQUIRE_COMPLETE      = 0  + 0x10000
    TASK_PROCESS_COMPLETE      = 1  + 0x10000
    TASK_FORMAT_BEGIN          = 2  + 0x10000
    TASK_FORMAT_PLAN           = 3  + 0x10000
    TASK_FORMAT_END            = 4  + 0x10000

    def is_engine_code(self):
        return 0 <= (self.value - ENGINE_BASE) <= 0xff
    def is_job_code(self):
        return 0 <= (self.value - JOB_BASE) <= 0xff
    def is_task_code(self):
        return 0 <= (self.value - TASK_BASE) <= 0xff

    def __str__(self):
        return self.name

@dataclass
class EventPeriods:
    name: str

    start_code: ProfileCode
    starts: np.ndarray

    end_code: ProfileCode
    ends: np.ndarray

    jobs: np.ndarray
    task: Optional[int]

    preload: Optional[int]

dtype = np.dtype([
    ('code', '<u8'),
    ('task', '<u8'),
    ('job', '<u8'),
    ('timestamp', '<u8'),
])

def load_binary(f):
    return np.fromfile(f, dtype=dtype)
load = load_binary

def format_events(events):
    events = pandas.DataFrame(events)
    events.code = events.code.apply(ProfileCode)

    # strip version event
    if events.iloc[0].code is ProfileCode.PROFILER_VERSION:
        events = events.iloc[1:]

    # normalize times
    events.timestamp = (events.timestamp - events.iloc[0].timestamp) / 1e9
    return events

def extract_start_and_preload(events):
    try:
        start_time = events[events.code == ProfileCode.ENGINE_START].iloc[0].timestamp
    except IndexError:
        raise RuntimeError('no engine start event found')
    preload_count = int(events[(events.code == ProfileCode.JOB_CREATE) & (events.timestamp <= start_time)].iloc[-1].job)

    return (start_time, preload_count)

def extract_stage_bounds(events) -> List[EventPeriods]:
    output = []

    names = ['block wait', 'pre-generate', 'acquire dispatch', 'acquire wait', 'post-generate', 'process dispatch', 'process+format wait', 'recycle']
    codes = [
        ProfileCode.JOB_CREATE,
        ProfileCode.JOB_CLEARANCE,
        ProfileCode.JOB_ACQUIRE_DISPATCH_BEGIN,
        ProfileCode.JOB_ACQUIRE_DISPATCH_END,
        ProfileCode.JOB_ACQUIRE_JOIN,
        ProfileCode.JOB_PROCESS_DISPATCH_BEGIN,
        ProfileCode.JOB_PROCESS_DISPATCH_END,
        ProfileCode.JOB_FORMAT_JOIN,
        ProfileCode.JOB_RECYCLE
    ]

    (start_time, preload_count) = extract_start_and_preload(events)

    for (name, a, b) in zip(names, codes[:-1], codes[1:]):
        esa = events[events.code == a]
        esb = events[events.code == b]
        n = min(len(esa), len(esb))

        # check if stage exhibits preloading
        start_before_start = events[(events.code == a) & (events.timestamp < start_time)]
        end_before_start = events[(events.code == b) & (events.timestamp < start_time)]
        preloaded = len(start_before_start) > preload_count // 2 and len(end_before_start) == 0

        output.append(EventPeriods(name, a, esa.iloc[:n].timestamp.values, b, esb.iloc[:n].timestamp.values, esa.job.iloc[:n].values, None, preload_count + 1 if preloaded else None))

    return output

def extract_task_bounds(events) -> List[EventPeriods]:
    output = []

    names = ['acquire task', 'process task']
    intervals = [(ProfileCode.JOB_ACQUIRE_DISPATCH_BEGIN, ProfileCode.TASK_ACQUIRE_COMPLETE), (ProfileCode.JOB_PROCESS_DISPATCH_BEGIN, ProfileCode.TASK_PROCESS_COMPLETE)]

    (start_time, preload_count) = extract_start_and_preload(events)

    for (name, (a, b)) in zip(names, intervals):
        es = events[events.code == b]
        if not len(es):
            continue

        baselines = events[events.code == a]
        es = es.join(baselines.set_index('job').timestamp, on='job', rsuffix='_baseline')

        for i in range(int(es.task.max()) + 1):
            # check if stage exhibits preloading
            start_before_start = events[(events.code == a) & (events.timestamp < start_time)]
            end_before_start = events[(events.code == b) & (events.timestamp < start_time) & (events.task == i)]
            preloaded = len(start_before_start) > preload_count // 2 and len(end_before_start) == 0

            est = es[es.task == i]
            output.append(EventPeriods(name, a, est.timestamp_baseline.values, b, est.timestamp.values, est.job.values, i, preload_count + 1 if preloaded else None))

    names = ['format task']
    intervals = [(ProfileCode.TASK_FORMAT_BEGIN, ProfileCode.TASK_FORMAT_END)]

    for (name, (a, b)) in zip(names, intervals):
        es = events[events.code == b]
        if not len(es):
            continue

        baselines = events[events.code == a]
        es = es.join(baselines.set_index(['job', 'task']), on=['job', 'task'], rsuffix='_baseline')

        for i in range(int(es.task.max()) + 1):
            # check if stage exhibits preloading
            start_before_start = events[(events.code == a) & (events.timestamp < start_time)]
            end_before_start = events[(events.code == b) & (events.timestamp < start_time) & (events.task == i)]
            preloaded = len(start_before_start) > preload_count // 2 and len(end_before_start) == 0

            est = es[es.task == i]
            output.append(EventPeriods(name, a, est.timestamp_baseline.values, b, est.timestamp.values, est.job.values, i, preload_count + 1 if preloaded else None))

    return output

def print_statistics(events):
    (start_time, preload_count) = extract_start_and_preload(events)

    def _print_stats(name, ep: EventPeriods):
        if any([s in ep.name for s in ['block wait', 'pre-generate', 'acquire']]):
            mask = ep.jobs > preload_count
        else:
            mask = np.ones_like(ep.starts, dtype=bool)

        if len(ep.starts[mask]) <= 2:
            return

        intervals = np.diff(ep.starts[mask])
        durations = ep.ends[mask] - ep.starts[mask]

        notes = []
        if ep.preload:
            durations /= ep.preload
            notes.append(f'P{ep.preload}')
        notes = ','.join(notes)

        print(f'{name:20s}    {len(intervals):6d}    {1e3*intervals.mean():6.2f} +/- {1e3*intervals.std():6.2f}  [{1e3*intervals.min():7.2f} - {1e3*intervals.max():7.2f}] ms   ({1 / intervals.mean():6.1f} Hz)    {1e3*durations.mean():7.2f} +/- {1e3*durations.std():6.2f} [{1e3*durations.min():7.2f} - {1e3*durations.max():7.2f}] ms   ({100*durations.mean()/intervals.mean():6.1f}%)    {notes}')

    stage_bounds = extract_stage_bounds(events)
    task_bounds = extract_task_bounds(events)

    header = 'Activity               Samples     Interval (mean +/- std, min - max)         Rate          Duration (mean +/- std, min - max)           Usage        Notes'
    print(header)
    print('-' * len(header))

    for sb in stage_bounds:
        _print_stats(sb.name, sb)

        if sb.name.endswith('wait'):
            while task_bounds and task_bounds[0].name.split()[0] in sb.name:
                tb = task_bounds.pop(0)
                _print_stats(f' - {tb.name} {tb.task}', tb)

def plot_timeline(events, waterfall=True):
    fig, ax = plt.subplots()
    legend = []

    # draw engine events
    mask = events.code.apply(lambda c: c.is_engine_code())
    draws = events[mask]
    for (_, e) in draws.iterrows():
        ax.axvline(e.timestamp, c='k', ls='--')
        ax.annotate(
            e.code.name.split('_')[-1].title(),
            xy=(e.timestamp, 1), xycoords=('data', 'axes fraction'),
            xytext=(0, 4), textcoords='offset points',
            ha='center', va='bottom', rotation='vertical'
        )

    offsets = {
        ProfileCode.JOB_CREATE: 0,
        ProfileCode.JOB_CLEARANCE: -1,
        ProfileCode.JOB_GENERATE_SCAN: -1,
        ProfileCode.JOB_GENERATE_STROBE: -1,
        ProfileCode.JOB_ACQUIRE_DISPATCH_BEGIN: -2,
        ProfileCode.JOB_ACQUIRE_DISPATCH_END: -2,
        ProfileCode.TASK_ACQUIRE_COMPLETE: -2,
        ProfileCode.JOB_ACQUIRE_JOIN: -3,
        ProfileCode.JOB_PROCESS_DISPATCH_BEGIN: -4,
        ProfileCode.JOB_PROCESS_DISPATCH_END: -4,
        ProfileCode.TASK_PROCESS_COMPLETE: -4,
        ProfileCode.TASK_FORMAT_BEGIN: -5,
        ProfileCode.TASK_FORMAT_PLAN: -5,
        ProfileCode.TASK_FORMAT_END: -5,
        ProfileCode.JOB_FORMAT_JOIN: -6,
        ProfileCode.JOB_RECYCLE: -6
    }
    stages = ['Wait', 'Pre-Generate', 'Acquire', 'Post-Generate', 'Process', 'Format', 'Recycle'][::-1]

    # draw job intervals
    styles = [('k', 'none'), ('C0', 'C0'), ('C1', 'C1'), ('C1', 'none'), ('C2', 'C2'), ('C3', 'C3'), ('C3', 'none'), ('C5', 'C5')]
    for (sb, (ec, fc)) in zip(extract_stage_bounds(events), styles):
        ps = []
        for (t1, t2, j) in zip(sb.starts, sb.ends, sb.jobs):
            o = j if waterfall else offsets[sb.start_code]
            ps.append(Rectangle((t1, o - 0.5), t2 - t1, 1))
        ax.add_collection(PatchCollection(ps, fc=fc, ec=ec))
        legend.append(Patch(fc=fc, ec=ec, label=sb.name))

    # draw scan events
    for code in [ProfileCode.JOB_GENERATE_SCAN, ProfileCode.JOB_GENERATE_STROBE]:
        segments = []
        draws = events[events.code == code]
        size = draws.task.max() + 1
        for (_, e) in draws.iterrows():
            o = e.job if waterfall else offsets[e.code]
            x = e.timestamp
            y = o - 0.5 + e.task / size
            segments.append(([x, y], [x, y + 1 / size]))
        ax.add_collection(LineCollection(segments, color='w', ls='--', alpha=0.5))

    # draw baselined task events
    styles = {'acquire': ('none', 'C1'), 'process': ('none', 'C3'), 'format': ('none', 'C4')}
    hatches = ['/', '\\', '|', '-', '+', 'x', 'o', 'O', '.', '*']
    for tb in extract_task_bounds(events):
        (ec, fc) = styles[tb.name.split()[0]]
        size = int(events[events.code == tb.end_code].task.max()) + 1
        alpha = np.linspace(0.4, 0.6, size)[int(tb.task)] if size > 1 else 0.5
        ps = []
        for (t1, t2, j) in zip(tb.starts, tb.ends, tb.jobs):
            o = j if waterfall else offsets[tb.end_code]
            ps.append(Rectangle((t1, o - 0.5 + tb.task / size), t2 - t1, 1 / size))
        ax.add_collection(PatchCollection(ps, fc=fc, ec=ec, alpha=alpha))
        legend.append(Patch(fc=fc, ec=ec, alpha=alpha, label=f'{tb.name} {tb.task}'))

    # draw format plan events
    segments = []
    draws = events[events.code == ProfileCode.TASK_FORMAT_PLAN]
    size = draws.task.max() + 1
    for (_, e) in draws.iterrows():
        o = e.job if waterfall else offsets[e.code]
        x = e.timestamp
        y = o - 0.5 + e.task / size
        segments.append(([x, y], [x, y + 1 / size]))
    ax.add_collection(LineCollection(segments, color='C4', ls='--', alpha=0.5))

    ax.autoscale()
    if waterfall:
        ax.set_ylabel('job')
        ax.legend(handles=legend, loc='lower right')
    else:
        ax.set_yticks(sorted(list(set([o for (_, o) in offsets.items()]))))
        ax.set_yticklabels(stages)
    ax.set_xlabel('time (s)')

    plt.show()

if __name__ == '__main__':
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description='print vortex profiler log', formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('path', help='path to profiler log')
    parser.add_argument('--count', '-c', type=int, help='number of records to show')
    parser.add_argument('--skip', '-s', type=int, help='number of records to skip')
    parser.add_argument('--pretty', '-p', action='store_true', help='show pretty output')
    parser.add_argument('--timeline', '--timing', action='store_true', help='show profiler timeline (timing) diagram')
    parser.add_argument('--waterfall', action='store_true', help='show profiler waterfall diagram')
    parser.add_argument('--statistics', '--stats', action='store_true', help='show profiler statistics')

    args = parser.parse_args()

    events = load(args.path)

    if args.skip is not None:
        events = events[args.skip:]
    if args.count is not None:
        events = events[:args.count]

    if args.statistics:
        print_statistics(format_events(events))

    if args.timeline:
        plot_timeline(format_events(events), False)
    elif args.waterfall:
        plot_timeline(format_events(events), True)
    elif args.pretty:
        pandas.set_option('display.max_rows', args.count)

        events = pandas.DataFrame(events)
        events['code'] = events['code'].apply(ProfileCode)

        print(events)
    elif not args.statistics:
        print(events)
