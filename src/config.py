import sys


class Context:
    def __init__(self, params, flags):
        self.params = params
        self.flags = flags

    def get_value_or_default(self, key: str, default):
        flag = self.__key_to_flag(key)
        if flag in self.flags and len(self.flags[flag]) > 0:
            return type(default)(self.flags[flag][0])
        return default

    def get_value_or_exit(self, key: str):
        flag = self.__key_to_flag(key)
        if flag in self.flags and len(self.flags[flag]) > 0:
            return self.flags[flag][0]
        print("No such value", key)
        exit(-1)

    def has_flag(self, key):
        flag = self.__key_to_flag(key)
        return flag in self.flags

    def __key_to_flag(self, key: str) -> str:
        return "--" + key


def __is_flag(string: str):
    return string[0] == '-'


def parse_argv() -> Context:
    tokens = sys.argv[1:]

    params = []
    flags = {}
    index = 0

    while index < len(tokens) and not __is_flag(tokens[index]):
        params.append(tokens[index])
        index += 1

    while index < len(tokens):
        key = tokens[index]
        index += 1

        flags[key] = []
        while index < len(tokens) and not __is_flag(tokens[index]):
            flags[key].append(tokens[index])
            index += 1

    return Context(params, flags)
