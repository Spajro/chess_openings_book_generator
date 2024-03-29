import sys


def __is_key(string: str):
    return string[0] == '-'


def parse_argv(params_count: int):
    tokens = sys.argv[1:]
    params = tokens[:params_count]
    rest = tokens[params_count:]
    values = {}
    flags = []
    index = 0
    while index < len(rest):
        if __is_key(rest[index]):
            key = rest[index]
            if index + 1 == len(rest) or __is_key(rest[index + 1]):
                flags.append(key)
                index += 1
            else:
                index += 1
                temp = []
                while index < len(rest) and not __is_key(rest[index]):
                    temp.append(rest[index])
                    index += 1
                values[key] = temp
        else:
            print("ERROR")
    return {
        "params": params,
        "values": values,
        "flags": flags,
    }