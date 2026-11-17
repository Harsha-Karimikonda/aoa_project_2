"""Replay recorded instances and verify the supplied CSVs, without retiming."""
import csv
import json
import statistics
from pathlib import Path
from src.algorithms import assign_volunteers, greedy_depots, exact_depots
from src.experiments import flow_instance, cover_instance


def main():
    root = Path(__file__).resolve().parents[1]
    results = root / 'results'
    with (results / 'raw_timings.csv').open() as f:
        raw = list(csv.DictReader(f))
    assert len(raw) == 60
    for row in raw:
        k, seed = int(row['size']), int(row['seed'])
        if row['problem'] == 'flow':
            result = assign_volunteers(*flow_instance(k, row['family'], seed))
            assert result.feasible and result.value == 2 * k
            operations = result.edge_scans
            assert int(row['bound']) == 2 * result.edges * (result.value + 1)
        else:
            sites = cover_instance(k, row['family'], seed)
            result = greedy_depots(k, sites)
            assert result.feasible
            operations = result.membership_checks
            assert int(row['bound']) == k * sum(map(len, sites))
            if row['family'] == 'singleton':
                assert operations == k * (k + 1) // 2
        assert operations == int(row['operations']) <= int(row['bound'])
        assert 0 < float(row['min_seconds']) <= float(row['seconds']) <= float(row['max_seconds'])
    for problem, families in [('flow', ['sparse', 'dense']),
                              ('cover', ['singleton', 'dense'])]:
        for family in families:
            with (results / (problem + '_' + family + '.csv')).open() as f:
                aggregate = list(csv.DictReader(f))
            assert len(aggregate) == 5
            for row in aggregate:
                group = [r for r in raw if r['problem'] == problem and
                         r['family'] == family and r['size'] == row['size']]
                assert len(group) == 3
                for key in ['seconds', 'operations', 'bound', 'incidence', 'rounds']:
                    assert float(row[key]) == statistics.median(float(r[key]) for r in group)
    with (results / 'quality.csv').open() as f:
        quality = list(csv.DictReader(f))
    assert len(quality) == 100
    # Quality uses a different density from the scaling generator.
    import random
    for row in quality:
        rng = random.Random(int(row['seed']))
        n, m = int(row['communities']), int(row['candidates'])
        sites = [{u for u in range(n) if rng.random() < .25} for _ in range(m)]
        for u in range(n):
            sites[rng.randrange(m)].add(u)
        opt = exact_depots(n, sites)
        greedy = greedy_depots(n, sites)
        assert len(opt) == int(row['optimum'])
        assert len(greedy.selected) == int(row['greedy'])
        assert float(row['ratio']) == len(greedy.selected) / len(opt)
    metadata = json.loads((results / 'metadata.json').read_text())
    assert metadata['summary']['quality']['optimal_count'] == sum(
        row['greedy'] == row['optimum'] for row in quality)
    print('PASS: all 60 recorded operation counts reproduced exactly')
    print('PASS: every count satisfies its theoretical bound')
    print('PASS: singleton counts equal k(k+1)/2')
    print('PASS: all 20 aggregate CSV rows match the raw medians')
    print('PASS: all 100 quality results reproduced against the exact oracle')


if __name__ == '__main__':
    main()
