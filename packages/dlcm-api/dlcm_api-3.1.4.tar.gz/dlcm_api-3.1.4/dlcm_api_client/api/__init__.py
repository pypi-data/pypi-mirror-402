# flake8: noqa

import os
import importlib
import sys
import types

class _LazyApiModule(types.ModuleType):
    def __init__(self, name):
        super().__init__(name)
        self.__path__ = [os.path.dirname(__file__)]
        self._module_names = [
            fname[:-3] for fname in os.listdir(self.__path__[0])
            if fname.endswith('_api.py') and not fname.startswith('__')
        ]

    def __getattr__(self, name):
        if name not in self._module_names:
            raise AttributeError(f'No such API module: {name}')
        module = importlib.import_module(f'{__name__}.{name}')
        setattr(self, name, module)
        return module

    def __dir__(self):
        return self._module_names

sys.modules[__name__] = _LazyApiModule(__name__)
