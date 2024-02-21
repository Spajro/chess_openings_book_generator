import json

import chess.pgn

from src import config, pgn_tree, mix_tree
from src.core import Color, convert_result


def __write(path, v):
    f = open(path, "w")
    f.write(v)
    f.close()


def __read(pgn_path: str, root):
    pgn = open(pgn_path, encoding="utf-8")
    game = chess.pgn.read_game(pgn)
    count = 0
    while game is not None:
        tc = int(game.headers["TimeControl"].split('+')[0])
        if tc >= 600 and game.variations:
            # if game.variations:
            root.insert(convert_result(game.headers['Result']), game.variations[0], 1)
        game = chess.pgn.read_game(pgn)
        count += 1

    print("Games count: ", count)
    pgn.close()
    return root


def __get_root_for_mode(mode: str):
    match mode:
        case 'pgn':
            return pgn_tree.InputNode(Color.WHITE)
        case 'mix':
            return mix_tree.InputNode(Color.WHITE, None)
        case 'raw':
            return None
        case _:
            exit(-1)


args = config.parse_argv(2)
mode = args['params'][0]
json_path = args['params'][1]
pgn_path = args['params'][2]
root = __get_root_for_mode(mode)

__write(json_path, json.dumps(__read(pgn_path, root).to_dict()))
