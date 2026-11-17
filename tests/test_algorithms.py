import itertools
import random
import unittest
from src.algorithms import assign_volunteers, greedy_depots, exact_depots


def brute_flow(limits, demands, edges):
    best = 0
    for bits in itertools.product((0, 1), repeat=len(edges)):
        vl, sl = [0] * len(limits), [0] * len(demands)
        for bit, (v, j) in zip(bits, edges):
            vl[v] += bit
            sl[j] += bit
        if all(x <= b for x, b in zip(vl, limits)) and all(
                x <= d for x, d in zip(sl, demands)):
            best = max(best, sum(bits))
    return best


class AlgorithmTests(unittest.TestCase):
    def check_assignment(self, result, limits, demands, edges):
        self.assertEqual(result.value, len(result.assignments))
        self.assertEqual(len(set(result.assignments)), result.value)
        self.assertTrue(set(result.assignments) <= set(edges))
        for v, limit in enumerate(limits):
            self.assertLessEqual(sum(a == v for a, _ in result.assignments), limit)
        for j, demand in enumerate(demands):
            self.assertLessEqual(sum(b == j for _, b in result.assignments), demand)
        self.assertEqual(result.feasible, result.value == sum(demands))

    def test_reverse_edge_rerouting(self):
        r = assign_volunteers([1, 1], [1, 1], [(0, 0), (0, 1), (1, 0)])
        self.assertTrue(r.feasible)
        self.assertEqual(set(r.assignments), {(0, 1), (1, 0)})

    def test_flow_edge_cases(self):
        self.assertTrue(assign_volunteers([], [], []).feasible)
        self.assertFalse(assign_volunteers([], [1], []).feasible)
        self.assertTrue(assign_volunteers([0], [0], [(0, 0)]).feasible)
        self.assertEqual(assign_volunteers([4], [2], [(0, 0)] * 2).value, 1)
        self.assertFalse(assign_volunteers([2, 2], [1, 2], [(0, 0), (1, 0)]).feasible)

    def test_random_flow_against_exhaustive_oracle(self):
        rng = random.Random(20261117)
        for _ in range(180):
            nv, ns = rng.randint(0, 3), rng.randint(0, 3)
            limits = [rng.randint(0, 3) for _ in range(nv)]
            demands = [rng.randint(0, 3) for _ in range(ns)]
            edges = [(v, j) for v in range(nv) for j in range(ns) if rng.random() < .65]
            r = assign_volunteers(limits, demands, edges)
            self.check_assignment(r, limits, demands, edges)
            self.assertEqual(r.value, brute_flow(limits, demands, edges))

    def test_greedy_counterexample(self):
        sites = [{0, 1, 2, 3}, {0, 1, 4}, {2, 3, 5}]
        self.assertEqual(greedy_depots(6, sites).selected, [0, 1, 2])
        self.assertEqual(exact_depots(6, sites), [1, 2])

    def test_cover_edge_cases(self):
        self.assertEqual(greedy_depots(0, []).selected, [])
        self.assertFalse(greedy_depots(1, []).feasible)
        self.assertEqual(greedy_depots(3, [{0, 1}]).uncovered, {2})
        self.assertEqual(greedy_depots(2, [{0}, {0}, {1}]).selected, [0, 2])
        self.assertEqual(exact_depots(0, []), [])
        self.assertIsNone(exact_depots(1, []))

    def test_random_cover_against_exact_and_bound(self):
        rng = random.Random(17)
        for _ in range(180):
            n, m = rng.randint(0, 7), rng.randint(0, 9)
            sites = [{u for u in range(n) if rng.random() < .4} for _ in range(m)]
            r, opt = greedy_depots(n, sites), exact_depots(n, sites)
            self.assertEqual(r.feasible, opt is not None)
            if r.feasible:
                covered = set().union(*(sites[i] for i in r.selected)) if r.selected else set()
                self.assertEqual(covered, set(range(n)))
                h = sum(1 / k for k in range(1, n + 1))
                self.assertLessEqual(len(r.selected), h * len(opt) + 1e-9)
                self.assertLessEqual(r.rounds, min(n, m))

    def test_invalid_inputs(self):
        for args in [([-1], [1], []), ([1], [1], [(2, 0)]), ([1.5], [1], [])]:
            with self.assertRaises(ValueError):
                assign_volunteers(*args)
        with self.assertRaises(ValueError):
            greedy_depots(2, [{2}])


if __name__ == '__main__':
    unittest.main()
