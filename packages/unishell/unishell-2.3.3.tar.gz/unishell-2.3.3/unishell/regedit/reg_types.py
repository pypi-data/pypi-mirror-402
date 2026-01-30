import platform
if platform.system() != "Windows":
    from .._internal.funcs import FakeObj
    def __getattr__(name):
        return FakeObj()
else:
    try:
        from unishell_win.regedit.reg_types import *
    except ImportError:
        raise ImportError("Not found module unishell_win. pip install unishell_win")
    