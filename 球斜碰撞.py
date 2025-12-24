from physics2d import *


phys = Physics2D()
# 球
test = Circle(
    Pos2D(1, 10),
    1,
    1,
)
# 待撞的球
hit = Circle(
    Pos2D(10, 8.9),
    1,
    1,
)

# test有向右的的初速度

test.velocity = Vector2D(10, 0)

# 添加到场景
phys.objects.append(hit)
phys.objects.append(test)