import concurrent.futures
from typing import Union

import chess.pgn
from stockfish import Stockfish

from src.config import Context
from src.core import Color, next_color, Node

EMPTY = 'X'


class MixValues:
    def __init__(self, ctx: Context):
        self.time = ctx.get_value_or_default("time_per_node", 5 * 1000)
        self.cut_off = ctx.get_value_or_default("cut_off", 10)
        self.max_depth = ctx.get_value_or_default("max_depth", 5)
        self.threads = ctx.get_value_or_default("threads", 10)
        self.stockfish = ctx.get_value_or_exit("stockfish")

    def to_dict(self):
        return {
            "time_per_node": self.time,
            "cut_off": self.cut_off,
            "max_depth": self.max_depth,
        }


def get_best_for_node(node: 'MixNode', stockfish_path: str, time: int) -> str:
    stockfish = Stockfish(stockfish_path)
    path = node.path_from_root()
    # print("P", path)
    stockfish.set_position(path)
    best = stockfish.get_best_move_time(time)
    return best


class MixNode(Node):
    def __init__(self, color: Color, root: Union['MixNode', None], values: MixValues):
        self.count: int = 0
        self.evaluation: str = EMPTY
        self.children: dict[str, 'MixNode'] = dict()
        self.color = color
        self.root = root
        self.values = values

    def insert(self, result: int, node: chess.pgn.GameNode, depth):
        self.count += 1
        if not node.move.uci() in self.children:
            self.children[node.move.uci()] = MixNode(next_color(self.color), self, self.values)
        if node.variations and depth <= self.values.max_depth:
            self.children[node.move.uci()].insert(result, node.variations[0], depth + 1)

    def cut_size(self):
        return 1 + sum(
            map(lambda x: x.cut_size(), filter(lambda x: x.count > self.values.cut_off, self.children.values())))

    def eval_size(self):
        result = sum(
            map(lambda x: x.eval_size(),
                filter(lambda x: x.count > self.values.cut_off, self.children.values())))
        if self.evaluation == EMPTY:
            result += 1
        return result

    def size(self):
        return 1 + sum(map(lambda x: x.size(), self.children.values()))

    def path_from_root(self) -> list[str]:
        if self.root is None:
            return []
        return self.root.__path_from_root(self)

    def __path_from_root(self, last: 'MixNode') -> list[str]:
        if self.root is None:
            return [next(move for move, node in self.children.items() if node == last)]
        return self.root.__path_from_root(self) + [next(move for move, node in self.children.items() if node == last)]

    def to_dict(self):
        if self.children:
            non_empty_children = [(k, v) for k, v in self.children.items() if
                                  v.children and v.count > self.values.cut_off]
            children_dicts = [x for x in (list((k, v.to_dict()) for (k, v) in non_empty_children)) if x[1] is not None]
        else:
            children_dicts = []

        return {k: v for (k, v) in [("best", self.evaluation)] + children_dicts}

    def get_nodes_list(self):
        result = []

        if self.count > self.values.cut_off:
            result += [x for xs in self.children.values() for x in xs.get_nodes_list()]
            if self.evaluation == EMPTY:
                result.append(self)
        return result

    def evaluate(self):
        nodes = self.get_nodes_list()

        with concurrent.futures.ThreadPoolExecutor(self.values.threads) as executor:
            futures = [(executor.submit(get_best_for_node, n, self.values.stockfish, self.values.time), n)
                       for n in nodes]
        results = [(f.result(), n) for f, n in futures]

        for e, n in results:
            n.evaluation = e

    def load_eval(self, prev):
        self.evaluation = prev["best"]
        for move, node in [(m, n) for m, n in self.children.items() if m in prev]:
            node.load_eval(prev[move])
