from qtpy.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

try:
    from napari.qt import get_current_stylesheet
except ImportError:

    def get_current_stylesheet():
        return ""


class ComplexDialog(QDialog):
    """Dialog to ask user how to display complex number arrays."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.setWindowTitle("Complex Data Display Options")
        self.value_selected = "magnitude_phase"

        label = QLabel(
            "Complex data detected. How would you like to display it?\n"
            "Two image layers will be created."
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        # Radio buttons for display options
        self.mag_phase_radio = QRadioButton("Magnitude and Phase")
        self.mag_phase_radio.setChecked(True)  # Default option
        self.mag_phase_radio.toggled.connect(
            lambda: self.on_selection("magnitude_phase")
        )

        self.real_imag_radio = QRadioButton("Real and Imaginary")
        self.real_imag_radio.toggled.connect(
            lambda: self.on_selection("real_imaginary")
        )

        layout.addWidget(self.mag_phase_radio)
        layout.addWidget(self.real_imag_radio)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)
        self.setStyleSheet(get_current_stylesheet())

    def on_selection(self, value):
        self.value_selected = value
