from physics2d import *


phys = Physics2D()
# phys.continuous_collision_sampling_enabled = False
phys.extend_correction_enabled = True

space_LR = (1, 30)  # 左右侧墙壁位置
space_TB = (1, 20)  # 顶底侧墙壁位置
# 左侧墙壁
wall_left = Line(
    Pos2D(space_LR[0], 0),
    Vector2D(0, 1),
    0,
    True
)
# 右侧墙壁
wall_right = Line(
    Pos2D(space_LR[1], 0),
    Vector2D(0, 1),
    0,
    True
)
# 下侧墙壁
wall_bottom = Line(
    Pos2D(0, space_TB[0]),
    Vector2D(1, 0),
    0,
    True
)
# 上侧墙壁
wall_top = Line(
    Pos2D(0, space_TB[1]),
    Vector2D(1, 0),
    0,
    True
)
# 中心球
center_ball = Circle(
    Pos2D((space_LR[0]+space_LR[1])/2, (space_TB[0]+space_TB[1])/2),
    1,
    100
)
center_ball.name = "Ball Center"
# 有右上的初速度
center_ball.velocity = Vector2D(10, 10)
# 自定义属性：颜色
center_ball.color = (255, 0, 0) # type: ignore

phys.extend([
    wall_left,
    wall_right,
    wall_bottom,
    wall_top,
    center_ball
])

# 左右侧各3个球
for i in range(2):
    for j in range(3):
        ball = Circle(
            Pos2D(5 if i else 25, 7 + j * 3),
            1,
            1
        )
        ball.name = f"Ball LR {i}-{j}"
        phys.append(ball)
# 顶底侧各3个球
for i in range(2):
    for j in range(3):
        ball = Circle(
            Pos2D(12 + j * 3, 5 if i else 15),
            1,
            1
        )
        ball.name = f"Ball TB {i}-{j}"
        phys.append(ball)

# 回调
def on_collision(dt: float):
    # 检查是否有球出界，若有则发送信息
    for obj in phys._active_objects:
        if isinstance(obj, Circle):
            if not (space_LR[0] <= obj.pos.x <= space_LR[1] and space_TB[0] <= obj.pos.y <= space_TB[1]) and not getattr(obj, "is_out_of_bounds", False):
                print(f"[Out of Bounds] {obj.name} out of bounds at position ({obj.pos.x:.2f}, {obj.pos.y:.2f})")
                obj.is_out_of_bounds = True # type: ignore
                obj.color = (0, 0, 255)  # type: ignore
                phys.setFixed(obj, True)

phys.update_callback = on_collision # type: ignore