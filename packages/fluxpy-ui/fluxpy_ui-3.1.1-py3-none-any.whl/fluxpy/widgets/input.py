from PyQt6.QtWidgets import QLineEdit, QTextEdit, QCheckBox, QRadioButton, QSlider, QComboBox, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from .base import Control

# --- Input Widgets ---

class TextField(Control):
    def __init__(self, value="", label=None, hint_text="", password=False, multiline=False, 
                 max_length=None, on_change=None, on_submit=None, **kwargs):
        self.value = value
        self.label = label
        self.hint_text = hint_text
        self.password = password
        self.multiline = multiline
        self.max_length = max_length
        self.on_change = on_change
        self.on_submit = on_submit
        super().__init__(**kwargs)

    def _create_internal_control(self):
        # إنشاء حاوية لتضمين الـ label وحقل الإدخال
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        if self.label:
            self.label_widget = QLabel(self.label)
            layout.addWidget(self.label_widget)
        
        if self.multiline:
            self.input_widget = QTextEdit()
            self.input_widget.setText(str(self.value))
        else:
            self.input_widget = QLineEdit(str(self.value))
            self.input_widget.setPlaceholderText(self.hint_text)
            if self.password:
                self.input_widget.setEchoMode(QLineEdit.EchoMode.Password)
            if self.max_length:
                self.input_widget.setMaxLength(self.max_length)
            
            if self.on_change:
                self.input_widget.textChanged.connect(lambda text: self.on_change(self, text))
            if self.on_submit:
                self.input_widget.returnPressed.connect(lambda: self.on_submit(self))
        
        layout.addWidget(self.input_widget)
        return container

    @property
    def value(self):
        if isinstance(self.input_widget, QLineEdit):
            return self.input_widget.text()
        elif isinstance(self.input_widget, QTextEdit):
            return self.input_widget.toPlainText()
        return ""

    @value.setter
    def value(self, new_value):
        if isinstance(self.input_widget, QLineEdit):
            self.input_widget.setText(new_value)
        elif isinstance(self.input_widget, QTextEdit):
            self.input_widget.setText(new_value)
        self.update()

class Checkbox(Control):
    def __init__(self, label="", value=False, on_change=None, **kwargs):
        self.label = label
        self.value = value
        self.on_change = on_change
        super().__init__(**kwargs)

    def _create_internal_control(self):
        cb = QCheckBox(self.label)
        cb.setChecked(self.value)
        if self.on_change:
            cb.stateChanged.connect(lambda state: self.on_change(self, state == Qt.CheckState.Checked.value))
        return cb

class Radio(Control):
    def __init__(self, label="", value=False, group_name=None, on_change=None, **kwargs):
        self.label = label
        self.value = value
        self.group_name = group_name # لتجميع أزرار الراديو
        self.on_change = on_change
        super().__init__(**kwargs)

    def _create_internal_control(self):
        rb = QRadioButton(self.label)
        rb.setChecked(self.value)
        if self.on_change:
            rb.toggled.connect(lambda checked: self.on_change(self, checked))
        return rb

class Slider(Control):
    def __init__(self, min=0, max=100, value=0, on_change=None, **kwargs):
        self.min = min
        self.max = max
        self.value = value
        self.on_change = on_change
        super().__init__(**kwargs)

    def _create_internal_control(self):
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setMinimum(self.min)
        slider.setMaximum(self.max)
        slider.setValue(self.value)
        if self.on_change:
            slider.valueChanged.connect(lambda value: self.on_change(self, value))
        return slider

class Switch(Control):
    def __init__(self, label="", value=False, on_change=None, **kwargs):
        # في PyQt6، يمكن محاكاة Switch باستخدام QCheckBox مع QSS
        self.label = label
        self.value = value
        self.on_change = on_change
        super().__init__(**kwargs)

    def _create_internal_control(self):
        cb = QCheckBox(self.label)
        cb.setChecked(self.value)
        # تطبيق QSS لجعله يبدو كـ Switch
        cb.setStyleSheet("""
            QCheckBox::indicator {
                width: 30px;
                height: 15px;
                border-radius: 7px;
            }
            QCheckBox::indicator:checked {
                background-color: #007bff;
            }
            QCheckBox::indicator:unchecked {
                background-color: #ccc;
            }
        """)
        if self.on_change:
            cb.stateChanged.connect(lambda state: self.on_change(self, state == Qt.CheckState.Checked.value))
        return cb

class Dropdown(Control):
    def __init__(self, options=None, value=None, on_change=None, **kwargs):
        self.options = options if options is not None else []
        self.value = value
        self.on_change = on_change
        super().__init__(**kwargs)

    def _create_internal_control(self):
        combo = QComboBox()
        for option in self.options:
            # نفترض أن option هو قاموس {text: "...", key: "..."} أو مجرد نص
            if isinstance(option, dict):
                combo.addItem(option.get('text', str(option)), option.get('key', option.get('text')))
            else:
                combo.addItem(str(option), str(option))
        
        if self.value:
            index = combo.findData(self.value)
            if index != -1:
                combo.setCurrentIndex(index)
        
        if self.on_change:
            combo.currentTextChanged.connect(lambda text: self.on_change(self, text))
        
        return combo

# --- Export for easy import ---
__all__ = [
    "TextField", "Checkbox", "Radio", "Slider", "Switch", "Dropdown"
]
