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
            item_widget = QWidget()
            layout = QVBoxLayout(item_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(control.internal_control)
            
            item.setSizeHint(item_widget.sizeHint())
            list_widget.setItemWidget(item, item_widget)
            
        if not self.scrollable:
            list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            
        return list_widget

class DataTable(Control):
    def __init__(self, columns=None, rows=None, **kwargs):
        self.columns = columns if columns is not None else []
        self.rows = rows if rows is not None else []
        super().__init__(**kwargs)

    def _create_internal_control(self):
        table = QTableWidget()
        table.setColumnCount(len(self.columns))
        table.setRowCount(len(self.rows))
        
        # تعيين رؤوس الأعمدة بذكاء (دعم نصوص أو قواميس)
        header_labels = []
        for col in self.columns:
            if isinstance(col, dict):
                header_labels.append(col.get('label', ''))
            else:
                header_labels.append(str(col))
        
        table.setHorizontalHeaderLabels(header_labels)
        
        # تعبئة البيانات
        for i, row_data in enumerate(self.rows):
            for j, cell_data in enumerate(row_data):
                if isinstance(cell_data, Control):
                    # إذا كانت الخلية تحتوي على عنصر تحكم (مثل TextField أو Container)
                    table.setCellWidget(i, j, cell_data.internal_control)
                else:
                    # إذا كانت نصاً أو رقماً
                    item = QTableWidgetItem(str(cell_data))
                    
                    # محاذاة البيانات الرقمية إذا تم تحديد ذلك في القاموس
                    if j < len(self.columns) and isinstance(self.columns[j], dict):
                        if self.columns[j].get('numeric', False):
                            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    table.setItem(i, j, item)
                
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        return table

# --- Export for easy import ---
__all__ = [
    "ListView", "DataTable"
]
