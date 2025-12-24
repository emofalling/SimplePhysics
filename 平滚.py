from physics2d import *


phys = Physics2D()
# 全局重力
phys.global_acceleration = Vector2D(0, -9.81)
# 地面
floor = Line(
    Pos2D(0, 1),
    Vector2D(1, 0),
    0,
    True
)
floor.name = "floor"
# 球
ball = Circle(
    Pos2D(2, 2),
    1,
    1,
)
ball.name = "ball"
# 球有向右的初速度
ball.velocity = Vector2D(5, 0)


phys.objects.append(ball)
phys.objects.append(floor)