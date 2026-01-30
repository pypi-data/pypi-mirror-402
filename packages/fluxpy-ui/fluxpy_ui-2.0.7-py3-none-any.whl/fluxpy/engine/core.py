from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsEllipseItem
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QBrush, QColor

class GameEntity:
    def __init__(self, x, y, width, height, color="red", shape="rect"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.shape = shape
        self.item = None
        self.vx = 0
        self.vy = 0

    def build(self):
        if self.shape == "rect":
            self.item = QGraphicsRectItem(0, 0, self.width, self.height)
        else:
            self.item = QGraphicsEllipseItem(0, 0, self.width, self.height)
        self.item.setBrush(QBrush(QColor(self.color)))
        self.item.setPos(self.x, self.y)
        return self.item

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.item:
            self.item.setPos(self.x, self.y)

class FluxEngine:
    def __init__(self, width=800, height=600, bgcolor="#000000"):
        self.width = width
        self.height = height
        self.bgcolor = bgcolor
        self.entities = []
        
        self.scene = QGraphicsScene(0, 0, width, height)
        self.scene.setBackgroundBrush(QBrush(QColor(bgcolor)))
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(Qt.RenderHint.Antialiasing)
        self.view.setFixedSize(width, height)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.game_loop)
        self.fps = 60

    def add_entity(self, entity):
        self.entities.append(entity)
        self.scene.addItem(entity.build())

    def start(self):
        self.timer.start(1000 // self.fps)

    def game_loop(self):
        for entity in self.entities:
            entity.update()

    def build(self):
        return self.view
