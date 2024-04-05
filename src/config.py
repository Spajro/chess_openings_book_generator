import sys


class Context:
    def __init__(self, params, values, flags):
        self.params = params
        self.values = values
        self.flags = flags

    def get_value_or_default(self, key, default):
        if key in self.values:
            return type(default)(self.values[key][0])
        return default


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
            exit(-1)
    return Context(params, values, flags)
