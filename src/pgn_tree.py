import sys
from operator import itemgetter

import chess.pgn

from src.core import Color, next_color

# Parametry
NODE_CUT_OFF = 500
EVAL_CUT_OFF = 200
debug = "--debug" in sys.argv
threshold = 5


class InputNode:
    def __init__(self, color: Color):
        self.score: int = 0
        self.count: int = 0
        self.children: dict[str, 'InputNode'] = dict()
        self.color = color

    def insert(self, result: int, node: chess.pgn.GameNode, depth):
        self.score += result
        self.count += 1
        if not node.move.uci() in self.children:
            self.children[node.move.uci()] = InputNode(next_color(self.color))
        if node.variations and depth <= threshold:
            self.children[node.move.uci()].insert(result, node.variations[0], depth + 1)

    def eval(self):
        if self.count == 0:
            return 0
        return self.score / self.count

    def to_dict(self):
        result = []

        # find best move
        candidates = list((k, v.eval()) for (k, v) in self.children.items() if v.count > EVAL_CUT_OFF)

        if len(candidates) == 0:
            return None

        if self.color == Color.WHITE:
            best = max(candidates, key=itemgetter(1))[0]
        else:
            best = min(candidates, key=itemgetter(1))[0]

        result.append(("best", best))

        # append debug
        if debug:
            result.append(("score", self.score))
            result.append(("count", self.count))
            result.append(("eval", self.eval()))

        # build tree recursively
        if self.children:
            non_empty_children = [(k, v) for k, v in self.children.items() if v.children and v.count > NODE_CUT_OFF]
            children_dicts = [x for x in (list((k, v.to_dict()) for (k, v) in non_empty_children)) if x[1] is not None]
        else:
            children_dicts = []

        result += children_dicts
        return {k: v for (k, v) in result}
