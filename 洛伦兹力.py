from physics2d import *


phys = Physics2D()

# 重力
phys.global_acceleration = Vector2D(0, -9.81)

# 球(粒子)
ball = Circle(
    Pos2D(20, 20),
    0.1,
    1,
)

# 给定初速度
ball.velocity = Vector2D(10, 0)

phys.objects.append(ball)

ball_charge = 1.0
lorenz_scale = 10.0

def update_callback(dt: float):
    # 洛伦兹力垂直于速度方向
    ball.extra_force = ball.velocity.rotate90() * ball_charge * ball_charge / ball.mass * lorenz_scale # type: ignore

phys.update_callback = update_callback # type: ignore