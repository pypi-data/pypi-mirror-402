from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt
from .base import Control

# --- List & Table Widgets ---

class ListView(Control):
    def __init__(self, controls=None, spacing=5, scrollable=True, **kwargs):
        self.controls = controls if controls is not None else []
        self.spacing = spacing
        self.scrollable = scrollable
        super().__init__(**kwargs)

    def _create_internal_control(self):
        list_widget = QListWidget()
        list_widget.setSpacing(self.spacing)
        
        for control in self.controls:
            item = QListWidgetItem(list_widget)
            # إنشاء QWidget لتضمين عنصر التحكم
            item_widget = QWidget()
            layout = QVBoxLayout(item_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(control.internal_control)
            
            item.setSizeHint(item_widget.sizeHint())
            list_widget.setItemWidget(item, item_widget)
            control._page = self._page
            
        if not self.scrollable:
            list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
        return list_widget

class DataTable(Control):
    def __init__(self, columns=None, rows=None, **kwargs):
        self.columns = columns if columns is not None else [] # [{label: "...", numeric: False}]
        self.rows = rows if rows is not None else [] # [[cell1, cell2, ...], ...]
        super().__init__(**kwargs)

    def _create_internal_control(self):
        table = QTableWidget()
        table.setColumnCount(len(self.columns))
        table.setRowCount(len(self.rows))
        
        # تعيين رؤوس الأعمدة
        header_labels = [col.get('label', '') for col in self.columns]
        table.setHorizontalHeaderLabels(header_labels)
        
        # تعبئة البيانات
        for i, row_data in enumerate(self.rows):
            for j, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                
                # محاذاة البيانات الرقمية إلى اليمين
                if self.columns[j].get('numeric', False):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                table.setItem(i, j, item)
                
        # ضبط حجم الأعمدة ليناسب المحتوى
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        return table

# --- Export for easy import ---
__all__ = [
    "ListView", "DataTable"
]
