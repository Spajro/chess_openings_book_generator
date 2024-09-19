import datetime
import json
import time

import chess.pgn

from src import config, pgn_tree, mix_tree
from src.config import Context
from src.core import Color, convert_result
from src.mix_tree import MixValues
from src.pgn_tree import PgnValues


def __write(path, v):
    f = open(path, "w")
    f.write(v)
    f.close()


def __read(root, ctx: Context):
    pgn = open(ctx.get_value_or_exit("pgn"), encoding="utf-8")
    game = chess.pgn.read_game(pgn)
    count = 0
    while game is not None:
        # tc = int(game.headers["TimeControl"].split('+')[0])
        # if tc >= 600 and game.variations:
        if game.variations:
            root.insert(convert_result(game.headers['Result']), game.variations[0], 1)
        game = chess.pgn.read_game(pgn)
        count += 1

    print("Games count: ", count)
    pgn.close()
    return root


def __get_root(ctx: Context):
    stock = ctx.has_flag("stockfish")
    pgn = ctx.has_flag("pgn")
    if pgn and stock:
        return mix_tree.MixNode(Color.WHITE, None, MixValues(ctx))
    if pgn:
        return pgn_tree.PgnNode(Color.WHITE, PgnValues(ctx))
    print("Cant create root node ", stock, pgn)
    exit(-1)


def __estimate(tree, ctx: Context):
    size = tree.size()
    cut_size = tree.cut_size()
    estimate = (cut_size * ctx.get_value_or_default("time_per_node", 5 * 1000)) / 1000 / 10
    date = datetime.datetime.fromtimestamp(time.time() + estimate).strftime('%c')
    print("Nodes: ", size,
          "\nNodes after cut: ", cut_size,
          "\nTime estimation: ", estimate, "s",
          "\nFinish time estimation: ", date
          )


def __to_json(tree,pgn):
    jsonable = tree.to_dict()
    jsonable["values"] = tree.values.to_dict()
    jsonable["values"]["pgn"]=pgn
    return json.dumps(jsonable)


ctx = config.parse_argv()
json_path = ctx.params[0]
root = __get_root(ctx)
tree = __read(root, ctx)
if ctx.has_flag("stockfish"):
    __estimate(tree, ctx)
    tree.eval()
__write(json_path, __to_json(tree,ctx.get_value_or_exit("pgn")))
