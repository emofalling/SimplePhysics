# 仅用于电脑端，屏蔽@micropython.native

from warnings import warn

# 定义native空装饰器
def native(func):
    return func

def const(expr: int):
    if not isinstance(expr, int):
        warn(f"micropython.const applied to non-int value: {expr!r}", RuntimeWarning)
    return expr