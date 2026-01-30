from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QBrush

class GameEntity:
    def __init__(self, x=0, y=0, width=50, height=50, color="red"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.vx = 0
        self.vy = 0
        self.item = None

class FluxEngine:
    def __init__(self, width=800, height=600, bgcolor="white"):
        self.width = width
        self.height = height
        self.bgcolor = bgcolor
        self.entities = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)

    def add_entity(self, entity):
        self.entities.append(entity)

    def start(self, fps=60):
        self.timer.start(1000 // fps)

    def update(self):
        for entity in self.entities:
            entity.x += entity.vx
            entity.y += entity.vy
            if entity.item:
                entity.item.setPos(entity.x, entity.y)

    def render_desktop(self):
        scene = QGraphicsScene(0, 0, self.width, self.height)
        scene.setBackgroundBrush(QBrush(QColor(self.bgcolor)))
        view = QGraphicsView(scene)
        
        for entity in self.entities:
            item = QGraphicsRectItem(0, 0, entity.width, entity.height)
            item.setBrush(QBrush(QColor(entity.color)))
            item.setPos(entity.x, entity.y)
            entity.item = item
            scene.addItem(item)
            
        return view

    def render_web(self):
        return f'<div style="width: {self.width}px; height: {self.height}px; background: {self.bgcolor}; position: relative;">(Game Engine Web Placeholder)</div>'
