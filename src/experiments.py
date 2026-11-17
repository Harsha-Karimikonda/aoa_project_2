"""Reproducible benchmarks, exact quality checks, CSVs, and TeX plots.

Run from the project root: uv run python -m src.experiments
No third-party Python packages are required.
"""
import argparse
import csv
import json
import math
import platform
import random
import statistics
import sys
import time
from pathlib import Path
from src.algorithms import assign_volunteers, greedy_depots, exact_depots

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261117


def flow_instance(k, family, seed):
    rng = random.Random(seed)
    probability = min(6 / k, 1) if family == 'sparse' else .25
    edges = {(v, j) for v in range(k) for j in range(k) if rng.random() < probability}
    # A planted 2-regular assignment guarantees feasibility; shifts are disjoint.
    edges.update((v, v) for v in range(k))
    edges.update((v, (v + 1) % k) for v in range(k))
    return [2] * k, [2] * k, sorted(edges)


def cover_instance(n, family, seed):
    if family == 'singleton':
        return [{i} for i in range(n)]
    rng = random.Random(seed)
    sets = [{u for u in range(n) if rng.random() < .1} for _ in range(n)]
    for u in range(n):
        sets[rng.randrange(n)].add(u)
    return sets


def timed(call, minimum_seconds, repeats):
    # Warm up, then batch short runs to reduce clock quantization/noise.
    result = call()
    start = time.perf_counter()
    call()
    elapsed = time.perf_counter() - start
    batch = max(1, min(500, math.ceil(minimum_seconds / max(elapsed, 1e-9))))
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        for _ in range(batch):
            result = call()
        samples.append((time.perf_counter() - start) / batch)
    return result, statistics.median(samples), min(samples), max(samples), batch


def write_csv(path, rows):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def slope(rows, field):
    x = [math.log(r['size']) for r in rows]
    y = [math.log(max(r[field], 1e-12)) for r in rows]
    mx, my = statistics.mean(x), statistics.mean(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / sum((a - mx)**2 for a in x)


def plots():
    # LaTeX reads checked-in CSVs directly; Overleaf supplies PGFPlots.
    for problem, families in [('flow', ['sparse', 'dense']),
                              ('cover', ['singleton', 'dense'])]:
        for measure, ylabel in [('seconds', 'Median runtime (seconds)'),
                                ('operations', 'Counted operations')]:
            parts = [r'\begin{tikzpicture}',
                     r'\begin{loglogaxis}[width=.98\columnwidth,height=4.6cm,'
                     r'xlabel={Instance size $k$},ylabel={' + ylabel + r'},'
                     r'grid=major,legend style={font=\scriptsize},'
                     r'legend pos=north west, unbounded coords=discard]']
            for family, color, marker in zip(families, ['blue', 'red'], ['*', 'square*']):
                path = 'results/' + problem + '_' + family + '.csv'
                parts.append(r'\addplot+[' + color + ',mark=' + marker +
                             r'] table[x=size,y=' + measure + r',col sep=comma]{' + path + '};')
                parts.append(r'\addlegendentry{' + family + '}')
                if measure == 'operations':
                    parts.append(r'\addplot[' + color + r',dashed,no marks] '
                                 r'table[x=size,y=bound,col sep=comma]{' + path + '};')
                    parts.append(r'\addlegendentry{' + family + ' bound}')
            parts.extend([r'\end{loglogaxis}', r'\end{tikzpicture}'])
            (ROOT / 'report' / 'figures' / (problem + '_' + measure + '.tex')).write_text(
                '\n'.join(parts) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats', type=int, default=5)
    parser.add_argument('--instances', type=int, default=3)
    parser.add_argument('--minimum-seconds', type=float, default=.02)
    args = parser.parse_args()
    if args.repeats < 1 or args.instances < 1 or args.minimum_seconds <= 0:
        parser.error('all parameters must be positive')
    results = ROOT / 'results'
    results.mkdir(exist_ok=True)
    summary, raw = {}, []
    for problem, families, sizes in [
            ('flow', ['sparse', 'dense'], [16, 32, 64, 128, 256]),
            ('cover', ['singleton', 'dense'], [32, 64, 128, 256, 512])]:
        for family in families:
            aggregate = []
            for size in sizes:
                per_size = []
                for trial in range(args.instances):
                    seed = SEED + size * 100 + trial
                    if problem == 'flow':
                        instance = flow_instance(size, family, seed)
                        call = lambda: assign_volunteers(*instance)
                    else:
                        instance = cover_instance(size, family, seed)
                        call = lambda: greedy_depots(size, instance)
                    r, seconds, low, high, batch = timed(call, args.minimum_seconds, args.repeats)
                    assert r.feasible
                    if problem == 'flow':
                        assert r.value == 2 * size
                        operations = r.edge_scans
                        # At most 2E residual edge inspections on each of F+1 BFSs.
                        bound = 2 * r.edges * (r.value + 1)
                        incidence = r.edges - 2 * size
                        rounds = r.bfs_calls - 1
                    else:
                        incidence = sum(map(len, instance))
                        operations = r.membership_checks
                        bound = min(size, len(instance)) * incidence
                        rounds = r.rounds
                    assert operations <= bound
                    row = dict(problem=problem, family=family, size=size, trial=trial,
                               seed=seed, seconds=seconds, min_seconds=low,
                               max_seconds=high, batch=batch, operations=operations,
                               bound=bound, incidence=incidence, rounds=rounds)
                    raw.append(row)
                    per_size.append(row)
                aggregate.append(dict(size=size, **{key: statistics.median(r[key] for r in per_size)
                                                   for key in ['seconds', 'operations', 'bound',
                                                               'incidence', 'rounds']}))
                print(problem, family, size, f"{aggregate[-1]['seconds']:.6f}s", flush=True)
            write_csv(results / (problem + '_' + family + '.csv'), aggregate)
            summary[problem + '_' + family] = {
                'timing_slope': slope(aggregate, 'seconds'),
                'operation_slope': slope(aggregate, 'operations'),
                'largest_seconds': aggregate[-1]['seconds'],
                'largest_operations': aggregate[-1]['operations']}
    write_csv(results / 'raw_timings.csv', raw)
    quality = []
    for trial in range(100):
        rng = random.Random(SEED + trial)
        n, m = 12, 14
        sites = [{u for u in range(n) if rng.random() < .25} for _ in range(m)]
        for u in range(n):
            sites[rng.randrange(m)].add(u)
        greedy = greedy_depots(n, sites)
        optimum = exact_depots(n, sites)
        quality.append(dict(trial=trial, seed=SEED + trial, communities=n, candidates=m,
                            greedy=len(greedy.selected), optimum=len(optimum),
                            ratio=len(greedy.selected) / len(optimum)))
    write_csv(results / 'quality.csv', quality)
    summary['quality'] = {'instances': len(quality),
                          'mean_ratio': statistics.mean(r['ratio'] for r in quality),
                          'max_ratio': max(r['ratio'] for r in quality),
                          'optimal_count': sum(r['ratio'] == 1 for r in quality)}
    metadata = {'seed': SEED, 'python': sys.version, 'platform': platform.platform(),
                'processor': platform.processor(), 'parameters': vars(args), 'summary': summary}
    (results / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    with (results / 'summary.tex').open('w') as f:
        for key, values in summary.items():
            prefix = ''.join(word.title() for word in key.split('_'))
            for stat, value in values.items():
                name = prefix + ''.join(word.title() for word in stat.split('_'))
                formatted = str(value) if isinstance(value, int) else f'{value:.3f}'
                f.write('\\newcommand{\\' + name + '}{' + formatted + '}\n')
    plots()
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
