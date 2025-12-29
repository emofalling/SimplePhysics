from physics2d import *


phys = Physics2D()
# 测试：台球碰撞
# 球
test = Circle(
    Pos2D(1, 10),
    1,
    1,
)
# 待撞的球
hit1 = Circle(
    Pos2D(10, 8.9),
    1,
    1,
)
# 待撞的球
hit2 = Circle(
    Pos2D(10, 11.1),
    1,
    1,
)

# test有向右的的初速度

test.velocity = Vector2D(10, 0)

# 添加到场景
phys.append(hit1)
phys.append(hit2)
phys.append(test)