from physics2d import *


phys = Physics2D()

# 左侧挡板
pad = Line(
    Pos2D(1, 0), 
    Vector2D(0, 1),
    0.0,
    True
)


# 球1
ball1 = Circle(
    Pos2D(5, 10), 
    1.0,
    1.0,
)

# 球2，质量是10的平方幂次
ball2 = Circle(
    Pos2D(10, 10), 
    1.0,
    100000000.0,
)

# 有向左的初速度

ball2.velocity = Vector2D(-1, 0) # 速度太大会穿模

phys.append(pad)
phys.append(ball1)
phys.append(ball2)

# ball1的碰撞次数
ball1_count = 0
def collision_handler(plat):
    global ball1_count
    ball1_count += 1
    print("ball1碰撞次数：", ball1_count)

ball1.collision_handler = collision_handler # type: ignore

# 接下来总能发现，碰撞次数是pi的整倍次