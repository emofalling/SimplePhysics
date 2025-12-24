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
# 球
ball = Circle(
    Pos2D(2, 20),
    1,
    1
)
# 球的初速度
ball.velocity = Vector2D(5, 0)
# 动能损失
ball.collision_energy_loss = 0.25

# 添加到场景
phys.objects.append(floor)
phys.objects.append(ball)