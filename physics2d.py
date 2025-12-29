import math

import micropython

DIV_EPLISON = 1e-10

class Vector2D:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
    
    @micropython.native
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector2D):
            return False
        return self.x == other.x and self.y == other.y

    @micropython.native
    def __add__(self, other):
        return type(self)(self.x + other.x, self.y + other.y)

    @micropython.native
    def __sub__(self, other):
        return type(self)(self.x - other.x, self.y - other.y)

    @micropython.native
    def __mul__(self, other):
        if isinstance(other, Vector2D):
            return self.x * other.x + self.y * other.y
        elif isinstance(other, (int, float)):
            return type(self)(self.x * other, self.y * other)
        else:
            raise TypeError("Unsupported operand type(s) for *: '{}' and '{}'".format(type(self).__name__, type(other).__name__))
    
    @micropython.native
    def __rmul__(self, other):
        return self * other
        # 注意：在MicroPython中，不会考虑调用__rmul__，而是直接在对方对象上调用__mul__，因此需要注意乘法顺序
    
    @micropython.native
    def cross(self, other):
        if isinstance(other, Vector2D):
            return self.x * other.y - self.y * other.x
        else:
            raise TypeError("Unsupported operand type(s) for cross: '{}' and '{}'".format(type(self).__name__, type(other).__name__))

    @micropython.native
    def __truediv__(self, other):
        if isinstance(other, (int, float)):
            return type(self)(self.x / other, self.y / other)
        else:
            raise TypeError("Unsupported operand type(s) for /: '{}' and '{}'".format(type(self).__name__, type(other).__name__))
    
    @micropython.native
    def normalize(self, eps: float = DIV_EPLISON, zero_replace: tuple = (1, 0)):
        """返回单位向量。若长度小于eps(默认DIV_EPLISON)，则返回zero_replace(默认为单位向量(1, 0))"""
        abs_val = abs(self)
        if abs_val < eps:
            return type(self)(*zero_replace)
        return self / abs_val

    @micropython.native
    def __neg__(self):
        return type(self)(-self.x, -self.y)

    @micropython.native
    def abs_square(self):
        return self.x ** 2 + self.y ** 2
    
    @micropython.native
    def __abs__(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    @micropython.native
    def __repr__(self):
        return "Vector2D({}, {})".format(self.x, self.y)
    
    @micropython.native
    def rotate90(self):
        return type(self)(-self.y, self.x)

class Pos2D(Vector2D):
    pass

@micropython.native
def inter_line_and_linesegment(line_pos: Pos2D, line_dir: Vector2D, seg_start: Pos2D, seg_end: Pos2D):
    """计算点向式直线与线段的交点  
    line_pos: 直线上一点  
    line_dir: 直线方向向量。已经归一化  
    seg_start: 线段起点  
    seg_end: 线段终点  
    返回交点坐标Pos2D，若无交点则返回None"""
    # 线段方向向量
    seg_dir = seg_end - seg_start
    # 计算行列式
    det = line_dir.cross(seg_dir)
    if abs(det) < DIV_EPLISON:
        # 平行或重合
        return None
    # 计算参数t和u
    diff = seg_start - line_pos
    t = diff.cross(seg_dir) / det
    u = diff.cross(line_dir) / det
    # 检查u是否在[0, 1]范围内
    if u < 0 or u > 1:
        return None
    # 计算交点坐标
    intersection = line_pos + line_dir * t
    return intersection

class CollisionEvent:
    """碰撞点。仅内部使用"""
    def __init__(self, 
                 obj1: 'PhysicalObject',
                obj2: 'PhysicalObject',
                 pos: Pos2D, 
                 normal: Vector2D
    ):
        """
        pos: 碰撞点位置  
        normal: 碰撞点单位法向量
        """
        self.obj1 = obj1
        self.obj2 = obj2
        self.pos = pos
        self.normal = normal
        self.obj1_last_velocity = obj1.velocity # 碰撞前速度
        self.obj2_last_velocity = obj2.velocity # 碰撞前速度


class PhysicalObject:
    """通用物理对象"""
    def __init__(self, 
                 pos: Pos2D | tuple[float, float],
                 mass: float,
                 fixed: bool = False
    ):  
        # 预先检查
        if mass < DIV_EPLISON and not fixed:
            raise ValueError("Mass must be positive")
        self.name = repr(self)
        if isinstance(pos, tuple):
            self.pos = Pos2D(pos[0], pos[1])
        elif isinstance(pos, Vector2D):
            self.pos = pos
        self.last_pos: Pos2D | None = None # 上一帧位置，供连续碰撞采样使用。仅在打开了该功能时使用
        self.mass = mass
        self.fixed = fixed
        self.extra_force = Vector2D(0, 0)
        self.extra_acceleration = Vector2D(0, 0)
        self.velocity = Vector2D(0, 0)
        self.collision_handler = None
        """碰撞处理函数，参数: 碰撞点。动量重分配之后调用。phys的collision_handler更优先"""
        self.collision_energy_loss = 0.0
        """碰撞能量损失，0-1之间，0表示无能量损失，1表示完全能量损失"""
    def collision(self, other, phys: 'Physics2D') -> CollisionEvent | None:
        raise NotImplementedError

class Circle(PhysicalObject):
    def __init__(self, 
                 pos: Pos2D | tuple[float, float],
                 radius: float,
                 mass: float, 
                 fixed: bool = False
    ):
        super().__init__(pos, mass, fixed)
        if radius < DIV_EPLISON:
            raise ValueError("Radius must be positive")
        self.radius = radius
    
    @micropython.native
    def collision(self, other: PhysicalObject, phys: 'Physics2D'):
        if isinstance(other, Circle):
            # 提前计算一些数值
            pos_d = other.pos - self.pos # 指向other.pos
            radius_sum = self.radius + other.radius
            # 对于一方fixed,碰撞位置：固定圆的圆周上与另一圆心连线的交点
            if self.fixed:
                pos = self.pos + pos_d.normalize() * self.radius
            elif other.fixed: # other.fixed
                pos = other.pos - pos_d.normalize() * other.radius
            # 对于双方均非fixed,碰撞位置：两圆心的加权中点
            else:
                pos = self.pos + (pos_d) * (self.radius / radius_sum)
            dis_square = pos_d.abs_square()
            # 若两圆心距离小于两圆半径之和，则碰撞。为优化逻辑，这里检查是否不碰撞
            if dis_square >= radius_sum ** 2:
                return None
            dis = math.sqrt(dis_square)
            # 两圆心单位法向量，任意方向
            normal = pos_d.normalize() # 注意：该向量指向other.pos
            # 优化：
            # 如果两圆均不固定，则按质量比，按碰撞法向移动两圆心，使两圆恰好接触
            # 如果一圆固定，则移动另一圆心，使两圆恰好接触
            # 穿透深度
            penetration = radius_sum - dis

            # 运动校正
            if phys.basic_correction_enabled:
                if self.fixed:
                    other.pos = pos + normal * other.radius
                elif other.fixed:
                    self.pos = pos - normal * self.radius
                elif phys.extend_correction_enabled: # 双方均非fixed，且启用扩展校正
                    # 仅在阈值范围内进行碰撞处理
                    # 方案1: 质量大的移动少
                    """
                    total_mass = self.mass + other.mass
                    self.pos += normal * (penetration * other.mass / total_mass)
                    other.pos -= normal * (penetration * self.mass / total_mass)
                    """
                    # 方案2: 按半径平均分配移动量
                    self.pos -= normal * (penetration * (other.radius / radius_sum))
                    other.pos += normal * (penetration * (self.radius / radius_sum))
            return CollisionEvent(self, other, pos, normal)
        else:
            return other.collision(self, phys)

class Line(PhysicalObject):
    def __init__(self, 
                 pos: Pos2D | tuple[float, float],
                 direction: Vector2D | tuple[float, float],
                 mass: float, 
                 fixed: bool = False
    ):
        super().__init__(pos, mass, fixed)
        if isinstance(direction, tuple):
            direction = Vector2D(direction[0], direction[1])
        if direction.abs_square() < DIV_EPLISON:
            raise ValueError("Direction vector cannot be zero")
        self.direction = direction.normalize()
    
    @micropython.native
    def collision(self, other: PhysicalObject, phys: 'Physics2D'):
        if isinstance(other, Line):
            raise NotImplementedError
        elif isinstance(other, Circle):
            # 圆心到直线上一点p的向量
            c = other.pos
            p = self.pos
            d = self.direction

            # 连续采样：检测两帧之间的圆心运动轨迹是否与直线相交
            if phys.continuous_collision_sampling_enabled and other.last_pos is not None:
                intersection = inter_line_and_linesegment(p, d, other.last_pos, other.pos)
                if intersection is not None:
                    # 计算last_pos与intersection的垂足向量
                    linepos_to_lastpos = other.last_pos - p
                    normal = linepos_to_lastpos - d * (d * linepos_to_lastpos)
                    normal = normal.normalize() # 指向circle.pos
                    # 运动校正:如果线是固定的，将圆的坐标设置为恰好让线接触圆的边界而不进入圆内
                    if phys.basic_correction_enabled and self.fixed:
                        other.pos = intersection + normal * other.radius
                    return CollisionEvent(self, other, intersection, normal)

            # 投影参数t
            t = d * (c - p)
            # 垂足坐标
            foot = p + d * t

            # 从垂足指向圆心的向量
            vec = c - foot

            dist_square = vec.abs_square()

            if dist_square >= other.radius ** 2:
                return None
            
            dist = math.sqrt(dist_square)

            # 碰撞点：圆与直线的接触点（在圆的边界上，沿法向从圆心后退半径距离）
            # 注意：直线无限长，碰撞点应该是圆心沿法向向直线移动半径距离的点
            if dist == 0:
                # 圆心正好在直线上，法向取垂直于direction的任意向量
                normal = d.rotate90()  # 垂直向量
            else:
                normal = vec.normalize()

            # 运动校正:如果线是固定的，将圆的坐标设置为恰好让线接触圆的边界而不进入圆内
            if phys.basic_correction_enabled and self.fixed:
                other.pos = foot + normal * other.radius

            return CollisionEvent(self, other, foot, normal)
        else:
            return other.collision(self, phys)
    
    @micropython.native
    def intpos_in_rect(self, w: float, h: float):
        """计算自身与矩形rect的交点  
        认为rect的左下角是(0, 0)，右上角是(w, h)
        返回((x1, y1), (x2, y2))，表示两交点坐标。
        若直线恰好与矩形相切，返回((x, y), None)。
        返回(None, None)表示无交点
        """
        x0, y0 = self.pos.x, self.pos.y
        dx, dy = self.direction.x, self.direction.y

        # 特殊情况：线水平
        if dy == 0:
            return ((0.0, y0), (w, y0))
        # 特殊情况：线垂直
        elif dx == 0:
            return ((x0, 0.0), (x0, h))
        
        # 计算每个可能可用的t值，满足(xi, yi) = (x0 + dx*t, y0 + dy*t)
        t_values = (
            # 左边界交点
            -x0 / dx, 
            # 右边界交点
            (w - x0) / dx, 
            # 下边界交点
            -y0 / dy, 
            # 上边界交点
            (h - y0) / dy,
        )

        # 检查是否在边界内
        points: list[tuple[float, float]] = []
        for t in t_values:
            x = x0 + dx * t
            y = y0 + dy * t
            if 0 <= x <= w and 0 <= y <= h:
                points.append((x, y))
        
        if len(points) == 0:
            return None, None
        elif len(points) == 1:
            return points[0], None
        else:
            return points[0], points[1]


        


class Physics2D:
    def __init__(self):
        self._active_objects: list[PhysicalObject] = []
        self._fixed_objects: list[PhysicalObject] = []
        self.global_force = Vector2D(0, 0)
        self.global_acceleration = Vector2D(0, 0)
        self.collision_handler = None
        """collision_handler参数列表：collision_point。优先于各物体的collision_handler调用"""
        self.update_callback = None
        """update_callback参数列表：dt"""
        self.basic_correction_enabled = True
        """基本穿透校正。能确保在大多数场景中不会出现异常"""
        self.extend_correction_enabled = False
        """更激进的穿透校正。在极端场景下可能会出现异常"""
        self.continuous_collision_sampling_enabled = True
        """基于数学的连续碰撞采样。在高速运动时能有效减少穿透现象，略微增加计算量"""

    @micropython.native
    def update_obj_move(self, obj: PhysicalObject, dt: float):
        """仅更新单个物体的移动，不考虑碰撞"""
        if obj.fixed:
            return
        obj_acceleration = (self.global_force + obj.extra_force) / obj.mass + (obj.extra_acceleration + self.global_acceleration)
        obj.velocity += obj_acceleration * dt
        obj.pos += obj.velocity * dt

    @micropython.native
    def update_move(self, dt: float):
        """仅更新移动，不考虑碰撞"""
        for obj in self._active_objects:
            if self.continuous_collision_sampling_enabled:
                # 记录上一帧位置
                obj.last_pos = Pos2D(obj.pos.x, obj.pos.y)
            self.update_obj_move(obj, dt)
    
    @micropython.native
    def update_collision(self):
        """更新碰撞"""
        # 碰撞检查与处理函数
        @micropython.native
        def handle_collision(obj1: PhysicalObject, obj2: PhysicalObject):
            # 检查碰撞
            collision_point: CollisionEvent | None = obj1.collision(obj2, self)
            if collision_point is None:
                return
            
            # 计算各自的动能保留率
            obj1_p = 1.0 - obj1.collision_energy_loss
            obj2_p = 1.0 - obj2.collision_energy_loss
            # print(f"{obj1.name}与{obj2.name}碰撞")
            # 处理碰撞
            # 根据动量守恒和动能守恒计算碰撞后的速度

            # 根据法向向量计算切向向量
            tangent = collision_point.normal.rotate90()
            
            # 两物体的速度分解到法向和切向
            v1n = obj1.velocity * collision_point.normal 
            v1t = obj1.velocity * tangent
            v2n = obj2.velocity * collision_point.normal
            v2t = obj2.velocity * tangent

            # 损失动能
            v1n *= obj1_p
            v2n *= obj2_p

            # 根据fixed属性判断是否需要更新速度
            if obj1.fixed:
                # obj2的法向反弹
                v2n = -v2n
                # 损失对面的动能
                v1n *= obj2_p
            elif obj2.fixed:
                # obj1的法向反弹
                v1n = -v1n
                # 损失对面的动能
                v2n *= obj1_p
            else: # 计算
                # 法向上两物体碰撞后的速度。为了加速计算，这里缓存部分变量。
                m1_p_m2 = obj1.mass + obj2.mass
                v1n, v2n = (
                    (v1n * (obj1.mass - obj2.mass) + 2 * obj2.mass * v2n) / m1_p_m2, 
                    (v2n * (obj2.mass - obj1.mass) + 2 * obj1.mass * v1n) / m1_p_m2
                )
            

            # 合并切向和法向速度
            obj1.velocity = collision_point.normal * v1n + tangent * v1t # type: ignore
            obj2.velocity = collision_point.normal * v2n + tangent * v2t # type: ignore

            # 调用handler
            if self.collision_handler is not None:
                self.collision_handler(collision_point)
            if obj1.collision_handler is not None:
                obj1.collision_handler(collision_point)
            if obj2.collision_handler is not None:
                obj2.collision_handler(collision_point)

        # 两两检查碰撞
        # 1. fixed-active
        for obj1 in self._fixed_objects:
            for obj2 in self._active_objects:
                handle_collision(obj1, obj2)
        # 2. active-active
        n = len(self._active_objects)
        for i in range(n):
            for j in range(i + 1, n):
                obj1 = self._active_objects[i]
                obj2 = self._active_objects[j]
                handle_collision(obj1, obj2)
    @micropython.native
    def update(self, dt: float):
        """更新。"""
        if self.update_callback is not None:
            self.update_callback(dt)
        self.update_move(dt)
        self.update_collision()
    def append(self, obj: PhysicalObject):
        if obj.fixed:
            self._fixed_objects.append(obj)
        else:
            self._active_objects.append(obj)
    def extend(self, objs: list[PhysicalObject]):
        for obj in objs:
            self.append(obj)
    def remove(self, obj: PhysicalObject):
        if obj.fixed:
            self._fixed_objects.remove(obj)
        else:
            self._active_objects.remove(obj)
    def setFixed(self, obj: PhysicalObject, fixed: bool):
        if obj.fixed == fixed:
            return
        obj.fixed = fixed
        if fixed:
            self._active_objects.remove(obj)
            self._fixed_objects.append(obj)
        else:
            self._fixed_objects.remove(obj)
            self._active_objects.append(obj)
