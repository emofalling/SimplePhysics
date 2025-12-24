# 仅用于电脑端，屏蔽@micropython.native

# 定义native空装饰器
def native(func):
    return func

def const(expr):
    return expr