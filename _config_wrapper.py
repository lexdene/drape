# -*- coding: utf-8 -*-
''' default config for drape '''


class ConfigWrapper:
    def __init__(self):
        self.__modules = []

    def register(self, module):
        self.__modules.insert(0, module)

    def __getattr__(self, key):
        for module in self.__modules:
            value = getattr(module, key, None)
            if value is not None:
                return value

        return object.__getattribute__(self, key)
