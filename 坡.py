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
# 坡
slope = Line(
    Pos2D(10-math.sqrt(2)/2, 10-math.sqrt(2)/2),
    Vector2D(1, -1),
    0,
    True
)
slope.name = "slope"
# 坡2
slope2 = Line(
    Pos2D(50, 1),
    Vector2D(1, 1),
    0,
    True
)
slope2.name = "slope2"
# 球
ball = Circle(
    Pos2D(10, 10),
    1,
    1,
)
ball.name = "ball"
# 0.5的动能损失
ball.collision_energy_loss = 0.3

# 击打的球
hit_ball = Circle(
    Pos2D(25, 3),
    1,
    1,
)
hit_ball.name = "hit_ball"


phys.objects.append(ball)
phys.objects.append(floor)
phys.objects.append(slope)
phys.objects.append(slope2)
phys.objects.append(hit_ball)