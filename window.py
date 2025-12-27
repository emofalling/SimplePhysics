from PyQt5.QtWidgets import (
    # 基础组件
    QApplication, QMainWindow, 
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QSlider, QCheckBox, QSpinBox,
    # 提示枚举类
    QSizePolicy,
    # 图形
    QGraphicsView, QGraphicsScene, 
    QGraphicsItem, 
    # 长方形
    QGraphicsRectItem,
    # 圆
    QGraphicsEllipseItem,
    # 线
    QGraphicsLineItem,
    # 文字
    QGraphicsTextItem,
    # 点
    QGraphicsPathItem,
    # 实心多边形
    QGraphicsPolygonItem,
)

from PyQt5.QtCore import Qt, QPoint, QPointF

from PyQt5.QtGui import QPainter, QPen, QColor, QPolygonF, QBrush

from PyQt5.QtCore import QTimer, pyqtSignal

import time

from physics2d import *

from typing import Any

from 坡 import phys # 改这里可以更改测试项目

phys_obj_scene_map: dict[PhysicalObject, QGraphicsItem] = {}

scale: float = 33.0

# ms
tick: int = 1

class WinMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initwindow()
        self.initcontent()
        # 是否力学分析
        self.force_analysis: bool = True
        # 力学分析的组件缓存
        self.force_analysis_cache: list[QGraphicsItem] = []
        # 是否碰撞分析
        self.collision_analysis: bool = True
        # 碰撞分析的暂存事件列表
        self.collision_analysis_events: list[CollisionEvent] = []
        # 碰撞分析的组件缓存
        self.collision_analysis_cache: list[QGraphicsItem] = []
        # 绑回调
        self.bind_callbacks()
        # 单次定时器任务：initscene
        QTimer.singleShot(0, self.initscene)
        # self.initscene()
        # 定时器任务：single_step
        self.timer = QTimer()
        self.timer.timeout.connect(self.single_step)
        self.timer.start(tick)
        # 空格切换暂停/继续
        def keyPressEvent(event):
            if event.key() == Qt.Key.Key_Space:
                if self.timer.isActive():
                    self.phys_stop()
                else:
                    self.phys_start()
        self.keyPressEvent = keyPressEvent # type: ignore
        self.show()
    # 回调函数
    def collision_callback(self, event: CollisionEvent):
        if self.collision_analysis:
            self.collision_analysis_events.append(event)
    # 绑定回调
    def bind_callbacks(self):
        if phys.collision_handler is not None:
            phys.collision_handler = self.collision_callback # type: ignore
        else:
            base_callback = phys.collision_handler
            def combined_callback(event: CollisionEvent):
                if base_callback is not None:
                    base_callback(event)
                self.collision_callback(event)
            phys.collision_handler = combined_callback # type: ignore
    
    def phys_stop(self):
        self.timer.stop()
    def phys_start(self):
        self._last_time_end = time.time()
        self.timer.start(tick)

    def initwindow(self):
        self.setWindowTitle("Simple Physics")
        # 设置窗口大小
        self.resize(1000, 800)
    def initcontent(self):
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(self.main_layout)

        # 添加一个GraphicsView
        self.graphics_view = QGraphicsView()
        self.main_layout.addWidget(self.graphics_view)
        # 尽可能拉伸
        self.graphics_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # 无边框
        self.graphics_view.setFrameShape(QGraphicsView.Shape.NoFrame)

        # 添加一个GraphicsScene，拉伸
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        # 背景黑色
        self.graphics_scene.setBackgroundBrush(QColor(0, 0, 0))
        # 当self.graphics_view resize时，调整self.graphics_scene的大小
        def resizeEvent_graphics_view(event):
            self.graphics_scene.setSceneRect(0, 0, event.size().width(), event.size().height())
            QGraphicsView.resizeEvent(self.graphics_view, event)
        self.graphics_view.resizeEvent = resizeEvent_graphics_view

        # 控制面板
        self.control_panel = QWidget()
        self.main_layout.addWidget(self.control_panel)
        self.control_panel_layout = QVBoxLayout()
        self.control_panel.setLayout(self.control_panel_layout)
        # 刷新间隔
        self.refresh_interval_layout = QHBoxLayout()
        self.control_panel_layout.addLayout(self.refresh_interval_layout)
        self.refresh_interval_label = QLabel("刷新间隔(ms)")
        self.refresh_interval_layout.addWidget(self.refresh_interval_label)
        self.refresh_interval_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.refresh_interval_slider = QSpinBox()
        self.refresh_interval_slider.setMinimum(1)
        self.refresh_interval_slider.setMaximum(2**31-1)
        self.refresh_interval_slider.setValue(tick)
        self.refresh_interval_layout.addWidget(self.refresh_interval_slider)
        # 实际延迟
        self.refresh_ms_label = QLabel(f"实际延迟：-- ms")
        self.control_panel_layout.addWidget(self.refresh_ms_label)
        def refresh_interval_changed(value):
            global tick
            tick = value
            # 重设定时器
            if self.timer.isActive():
                self.timer.stop()
                self.timer.start(tick)
        self.refresh_interval_slider.valueChanged.connect(refresh_interval_changed)
        
    def __map_pos(self, x, y) -> tuple[float, float]:
        # 将物理坐标映射到屏幕坐标
        return (
            x*scale,
            self.graphics_scene.height() - y*scale
        )
    
    def draw_scene(self):
        # 销毁collision_analysis_cache的所有组件
        for item in self.collision_analysis_cache:
            self.graphics_scene.removeItem(item)
        self.collision_analysis_cache.clear()
        
        for obj in phys._fixed_objects+phys._active_objects:
            if isinstance(obj, Line):
                line: QGraphicsLineItem = phys_obj_scene_map[obj] # type: ignore
                start, end = obj.intpos_in_rect(self.graphics_view.width()/scale, self.graphics_view.height()/scale)
                if start is None or end is None:
                    continue # 相切，忽略
                line.setLine(*self.__map_pos(*start), *self.__map_pos(*end))
                # 检查颜色属性
                color = QColor(*getattr(obj, "color", (255, 255, 255)))
                line.setPen(QPen(color, 1))
            elif isinstance(obj, Circle):
                circle: QGraphicsEllipseItem = phys_obj_scene_map[obj] # type: ignore
                maped_pos = self.__map_pos(obj.pos.x, obj.pos.y)
                circle.setPos(*maped_pos)
                # 检查颜色属性
                color = QColor(*getattr(obj, "color", (255, 255, 255)))
                circle.setPen(QPen(color, 1))
    
    def draw_force_analysis(self):
        for item in self.force_analysis_cache:
            self.graphics_scene.removeItem(item)
        self.force_analysis_cache.clear()
        for obj in phys._active_objects:
            if isinstance(obj, Circle):
                # 绘制运动方向箭头
                start = obj.pos
                end = obj.pos + obj.velocity * 0.2
                line = QGraphicsLineItem(*self.__map_pos(start.x, start.y), *self.__map_pos(end.x, end.y))
                pen = QPen(QColor(100, 0, 0))
                pen.setWidth(2)
                line.setPen(pen)
                self.graphics_scene.addItem(line)
                self.force_analysis_cache.append(line)
                # 箭头
                direction = (end - start).normalize()
                pen = QPen(QColor(100, 0, 0))
                arrow_size = 0.2
                pen.setWidth(1)
                left_wing = end - direction.rotate90() * (arrow_size / 2)
                right_wing = end + direction.rotate90() * (arrow_size / 2)
                top_wing = end + direction * arrow_size
                # 实心多边形
                polygon = QPolygonF([
                    QPointF(*self.__map_pos(left_wing.x, left_wing.y)),
                    QPointF(*self.__map_pos(right_wing.x, right_wing.y)),
                    QPointF(*self.__map_pos(top_wing.x, top_wing.y)),
                ])
                arrow_item = QGraphicsPolygonItem(polygon)
                arrow_item.setBrush(QBrush(QColor(100, 0, 0)))
                arrow_item.setPen(pen)
                self.graphics_scene.addItem(arrow_item)
                self.force_analysis_cache.append(arrow_item)
                


        
    def draw_collision_analysis(self, events: list[CollisionEvent]):
        for event in events:
            # 碰撞点
            point = self.__map_pos(event.pos.x, event.pos.y)
            # 创建一个实心点，无边框
            radius = 2
            ellipse = QGraphicsEllipseItem(point[0]-radius, point[1]-radius, radius*2, radius*2)
            ellipse.setBrush(QColor(0, 255, 0))
            ellipse.setPen(QPen(Qt.GlobalColor.transparent))
            self.graphics_scene.addItem(ellipse)
            self.collision_analysis_cache.append(ellipse)
            # 绘制碰撞平面：先计算线起点和终点
            normal_length = 3
            normal_start = event.pos - event.normal.rotate90() * normal_length
            normal_end = event.pos + event.normal.rotate90() * normal_length
            # 添加一条虚线
            line = QGraphicsLineItem(*self.__map_pos(normal_start.x, normal_start.y), *self.__map_pos(normal_end.x, normal_end.y))
            pen = QPen(QColor(128, 128, 128))
            pen.setStyle(Qt.PenStyle.DashLine)
            line.setPen(pen)
            self.graphics_scene.addItem(line)
            self.collision_analysis_cache.append(line)
        # 若有碰撞点，则暂停
        if len(events) > 0:
            # self.phys_stop()
            pass

    def initscene(self):
        # 根据phys初始化场景
        for obj in phys._fixed_objects+phys._active_objects:
            if isinstance(obj, Line):
                # 计算点向式直线与x轴和y轴的交点
                start, end = obj.intpos_in_rect(self.graphics_view.width()/scale, self.graphics_view.height()/scale)
                print(obj.name, self.graphics_view.width()/scale, self.graphics_view.height()/scale, "->", start, end)
                if start is None or end is None:
                    start = (-1, 1)
                    end = (-1, 1)
                # 添加一条线
                line = QGraphicsLineItem(*self.__map_pos(*start), *self.__map_pos(*end))
                self.graphics_scene.addItem(line)
                phys_obj_scene_map[obj] = line
            elif isinstance(obj, Circle):
                # 添加一个圆
                radius = obj.radius
                circle = QGraphicsEllipseItem(-radius*scale, -radius*scale, radius*2*scale, radius*2*scale)
                circle.setPos(*self.__map_pos(obj.pos.x, obj.pos.y))
                self.graphics_scene.addItem(circle)
                phys_obj_scene_map[obj] = circle
            else:
                raise Exception("未知物理对象类型")
        self.draw_scene()
    actual_delay: float = tick / 1000
    def single_step(self):
        # 仅模拟一步
        phys.update(self.actual_delay)
        # 更新场景
        self.draw_scene()
        # 如果开启力学分析，绘制力学分析
        if self.force_analysis:
            self.draw_force_analysis()
        # 如果开启碰撞分析，绘制碰撞分析
        if self.collision_analysis:
            self.draw_collision_analysis(self.collision_analysis_events)
            # 清空事件列表
            self.collision_analysis_events.clear()
        # 更新延迟
        time_end = time.time()
        last_time_end = getattr(self, "_last_time_end", None)
        if isinstance(last_time_end, float):
            actual_delay = (time_end - last_time_end)
            self.refresh_ms_label.setText(f"实际延迟：{actual_delay * 1000:.2f} ms")
            self.actual_delay = actual_delay
        self._last_time_end = time_end
        


        


if __name__ == "__main__":
    app = QApplication([])
    win = WinMain()
    app.exec_()
