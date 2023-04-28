from PySide6.QtWidgets import (
    QWidget, 
    QDialog, 
    QDialogButtonBox, 
    QHBoxLayout, 
    QLabel, 
    QLineEdit,
    QVBoxLayout, 
    QComboBox, 
    QPushButton
)

from .helper import resizeLineEdit

from modules.datatypes import Series
from modules.gui.utils import notify

class AddToZarrDialog(QDialog):

    def __init__(self, parent : QWidget, series : Series):
        """Create a zarr dialog.
        
            Params:
                parent (QWidget): the parent widget
                series (Series): the current series
        """
        self.series = series

        super().__init__(parent)

        self.setWindowTitle("Export Labels to Zarr")

        vlayout = QVBoxLayout()
        vlayout.setSpacing(10)

        # create the group combo box inputs
        self.group_widgets = []
        for i in range(5):
            row = QHBoxLayout()
            text = QLabel(self)
            text.setText("Group:")
            input = QComboBox(self)
            input.addItem("")
            input.addItems(sorted(series.object_groups.getGroupList()))
            input.resize(input.sizeHint())
            row.addWidget(text)
            row.addWidget(input)
            if i != 0:
                text.hide()
                input.hide()
            self.group_widgets.append((text, input))
            vlayout.addLayout(row)
        self.inputs = 1

        # create buttons for adding and removing group inputs
        addremove_row = QHBoxLayout()
        addremove_row.addSpacing(10)
        self.add_bttn = QPushButton(text="Add Group", parent=self)
        self.add_bttn.clicked.connect(self.addInput)
        self.remove_bttn = QPushButton(text="Remove Group", parent=self)
        self.remove_bttn.clicked.connect(self.removeInput)
        addremove_row.addWidget(self.remove_bttn)
        addremove_row.addWidget(self.add_bttn)
        self.remove_bttn.hide()
        vlayout.addLayout(addremove_row)

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        buttonbox = QDialogButtonBox(QBtn)
        buttonbox.accepted.connect(self.accept)
        buttonbox.rejected.connect(self.reject)

        vlayout.addSpacing(10)
        vlayout.addWidget(buttonbox)

        self.setLayout(vlayout)
    
    def addInput(self):
        """Add a group input."""
        if self.inputs >= 5:
            return
        text, input = self.group_widgets[self.inputs]
        text.show()
        input.show()
        self.inputs += 1
        self.updateButtons()
    
    def removeInput(self):
        """Remove a group input."""
        if self.inputs <= 1:
            return
        text, input = self.group_widgets[self.inputs-1]
        text.hide()
        input.hide()
        self.inputs -= 1
        self.updateButtons()
    
    def updateButtons(self):
        """Show/hide buttons according to number of inputs."""
        if self.inputs < 5:
            self.add_bttn.show()
        else:
            self.add_bttn.hide()
        if self.inputs > 1:
            self.remove_bttn.show()
        else:
            self.remove_bttn.hide()
    
    def accept(self):
        """Overwritten from QDialog."""        
        # check that user entered at least one group
        entered = False
        for text, input in self.group_widgets:
            entered |= bool(input.currentText())
        if not entered:
            notify("Please select a group.")
            return
        
        super().accept()
              

    def exec(self):
        """Run the dialog."""
        confirmed = super().exec()
        if confirmed:
            groups = set()
            for text, input in self.group_widgets:
                group = input.currentText()
                if group:
                    groups.add(group)
            groups = list(groups)

            return groups, True
        
        else:
            return None, False