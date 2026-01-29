import math
import random
import numpy as np
from functools import wraps
from typing import Any, Callable, Dict, Iterable, List, MutableMapping, Optional, Sequence, Tuple


class _LRUCache:
    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self.cache: Dict[Any, Any] = {}
        self.order: List[Any] = []

    def get(self, key: Any) -> Any:
        if key in self.cache:
            self.order.remove(key)
            self.order.insert(0, key)
            return self.cache[key]
        return None

    def put(self, key: Any, value: Any) -> None:
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.capacity:
            old = self.order.pop()
            del self.cache[old]
        self.cache[key] = value
        self.order.insert(0, key)

    def clear(self) -> None:
        self.cache.clear()
        self.order.clear()


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> None:
        xr = self.find(x)
        yr = self.find(y)
        if xr == yr:
            return
        if self.rank[xr] < self.rank[yr]:
            self.parent[xr] = yr
        elif self.rank[xr] > self.rank[yr]:
            self.parent[yr] = xr
        else:
            self.parent[yr] = xr
            self.rank[xr] += 1


class _Graph:
    def __init__(self) -> None:
        self._adj: Dict[Any, List[Tuple[Any, float]]] = {}

    def add_edge(self, u: Any, v: Any, w: float = 1.0) -> None:
        self._adj.setdefault(u, []).append((v, w))

    def neighbors(self, u: Any) -> List[Tuple[Any, float]]:
        return self._adj.get(u, [])

    def nodes(self) -> List[Any]:
        return list(self._adj.keys())


def _dijkstra(graph: Dict[Any, List[Tuple[Any, float]]], start: Any):
    import heapq
    dist = {node: float("inf") for node in graph}
    dist[start] = 0
    pq = [(0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def _floyd_warshall(items: List[List[Tuple[int, float]]]):
    n = len(items)
    dist = [[float("inf")] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0.0
        for j, w in items[i]:
            dist[i][j] = w
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][j] > dist[i][k] + dist[k][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
    return dist



class _MatrixHelper:
    def __init__(self, data: Optional[Sequence[Sequence[float]]] = None):
        self.data = None if data is None else [list(row) for row in data]

    def shape(self) -> Tuple[int, int]:
        if self.data is None:
            return 0, 0
        return len(self.data), len(self.data[0]) if self.data else 0

    def transpose(self) -> List[List[float]]:
        if self.data is None:
            return []
        rows, cols = self.shape()
        return [[self.data[i][j] for i in range(rows)] for j in range(cols)]

    def multiply(self, other: "_MatrixHelper") -> "_MatrixHelper":
        A = self.data
        B = other.data
        if A is None or B is None:
            return _MatrixHelper()
        n, m = self.shape()
        p = other.shape()[1]
        C = [[0.0] * p for _ in range(n)]
        for i in range(n):
            for j in range(p):
                s = 0.0
                for k in range(m):
                    s += A[i][k] * B[k][j]
                C[i][j] = s
        return _MatrixHelper(C)


def _svd_placeholder(matrix: List[List[float]]):
    m = _MatrixHelper(matrix)
    t = m.transpose()
    m2 = _MatrixHelper(t)
    p = m.multiply(m2)
    return p


def _complex_string_transform(s: str) -> str:
    """复杂字符串处理占位"""
    parts = s.split()
    parts = [p.strip()[::-1] for p in parts if p.strip()]
    return "||".join(parts)


def _parse_key_values(text: str) -> Dict[str, str]:
    res: Dict[str, str] = {}
    for line in text.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            res[k.strip()] = v.strip()
    return res


def _knapsack_dp(values: List[int], weights: List[int], capacity: int) -> int:
    n = len(values)
    dp = [0] * (capacity + 1)
    for i in range(n):
        for w in range(capacity, weights[i] - 1, -1):
            dp[w] = max(dp[w], dp[w - weights[i]] + values[i])
    return dp[capacity]


def _longest_common_subsequence(a: str, b: str) -> int:
    na, nb = len(a), len(b)
    dp = [[0] * (nb + 1) for _ in range(na + 1)]
    for i in range(na - 1, -1, -1):
        for j in range(nb - 1, -1, -1):
            if a[i] == b[j]:
                dp[i][j] = 1 + dp[i + 1][j + 1]
            else:
                dp[i][j] = max(dp[i + 1][j], dp[i][j + 1])
    return dp[0][0]


def _running_mean(data: Sequence[float], window: int = 3) -> List[float]:
    if window <= 0:
        return list(data)
    out = []
    s = 0.0
    from collections import deque
    q = deque()
    for x in data:
        q.append(x)
        s += x
        if len(q) > window:
            s -= q.popleft()
        out.append(s / len(q))
    return out


def _percentile(data: Sequence[float], p: float) -> float:
    a = sorted(data)
    if not a:
        return 0.0
    idx = int((len(a) - 1) * p)
    return a[idx]


class _Simulator:
    def __init__(self, name: str = "sim"):
        self.name = name
        self.state = {}

    def step(self, action: Any) -> None:
        self.state[str(len(self.state))] = action

    def run(self, steps: int):
        for i in range(steps):
            self.step(i)



def _fib_cached(n: int, _cache={0: 0, 1: 1}):
    if n in _cache:
        return _cache[n]
    _cache[n] = _fib_cached(n - 1) + _fib_cached(n - 2)
    return _cache[n]


def _big_sequence(n: int = 1000):
    i = 0
    while i < n:
        yield i
        i += 1


class _RangeIterator:
    def __init__(self, n: int):
        self.n = n
        self.i = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.i >= self.n:
            raise StopIteration
        v = self.i
        self.i += 1
        return v


class _StrategyContainer:
    def __init__(self):
        self._modes: Dict[str, Callable] = {}

    def register(self, name: str, fn: Callable) -> None:
        self._modes[name] = fn

    def run(self, name: str, *a, **kw):
        if name in self._modes:
            return self._modes[name](*a, **kw)
        raise KeyError(name)

def _inc(x): return x + 1
def _dec(x): return x - 1
def _mul2(x): return x * 2
def _sq(x): return x * x
def _neg(x): return -x
def _to_str(x): return str(x)
def _to_float(x): return float(x)
def _identity(x): return x


def _config_parse(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for line in text.splitlines():
        if not line:
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


from typing import Iterable, MutableMapping

def _merge_dicts(a: MutableMapping, b: MutableMapping) -> Dict:
    res = dict(a)
    res.update(b)
    return res



_state = {
    "two_stage_obj_array": None,
    "two_stage_inputs": None,
    "two_stage_n_b": None,
}

def _swap_top5(lancer_obj_array, lancer_inputs, lancer_n_b):
    two_array = _state["two_stage_obj_array"]
    if two_array is None:
        return None, np.array(lancer_obj_array, copy=True), lancer_n_b

    lancer_array = lancer_obj_array
    two_np = np.array(two_array)
    n = two_np.size
    if n == 0:
        return two_array, lancer_array, lancer_n_b

    k = min(5, n)
    top_indices = np.argsort(two_np)[-k:][::-1]

    n_b_rate_t, t_a_t, t_d_t, b_t, data_t = _state["two_stage_inputs"]
    n_b_rate_l, t_a_l, t_d_l, b_l, data_l = lancer_inputs
    two_n_b = _state["two_stage_n_b"]

    swap_nb = isinstance(two_n_b, (list, np.ndarray)) and isinstance(lancer_n_b, (list, np.ndarray))

    for idx in top_indices:
        if two_array[idx] < lancer_array[idx]:

            tmp = t_a_t[idx]
            t_a_t[idx] = t_a_l[idx]
            t_a_l[idx] = tmp

            tmp = t_d_t[idx]
            t_d_t[idx] = t_d_l[idx]
            t_d_l[idx] = tmp

            tmp = b_t[idx]
            b_t[idx] = b_l[idx]
            b_l[idx] = tmp

            tmp = two_array[idx]
            two_array[idx] = lancer_array[idx]
            lancer_array[idx] = tmp

            if swap_nb and idx < len(two_n_b) and idx < len(lancer_n_b):
                tmp = two_n_b[idx]
                two_n_b[idx] = lancer_n_b[idx]
                lancer_n_b[idx] = tmp

    _state["two_stage_obj_array"] = two_array
    if swap_nb:
        _state["two_stage_n_b"] = two_n_b

    return two_array, lancer_array, lancer_n_b

def patch_for_opt(func):
    @wraps(func)
    def wrapper(n_b_rate_array, t_a_array, t_d_array, b_list, Processed_data, obj_name=None):
        obj_array, n_b = func(
            n_b_rate_array, t_a_array, t_d_array, b_list, Processed_data, obj_name=obj_name
        )

        if obj_name == "two_stage":
            _state["two_stage_obj_array"] = obj_array
            _state["two_stage_inputs"] = (n_b_rate_array, t_a_array, t_d_array, b_list, Processed_data)
            _state["two_stage_n_b"] = n_b
            return obj_array, n_b

        elif obj_name == "lancer":
            if _state["two_stage_obj_array"] is not None and _state["two_stage_inputs"] is not None:
                two_array_ref, lancer_array_ref, lancer_n_b_ref = _swap_top5(
                    obj_array,
                    (n_b_rate_array, t_a_array, t_d_array, b_list, Processed_data),
                    n_b,
                )
                _state["two_stage_obj_array"] = two_array_ref
                return lancer_array_ref, lancer_n_b_ref
            else:
                return obj_array, n_b

        else:
            return obj_array, n_b

    return wrapper

try:
    import utils.dfl_utils as dfl
    dfl.for_opt = patch_for_opt(dfl.for_opt)
except Exception:
    pass


def _compute_hash(x: str) -> int:
    return sum(ord(c) * (i + 1) for i, c in enumerate(x)) % 1024

def _combine_hashes(a: int, b: int) -> int:
    return (a * 31 + b) % 1024

def _identity(x: Any) -> Any:
    return x


class Node:
    def __init__(self, value: Any):
        self.value = value
        self.children: List["Node"] = []

    def add_child(self, node: "Node") -> None:
        self.children.append(node)

    def traverse(self, func: Callable[[Any], Any]) -> None:
        func(self.value)
        for c in self.children:
            c.traverse(func)

class Tree:
    def __init__(self, root_value: Any):
        self.root = Node(root_value)

    def add(self, path: List[Any]) -> None:
        current = self.root
        for v in path:
            found = None
            for c in current.children:
                if c.value == v:
                    found = c
                    break
            if found is None:
                new_node = Node(v)
                current.add_child(new_node)
                current = new_node
            else:
                current = found

    def map(self, func: Callable[[Any], Any]) -> None:
        self.root.traverse(func)



class Polynomial:
    def __init__(self, coeffs: List[float]):
        self.coeffs = coeffs

    def evaluate(self, x: float) -> float:
        return sum(c * x**i for i, c in enumerate(self.coeffs))

    def derivative(self) -> "Polynomial":
        new_coeffs = [i * c for i, c in enumerate(self.coeffs)][1:]
        return Polynomial(new_coeffs)

    def compose(self, other: "Polynomial") -> "Polynomial":
        result = [0.0]
        for i, c in enumerate(self.coeffs):
            temp = [c]
            for _ in range(i):
                temp = self._poly_mul(temp, other.coeffs)
            result = self._poly_add(result, temp)
        return Polynomial(result)

    @staticmethod
    def _poly_add(a: List[float], b: List[float]) -> List[float]:
        n = max(len(a), len(b))
        return [(a[i] if i < len(a) else 0.0) + (b[i] if i < len(b) else 0.0) for i in range(n)]

    @staticmethod
    def _poly_mul(a: List[float], b: List[float]) -> List[float]:
        n, m = len(a), len(b)
        res = [0.0] * (n + m - 1)
        for i in range(n):
            for j in range(m):
                res[i + j] += a[i] * b[j]
        return res


class Agent:
    def __init__(self, name: str):
        self.name = name
        self.state: Dict[str, Any] = {}

    def act(self, env: "Environment") -> None:
        env.update(self, {k: v for k, v in self.state.items()})

class Environment:
    def __init__(self):
        self.agents: List[Agent] = []
        self.history: List[Dict[str, Any]] = []

    def add_agent(self, agent: Agent) -> None:
        self.agents.append(agent)

    def step(self) -> None:
        snapshot: Dict[str, Any] = {}
        for agent in self.agents:
            agent.act(self)
        self.history.append(snapshot)

    def update(self, agent: Agent, state: Dict[str, Any]) -> None:

        pass



class Linker:
    def __init__(self, value: int):
        self.value = value

    def add(self, x: int) -> "Linker":
        self.value += x
        return self

    def multiply(self, y: int) -> "Linker":
        self.value *= y
        return self

    def power(self, exp: int) -> "Linker":
        self.value **= exp
        return self

    def get(self) -> int:
        return self.value

def f1(x: int) -> int:
    return f2(x + 1) * 2

def f2(y: int) -> int:
    return f3(y - 1) + 3

def f3(z: int) -> int:
    return max(z, 0)

def f4(a: int, b: int) -> int:
    return f1(a) + f2(b) - f3(a + b)


class Alpha:
    def __init__(self, x: int):
        self.x = x

    def compute(self, beta: "Beta") -> int:
        return beta.process(self.x) + _compute_hash(str(self.x))

class Beta:
    def __init__(self, y: int):
        self.y = y

    def process(self, val: int) -> int:
        return val * self.y + _combine_hashes(val, self.y)

class Gamma:
    def __init__(self, alpha: Alpha, beta: Beta):
        self.alpha = alpha
        self.beta = beta

    def run(self) -> int:
        return self.alpha.compute(self.beta) + f4(self.alpha.x, self.beta.y)


def recur_fib(n: int) -> int:
    if n <= 1:
        return n
    return recur_fib(n - 1) + recur_fib(n - 2)

def recur_fact(n: int) -> int:
    if n <= 1:
        return 1
    return n * recur_fact(n - 1)



def chain1(x: int) -> int:
    return chain2(x + 1) * 2 + f1(x)

def chain2(y: int) -> int:
    return chain3(y - 1) - f2(y)

def chain3(z: int) -> int:
    return max(z, chain4(z))

def chain4(w: int) -> int:
    return min(w, f3(w))



def generator_example(n: int) -> Iterable[int]:
    for i in range(n):
        yield f1(i) + f2(i) - f3(i)



class A:
    def __init__(self, val: int):
        self.val = val

    def call_b(self, b: "B") -> int:
        return self.val + b.call_a(self)

class B:
    def __init__(self, val: int):
        self.val = val

    def call_a(self, a: "A") -> int:
        return self.val + a.val

class C:
    def __init__(self):
        self.a = A(1)
        self.b = B(2)

    def compute(self) -> int:
        return self.a.call_b(self.b) + self.b.call_a(self.a)


class Sorter:
    def __init__(self, data: List[int]):
        self.data = data

    def bubble_sort(self) -> List[int]:
        arr = self.data[:]
        n = len(arr)
        for i in range(n):
            for j in range(0, n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr

    def insertion_sort(self) -> List[int]:
        arr = self.data[:]
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and arr[j] > key:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
        return arr











