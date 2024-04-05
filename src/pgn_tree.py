from operator import itemgetter

import chess.pgn

from src.config import Context
from src.core import Color, next_color, Node


class PgnValues:
    def __init__(self, ctx: Context):
        self.node_cut_off = ctx.get_value_or_default("-node_cut_off", 500)
        self.eval_cut_off = ctx.get_value_or_default("-eval_cut_off", 10)
        self.max_depth = ctx.get_value_or_default("-max_depth", 5)
        self.debug = "--debug" in ctx.flags


class PgnNode(Node):
    def __init__(self, color: Color, values: PgnValues):
        self.score: int = 0
        self.count: int = 0
        self.children: dict[str, 'PgnNode'] = dict()
        self.color = color
        self.values = values

    def insert(self, result: int, node: chess.pgn.GameNode, depth):
        self.score += result
        self.count += 1
        if not node.move.uci() in self.children:
            self.children[node.move.uci()] = PgnNode(next_color(self.color), self.values)
        if node.variations and depth <= self.values.max_depth:
            self.children[node.move.uci()].insert(result, node.variations[0], depth + 1)

    def eval(self):
        if self.count == 0:
            return 0
        return self.score / self.count

    def to_dict(self):
        # find best move
        candidates = list((k, v.eval()) for (k, v) in self.children.items() if v.count > self.values.eval_cut_off)

        if len(candidates) == 0:
            return None

        if self.color == Color.WHITE:
            best = max(candidates, key=itemgetter(1))[0]
        else:
            best = min(candidates, key=itemgetter(1))[0]

        result = list(("best", best))

        # append debug
        if self.values.debug:
            result.append(("score", self.score))
            result.append(("count", self.count))
            result.append(("eval", self.eval()))

        # build tree recursively
        if self.children:
            non_empty_children = [(k, v) for k, v in self.children.items() if
                                  v.children and v.count > self.values.node_cut_off]
            children_dicts = [x for x in (list((k, v.to_dict()) for (k, v) in non_empty_children)) if x[1] is not None]
        else:
            children_dicts = []

        result += children_dicts
        return {k: v for (k, v) in result}
