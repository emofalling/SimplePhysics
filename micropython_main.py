from physics2d import *
from devlib import *

import utime # type: ignore

SCR_WIDTH = 128
SCR_HEIGHT = 64

phys = Physics2D()
# 左侧墙壁
wall_left = Line(
    Pos2D(1, 0),
    Vector2D(0, 1),
    0,
    True
)
# 右侧墙壁
wall_right = Line(
    Pos2D(30, 0),
    Vector2D(0, 1),
    0,
    True
)
# 下侧墙壁
wall_bottom = Line(
    Pos2D(0, 1),
    Vector2D(1, 0),
    0,
    True
)
# 上侧墙壁
wall_top = Line(
    Pos2D(0, 20),
    Vector2D(1, 0),
    0,
    True
)
# 中心球
ball = Circle(
    Pos2D(15, 10),
    1,
    100
)
# 有右上的初速度
ball.velocity = Vector2D(3, 3)
# 自定义属性：颜色
ball.color = (255, 0, 0) # type: ignore

phys.extend([
    wall_left,
    wall_right,
    wall_bottom,
    wall_top,
    ball
])

# 左右侧各3个球
for i in range(2):
    for j in range(3):
        ball = Circle(
            Pos2D(5 if i else 25, 7 + j * 3),
            1,
            1
        )
        phys.append(ball)
# 顶底侧各3个球
for i in range(2):
    for j in range(3):
        ball = Circle(
            Pos2D(12 + j * 3, 5 if i else 15),
            1,
            1
        )
        phys.append(ball)



scale = 3

def drawAnObject(obj):
    if isinstance(obj, Circle):
        oled.circle(round(obj.pos.x*scale), SCR_HEIGHT-round(obj.pos.y*scale), round(obj.radius*scale), 1)
    elif isinstance(obj, Line):
        start, end = obj.intpos_in_rect(SCR_WIDTH/scale, SCR_HEIGHT/scale)
        if start is None or end is None:
            return # 忽略
        oled.line(round(start[0]*scale), SCR_HEIGHT-round(start[1]*scale), # type: ignore
                  round(end[0]*scale), SCR_HEIGHT-round(end[1]*scale), 1) # type: ignore

def drawPhysics():
    oled.fill(0)
    for obj in phys._fixed_objects:
        drawAnObject(obj)
    for obj in phys._active_objects:
        drawAnObject(obj)
    oled.show()

td = 0.0

while True:
    ts = utime.ticks_us()
    phys.update(td / 1000000)
    drawPhysics()
    td = utime.ticks_diff(utime.ticks_us(), ts)