"""Exact volunteer assignment and greedy depot coverage; standard library only."""
from collections import deque
from dataclasses import dataclass
from itertools import combinations


@dataclass
class FlowResult:
    feasible: bool
    value: int
    assignments: list[tuple[int, int]]
    bfs_calls: int
    edge_scans: int
    vertices: int
    edges: int


def _counts(values):
    if any(type(x) is not int or x < 0 for x in values):
        raise ValueError("capacities must be nonnegative integers")


def assign_volunteers(limits, demands, eligibility):
    """IDs index limits/demands; return a maximum partial assignment if infeasible.

    Edges are deduplicated and sorted, making output deterministic. Each residual
    edge is [destination, reverse-edge index, remaining capacity].
    """
    _counts(limits)
    _counts(demands)
    nv, ns = len(limits), len(demands)
    eligible = sorted(set(eligibility))
    if any(type(v) is not int or type(j) is not int or
           not 0 <= v < nv or not 0 <= j < ns for v, j in eligible):
        raise ValueError("invalid volunteer or shift ID")
    source, sink = nv + ns, nv + ns + 1
    graph = [[] for _ in range(sink + 1)]

    def add_edge(a, b, cap):
        index = len(graph[a])
        graph[a].append([b, len(graph[b]), cap])
        graph[b].append([a, index, 0])
        return index

    for v, capacity in enumerate(limits):
        add_edge(source, v, capacity)
    references = []
    for v, j in eligible:
        references.append((v, j, add_edge(v, nv + j, 1)))
    for j, demand in enumerate(demands):
        add_edge(nv + j, sink, demand)
    value = scans = calls = 0
    while True:
        parent = [None] * len(graph)
        parent[source] = (-1, -1)
        queue = deque([source])
        calls += 1
        while queue and parent[sink] is None:
            a = queue.popleft()
            for index, edge in enumerate(graph[a]):
                scans += 1
                b, _, cap = edge
                if cap > 0 and parent[b] is None:
                    parent[b] = (a, index)
                    queue.append(b)
                    if b == sink:
                        break
        if parent[sink] is None:
            break
        # Every augmenting path contains a unit-capacity eligibility edge.
        amount, b = None, sink
        while b != source:
            a, index = parent[b]
            cap = graph[a][index][2]
            amount = cap if amount is None else min(amount, cap)
            b = a
        b = sink
        while b != source:
            a, index = parent[b]
            edge = graph[a][index]
            edge[2] -= amount
            graph[b][edge[1]][2] += amount
            b = a
        value += amount
    assignments = [(v, j) for v, j, index in references
                   if graph[v][index][2] == 0]
    return FlowResult(value == sum(demands), value, assignments, calls, scans,
                      len(graph), nv + ns + len(eligible))


@dataclass
class CoverResult:
    feasible: bool
    selected: list[int]
    uncovered: set[int]
    membership_checks: int
    rounds: int


def _coverage(n, coverage):
    _counts([n])
    sets = [tuple(sorted(set(s))) for s in coverage]
    if any(type(u) is not int or not 0 <= u < n for s in sets for u in s):
        raise ValueError("community IDs must lie in range(n)")
    return sets


def greedy_depots(n, coverage):
    """Unweighted Set Cover; break ties by lowest candidate index.

    Explicit membership scans, rather than opaque set intersections, make the
    measured operation count directly comparable with the analysis.
    """
    sets = _coverage(n, coverage)
    uncovered = set(range(n))
    reachable = set().union(*sets) if sets else set()
    if not uncovered <= reachable:
        return CoverResult(False, [], uncovered - reachable, 0, 0)
    selected, checks, rounds = [], 0, 0
    used = set()
    while uncovered:
        best, gain = None, 0
        rounds += 1
        for i, site in enumerate(sets):
            if i in used:
                continue
            current = 0
            for community in site:
                checks += 1
                current += community in uncovered
            if current > gain:
                best, gain = i, current
        # The initial union check guarantees a positive-gain choice.
        assert best is not None
        used.add(best)
        selected.append(best)
        uncovered.difference_update(sets[best])
    return CoverResult(True, selected, uncovered, checks, rounds)


def exact_depots(n, coverage):
    """Exponential oracle for SMALL test/quality instances, never large timings."""
    sets = [set(s) for s in _coverage(n, coverage)]
    target = set(range(n))
    for k in range(len(sets) + 1):
        for choice in combinations(range(len(sets)), k):
            covered = set().union(*(sets[i] for i in choice)) if choice else set()
            if covered == target:
                return list(choice)
    return None
