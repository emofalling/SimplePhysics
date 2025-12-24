from PyQt5.QtWidgets import (
    # 基础组件
    QApplication, QMainWindow, 
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QSlider, QCheckBox,
    # 提示枚举类
    QSizePolicy,
    # 图形
    QGraphicsView, QGraphicsScene, 
    QAbstractGraphicsShapeItem, 
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
)

from PyQt5.QtCore import Qt

from PyQt5.QtGui import QPainter, QPen, QColor

from PyQt5.QtCore import QTimer, pyqtSignal

from physics2d import *

from typing import Any

from 平面反弹 import phys # 改这里可以更改测试项目

phys_obj_scene_map: dict[PhysicalObject, Any] = {}

scale: float = 33.0

# ms
tick: int = 1

class WinMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initwindow()
        self.initcontent()
        # 单次定时器任务：initscene
        QTimer.singleShot(0, self.initscene)
        # 定时器任务：single_step
        self.timer = QTimer()
        self.timer.timeout.connect(self.single_step)
        self.timer.start(tick)
        # 空格切换暂停/继续
        def keyPressEvent(event):
            if event.key() == Qt.Key.Key_Space:
                if self.timer.isActive():
                    self.timer.stop()
                else:
                    self.timer.start()
        self.keyPressEvent = keyPressEvent # type: ignore
        self.show()

    def initwindow(self):
        self.setWindowTitle("Simple Physics")
        # 设置窗口大小
        self.resize(800, 600)
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
    def __map_pos(self, x, y) -> tuple[float, float]:
        # 将物理坐标映射到屏幕坐标
        return (
            x*scale,
            self.graphics_scene.height() - y*scale
        )

    def initscene(self):
        # 根据phys初始化场景
        for obj in phys._fixed_objects+phys._active_objects:
            if isinstance(obj, Line):
                # 计算点向式直线与x轴和y轴的交点
                start, end = obj.intpos_in_rect(self.graphics_view.width()/scale, self.graphics_view.height()/scale)
                if start is None or end is None:
                    continue # 相切，忽略
                # 添加一条线
                line = QGraphicsLineItem(*self.__map_pos(*start), *self.__map_pos(*end))
                line.setPen(QPen(QColor(255, 255, 255), 1))
                self.graphics_scene.addItem(line)
                phys_obj_scene_map[obj] = line
            elif isinstance(obj, Circle):
                # 添加一个圆
                radius = obj.radius
                circle = QGraphicsEllipseItem(-radius*scale, -radius*scale, radius*2*scale, radius*2*scale)
                circle.setPos(*self.__map_pos(obj.pos.x, obj.pos.y))
                # 检查颜色属性
                color = QColor(*getattr(obj, "color", (255, 255, 255)))
                circle.setPen(QPen(color, 1))
                self.graphics_scene.addItem(circle)
                phys_obj_scene_map[obj] = circle
    def single_step(self):
        # 仅模拟一步
        phys.update(tick / 1000)
        # 更新场景
        for obj in phys._fixed_objects+phys._active_objects:
            if isinstance(obj, Line):
                line: QGraphicsLineItem = phys_obj_scene_map[obj]
                start, end = obj.intpos_in_rect(self.graphics_view.width()/scale, self.graphics_view.height()/scale)
                if start is None or end is None:
                    continue # 相切，忽略
                line.setLine(*self.__map_pos(*start), *self.__map_pos(*end))
            elif isinstance(obj, Circle):
                circle: QGraphicsEllipseItem = phys_obj_scene_map[obj]
                maped_pos = self.__map_pos(obj.pos.x, obj.pos.y)
                circle.setPos(*maped_pos)
                # 留下轨迹


        


if __name__ == "__main__":
    app = QApplication([])
    win = WinMain()
    app.exec_()
