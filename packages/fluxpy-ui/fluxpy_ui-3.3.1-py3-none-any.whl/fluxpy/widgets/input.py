from PyQt6.QtWidgets import QLineEdit, QTextEdit, QCheckBox, QRadioButton, QSlider, QComboBox, QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from .base import Control
import inspect

def _safe_call(func, *args):
    """دالة مساعدة لاستدعاء الدوال بأمان بغض النظر عن عدد الوسائط."""
    if not func:
        return
    sig = inspect.signature(func)
    params_count = len(sig.parameters)
    if params_count == 0:
        func()
    elif params_count == 1:
        func(args[0])
    else:
        func(*args[:params_count])

# --- Input Widgets ---

class TextField(Control):
    def __init__(self, value="", label=None, hint_text="", password=False, multiline=False, 
                 max_length=None, on_change=None, on_submit=None, **kwargs):
        self._value = value
        self.label = label
        self.hint_text = hint_text
        self.password = password
        self.multiline = multiline
        self.max_length = max_length
        self.on_change = on_change
        self.on_submit = on_submit
        self.input_widget = None
        super().__init__(**kwargs)

    def _create_internal_control(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        if self.label:
            self.label_widget = QLabel(self.label)
            layout.addWidget(self.label_widget)
        
        if self.multiline:
            self.input_widget = QTextEdit()
            self.input_widget.setText(str(self._value))
            if self.on_change:
                self.input_widget.textChanged.connect(lambda: _safe_call(self.on_change, self, self.input_widget.toPlainText()))
        else:
            self.input_widget = QLineEdit(str(self._value))
            self.input_widget.setPlaceholderText(self.hint_text)
            if self.password:
                self.input_widget.setEchoMode(QLineEdit.EchoMode.Password)
            if self.max_length:
                self.input_widget.setMaxLength(self.max_length)
            
            if self.on_change:
                self.input_widget.textChanged.connect(lambda text: _safe_call(self.on_change, self, text))
            if self.on_submit:
                self.input_widget.returnPressed.connect(lambda: _safe_call(self.on_submit, self))
        
        layout.addWidget(self.input_widget)
        return container

    @property
    def value(self):
        if self.input_widget:
            if isinstance(self.input_widget, QLineEdit):
                return self.input_widget.text()
            elif isinstance(self.input_widget, QTextEdit):
                return self.input_widget.toPlainText()
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        if self.input_widget:
            if isinstance(self.input_widget, (QLineEdit, QTextEdit)):
                self.input_widget.setText(str(new_value))
            self.update()

class Checkbox(Control):
    def __init__(self, label="", value=False, on_change=None, **kwargs):
        self.label = label
        self._value = value
        self.on_change = on_change
        self.internal_cb = None
        super().__init__(**kwargs)

    def _create_internal_control(self):
        self.internal_cb = QCheckBox(self.label)
        self.internal_cb.setChecked(self._value)
        if self.on_change:
            self.internal_cb.stateChanged.connect(lambda state: _safe_call(self.on_change, self, state == Qt.CheckState.Checked.value))
        return self.internal_cb

    @property
    def value(self):
        if self.internal_cb:
            return self.internal_cb.isChecked()
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        if self.internal_cb:
            self.internal_cb.setChecked(new_value)
            self.update()

class Radio(Control):
    def __init__(self, label="", value=False, group_name=None, on_change=None, **kwargs):
        self.label = label
        self._value = value
        self.group_name = group_name
        self.on_change = on_change
        self.internal_rb = None
        super().__init__(**kwargs)

    def _create_internal_control(self):
        self.internal_rb = QRadioButton(self.label)
        self.internal_rb.setChecked(self._value)
        if self.on_change:
            self.internal_rb.toggled.connect(lambda checked: _safe_call(self.on_change, self, checked))
        return self.internal_rb

    @property
    def value(self):
        if self.internal_rb:
            return self.internal_rb.isChecked()
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        if self.internal_rb:
            self.internal_rb.setChecked(new_value)
            self.update()

class Slider(Control):
    def __init__(self, min=0, max=100, value=0, on_change=None, **kwargs):
        self.min = min
        self.max = max
        self._value = value
        self.on_change = on_change
        self.internal_slider = None
        super().__init__(**kwargs)

    def _create_internal_control(self):
        self.internal_slider = QSlider(Qt.Orientation.Horizontal)
        self.internal_slider.setMinimum(self.min)
        self.internal_slider.setMaximum(self.max)
        self.internal_slider.setValue(self._value)
        if self.on_change:
            self.internal_slider.valueChanged.connect(lambda value: _safe_call(self.on_change, self, value))
        return self.internal_slider

    @property
    def value(self):
        if self.internal_slider:
            return self.internal_slider.value()
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        if self.internal_slider:
            self.internal_slider.setValue(new_value)
            self.update()

class Switch(Control):
    def __init__(self, label="", value=False, on_change=None, **kwargs):
        self.label = label
        self._value = value
        self.on_change = on_change
        self.internal_cb = None
        super().__init__(**kwargs)

    def _create_internal_control(self):
        self.internal_cb = QCheckBox(self.label)
        self.internal_cb.setChecked(self._value)
        self.internal_cb.setStyleSheet("""
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
            self.internal_cb.stateChanged.connect(lambda state: _safe_call(self.on_change, self, state == Qt.CheckState.Checked.value))
        return self.internal_cb

    @property
    def value(self):
        if self.internal_cb:
            return self.internal_cb.isChecked()
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        if self.internal_cb:
            self.internal_cb.setChecked(new_value)
            self.update()

class Dropdown(Control):
    def __init__(self, options=None, value=None, on_change=None, **kwargs):
        self.options = options if options is not None else []
        self._value = value
        self.on_change = on_change
        self.internal_combo = None
        super().__init__(**kwargs)

    def _create_internal_control(self):
        self.internal_combo = QComboBox()
        for option in self.options:
            if isinstance(option, dict):
                self.internal_combo.addItem(option.get('text', str(option)), option.get('key', option.get('text')))
            else:
                self.internal_combo.addItem(str(option), str(option))
        
        if self._value:
            index = self.internal_combo.findData(self._value)
            if index != -1:
                self.internal_combo.setCurrentIndex(index)
        
        if self.on_change:
            self.internal_combo.currentTextChanged.connect(lambda text: _safe_call(self.on_change, self, text))
        
        return self.internal_combo

    @property
    def value(self):
        if self.internal_combo:
            return self.internal_combo.currentData()
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value
        if self.internal_combo:
            index = self.internal_combo.findData(new_value)
            if index != -1:
                self.internal_combo.setCurrentIndex(index)
            self.update()

# --- Export for easy import ---
__all__ = [
    "TextField", "Checkbox", "Radio", "Slider", "Switch", "Dropdown"
]
