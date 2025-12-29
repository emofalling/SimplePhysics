from physics2d import *


phys = Physics2D()
# 全局重力
phys.global_acceleration = Vector2D(0, -9.81)
# 地面(外圆)
floor = Circle(
    (20, -90),
    100,
    0,
    True
)
floor.name = "floor"

# 地面2
floor2 = Circle(
    (100, -80),
    100,
    0,
    True
)
floor2.name = "floor2"

# 球
ball = Circle(
    (21, 10),
    1,
    1
)
ball.name = "ball"

phys.extend([
    floor,
    floor2,
    ball
])