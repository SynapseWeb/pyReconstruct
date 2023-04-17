from PySide6.QtWidgets import (
    QDialog, 
    QDialogButtonBox, 
    QLabel, 
    QLineEdit, 
    QVBoxLayout,
    QGridLayout,
)

from .helper import resizeLineEdit

from modules.gui.utils import notify

class GridDialog(QDialog):

    def __init__(self, parent, properties : tuple):
        """Create a dialog for brightness/contrast."""
        super().__init__(parent)

        w, h, dx, dy, nx, ny = properties

        self.setWindowTitle("Set Grid")

        size_text = QLabel(self, text="Element size:")
        size_x_text = QLabel(self, text="X:")
        size_x_input = QLineEdit(self)
        size_x_input.adjustSize()
        size_x_input.setText(str(w))
        size_y_text = QLabel(self, text="Y:")
        size_y_input = QLineEdit(self)
        size_y_input.setText(str(h))

        dist_text = QLabel(self, text="Distance:")
        dist_x_text = QLabel(self, text="X:")
        dist_x_input = QLineEdit(self)
        dist_x_input.setText(str(dx))
        dist_y_text = QLabel(self, text="Y:")
        dist_y_input = QLineEdit(self)
        dist_y_input.setText(str(dy))

        num_text = QLabel(self, text="Number:")
        num_x_text = QLabel(self, text="X:")
        num_x_input = QLineEdit(self)
        num_x_input.setText(str(nx))
        num_y_text = QLabel(self, text="Y:")
        num_y_input = QLineEdit(self)
        num_y_input.setText(str(ny))

        self.inputs = [
            size_x_input, size_y_input,
            dist_x_input, dist_y_input,
            num_x_input, num_y_input
        ]
        for input in self.inputs:
            resizeLineEdit(input, "000")
        
        layout = QGridLayout()

        layout.addWidget(size_text, 0, 0)
        layout.addWidget(size_x_text, 0, 1)
        layout.addWidget(size_x_input, 0, 2)
        layout.addWidget(size_y_text, 0, 3)
        layout.addWidget(size_y_input, 0, 4)

        layout.addWidget(dist_text, 1, 0)
        layout.addWidget(dist_x_text, 1, 1)
        layout.addWidget(dist_x_input, 1, 2)
        layout.addWidget(dist_y_text, 1, 3)
        layout.addWidget(dist_y_input, 1, 4)

        layout.addWidget(num_text, 2, 0)
        layout.addWidget(num_x_text, 2, 1)
        layout.addWidget(num_x_input, 2, 2)
        layout.addWidget(num_y_text, 2, 3)
        layout.addWidget(num_y_input, 2, 4)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonbox = QDialogButtonBox(QBtn)
        self.buttonbox.accepted.connect(self.accept)
        self.buttonbox.rejected.connect(self.reject)

        self.vlayout = QVBoxLayout()
        self.vlayout.setSpacing(10)
        self.vlayout.addLayout(layout)
        self.vlayout.addWidget(self.buttonbox)

        self.setLayout(self.vlayout)
    
    def accept(self):
        """Overwritten from parent class."""
        for input in self.inputs[:4]:
            if not input.text().replace(".", "", 1).isnumeric():
                notify("Please enter a valid number.")
                return
        for input in self.inputs[4:]:
            if not input.text().isnumeric():
                notify("Please enter a whole number for the grid number.")
                return
        
        super().accept()
    
    def exec(self):
        "Run the dialog."
        confirmed = super().exec()
        if confirmed:
            response = []
            for input in self.inputs[:4]:
                response.append(float(input.text()))
            for input in self.inputs[4:]:
                response.append(int(input.text()))
            return response, True
        else:
            return None, False