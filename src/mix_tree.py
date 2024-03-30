import concurrent
from typing import Union
from concurrent.futures import ThreadPoolExecutor

import chess.pgn
from stockfish import Stockfish

from src.config import Context
from src.core import Color, next_color

stockfish_path = "F:\\.Programy\\stockfish\\stockfish-windows-x86-64-avx2.exe"


class MixValues:
    def __int__(self, ctx: Context):
        self.time = ctx.get_value_or_default("time_per_node", 5 * 1000)
        self.cut_off = ctx.get_value_or_default("cut_off", 10)
        self.threshold = ctx.get_value_or_default("threshold", 5)
        self.debug = "--debug" in ctx.flags
        self.stockfish = ctx.get_value_or_default("stockfish", "NONE")


def get_best_for_node(node: 'InputNode', stockfish: Stockfish, time: int) -> str:
    path = node.path_from_root()
    stockfish.set_position(path)
    best = stockfish.get_best_move_time(time)
    return best


def get_best_for_node_threaded(key: str, node: 'InputNode', stockfish: Stockfish, time: int) -> tuple[
    str, 'InputNode', str]:
    path = node.path_from_root()
    print("P", path)
    stockfish.set_position(path)
    best = stockfish.get_best_move_time(time)
    return key, node, best


class InputNode:
    def __init__(self, color: Color, root: Union['InputNode', None], values: MixValues):
        self.count: int = 0
        self.children: dict[str, 'InputNode'] = dict()
        self.color = color
        self.root = root
        self.values = values

    def insert(self, result: int, node: chess.pgn.GameNode, depth):
        self.count += 1
        if not node.move.uci() in self.children:
            self.children[node.move.uci()] = InputNode(next_color(self.color), self.values)
        if node.variations and depth <= self.values.threshold:
            self.children[node.move.uci()].insert(result, node.variations[0], depth + 1)

    def path_from_root(self) -> list[str]:
        if self.root is None:
            return []
        return self.root.__path_from_root(self)

    def __path_from_root(self, last: 'InputNode') -> list[str]:
        if self.root is None:
            return [next(move for move, node in self.children.items() if node == last)]
        return self.root.__path_from_root(self) + [next(move for move, node in self.children.items() if node == last)]

    def to_dict(self):
        return self.__to_dict(get_best_for_node(self, Stockfish(stockfish_path), self.values.time))

    def __to_dict(self, best):
        result = []
        # find best move
        result.append(("best", best))

        # build tree recursively
        if self.children:
            non_empty_children = [(k, v) for k, v in self.children.items() if
                                  v.children and v.count > self.values.cut_off]
            data = [(k, v, Stockfish(stockfish_path)) for k, v in non_empty_children]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(get_best_for_node_threaded, k, v, s, self.values.time) for k, v, s in data]
            children_result = [f.result() for f in futures]
            children_dicts = [(k, v.__to_dict(b)) for k, v, b in children_result]

        else:
            children_dicts = []

        result += children_dicts
        return {k: v for (k, v) in result}
