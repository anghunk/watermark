import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QSlider, QSpinBox, QPushButton, QColorDialog, QLabel, QCheckBox
)
from PySide6.QtGui import QPainter, QColor, QFont, QPen
from PySide6.QtCore import Qt, QRectF

# =============================================================================
#  1. 水印窗口类 (无需改动)
# =============================================================================
class WatermarkWindow(QWidget):
    """
    一个半透明、可点击穿透的全屏水印窗口。
    """
    def __init__(self, text, font_size, color, opacity, angle, space):
        super().__init__()
        self.text = text
        self.font_size = font_size
        self.color = color
        self.opacity = opacity
        self.angle = angle
        self.space = space
        self.init_ui()

    def init_ui(self):
        """初始化窗口UI和属性"""
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.show()

    def paintEvent(self, event):
        """当窗口需要重绘时调用此方法"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        font = QFont("Arial", self.font_size, QFont.Weight.Bold)
        painter.setFont(font)
        r, g, b = self.color
        alpha = int(255 * self.opacity)
        pen_color = QColor(r, g, b, alpha)
        painter.setPen(QPen(pen_color))
        step_x = self.font_size * len(self.text) * 0.5 + self.space
        step_y = self.font_size * 2 + self.space
        for x in range(-int(step_x), self.width() + int(step_x), int(step_x)):
            for y in range(0, self.height() + int(step_y), int(step_y)):
                painter.save()
                painter.translate(x, y)
                painter.rotate(self.angle)
                rect = QRectF(0, 0, step_x * 2, step_y * 2)
                painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, self.text)
                painter.restore()

# =============================================================================
#  2. GUI控制面板类 (功能升级)
# =============================================================================
class ControlPanel(QWidget):
    """
    用于设置和控制水印的GUI界面，支持实时预览。
    """
    def __init__(self):
        super().__init__()
        self.watermark_instance = None
        self.selected_color = QColor(128, 128, 128)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("屏幕水印工具")
        self.resize(350, 400) 
        
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        # --- 创建控件 ---
        self.text_input = QLineEdit("内部资料 请勿外传")
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(10, 200); self.size_spinbox.setValue(30)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(1, 100); self.opacity_slider.setValue(15)
        self.angle_slider = QSlider(Qt.Orientation.Horizontal)
        self.angle_slider.setRange(-90, 90); self.angle_slider.setValue(-30)
        self.space_spinbox = QSpinBox()
        self.space_spinbox.setRange(0, 1000); self.space_spinbox.setValue(150)
        self.color_button = QPushButton("选择颜色")
        self.update_color_button_style()

        form_layout.addRow(QLabel("水印文本:"), self.text_input)
        form_layout.addRow(QLabel("字体大小:"), self.size_spinbox)
        form_layout.addRow(QLabel("透明度:"), self.opacity_slider)
        form_layout.addRow(QLabel("旋转角度:"), self.angle_slider)
        form_layout.addRow(QLabel("水印间距:"), self.space_spinbox)
        form_layout.addRow(QLabel("水印颜色:"), self.color_button)

        # --- 新增：实时预览复选框 ---
        self.live_preview_checkbox = QCheckBox("启用实时预览")
        self.live_preview_checkbox.setChecked(True)

        # --- 功能按钮 ---
        self.apply_button = QPushButton("显示 / 更新水印")
        self.remove_button = QPushButton("隐藏水印")

        # --- 布局 ---
        main_layout.addLayout(form_layout)
        main_layout.addWidget(self.live_preview_checkbox)
        main_layout.addWidget(self.apply_button)
        main_layout.addWidget(self.remove_button)
        self.setLayout(main_layout)

        # --- 连接信号和槽 ---
        self.apply_button.clicked.connect(self.apply_watermark)
        self.remove_button.clicked.connect(self.remove_watermark)
        self.color_button.clicked.connect(self.open_color_picker)

        # --- 关键：连接所有设置控件的信号到更新函数 ---
        self.text_input.textChanged.connect(self._trigger_live_update)
        self.size_spinbox.valueChanged.connect(self._trigger_live_update)
        self.opacity_slider.valueChanged.connect(self._trigger_live_update)
        self.angle_slider.valueChanged.connect(self._trigger_live_update)
        self.space_spinbox.valueChanged.connect(self._trigger_live_update)

    def _trigger_live_update(self):
        """
        检查是否满足实时更新的条件，如果满足则执行更新。
        """
        # 只有当“实时预览”开启且水印实例已存在时，才自动更新
        if self.live_preview_checkbox.isChecked() and self.watermark_instance:
            self.apply_watermark()

    def open_color_picker(self):
        """打开颜色选择对话框"""
        color = QColorDialog.getColor(self.selected_color, self)
        if color.isValid():
            self.selected_color = color
            self.update_color_button_style()
            self._trigger_live_update() # 选择颜色后也触发实时更新

    def update_color_button_style(self):
        """更新颜色按钮的背景色以显示当前选择的颜色"""
        self.color_button.setStyleSheet(f"background-color: {self.selected_color.name()}; color: {'white' if self.selected_color.lightness() < 128 else 'black'};")

    def apply_watermark(self):
        """应用或更新水印"""
        # 如果水印已存在，先移除旧的，以便创建新的
        if self.watermark_instance:
            self.watermark_instance.close()

        text = self.text_input.text()
        if not text:
            self.watermark_instance = None
            return

        # 从UI控件读取所有参数
        font_size = self.size_spinbox.value()
        opacity = self.opacity_slider.value() / 100.0
        angle = self.angle_slider.value()
        space = self.space_spinbox.value()
        color_tuple = (self.selected_color.red(), self.selected_color.green(), self.selected_color.blue())

        # 创建新的水印实例
        self.watermark_instance = WatermarkWindow(
            text=text,
            font_size=font_size,
            color=color_tuple,
            opacity=opacity,
            angle=angle,
            space=space
        )

    def remove_watermark(self):
        """移除当前的水印"""
        if self.watermark_instance:
            self.watermark_instance.close()
            self.watermark_instance = None

    def closeEvent(self, event):
        """确保关闭控制面板时，水印也一起关闭"""
        self.remove_watermark()
        event.accept()

# =============================================================================
#  3. 程序主入口
# =============================================================================
def main():
    app = QApplication(sys.argv)
    control_panel = ControlPanel()
    control_panel.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
