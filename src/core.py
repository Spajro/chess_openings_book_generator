from enum import Enum

import chess.pgn


class Color(Enum):
    WHITE = 1
    BLACK = 2


def next_color(color: Color) -> Color:
    match color:
        case Color.WHITE:
            return Color.BLACK
        case Color.BLACK:
            return Color.WHITE


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


class Node:
    def insert(self, result: int, node: chess.pgn.GameNode, depth: int):
        pass

    def to_dict(self):
        pass
