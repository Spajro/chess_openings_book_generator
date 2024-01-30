import json
import sys
from enum import Enum
from operator import itemgetter

import chess.pgn

NODE_CUT_OFF = 500
EVAL_CUT_OFF = 200


class Color(Enum):
    WHITE = 1
    BLACK = 2


def next_color(color: Color) -> Color:
    match color:
        case Color.WHITE:
            return Color.BLACK
        case Color.BLACK:
            return Color.WHITE


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


def convert_result(result: str) -> int:
    match result:
        case "0-1":
            return -1
        case "1-0":
            return 1
        case "1/2-1/2":
            return 0
        case _:
            return 0


if len(sys.argv) < 4:
    print("Usage: generator.py PGN_PATH JSON_PATH MAX_DEPTH")
    exit(1)

pgn_path = sys.argv[1]
json_path = sys.argv[2]
threshold = int(sys.argv[3])

pgn = open(pgn_path, encoding="utf-8")
root = InputNode(Color.WHITE)
game = chess.pgn.read_game(pgn)
count = 0
while game is not None:
    if game.variations:
        root.insert(convert_result(game.headers['Result']), game.variations[0], 1)
    game = chess.pgn.read_game(pgn)
    count += 1

print("Games count: ", count)

pgn.close()

json = json.dumps(root.to_dict())
f = open(json_path, "w")
f.write(json)
f.close()
