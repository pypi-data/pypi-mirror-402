import os
import sys

# ——— Privilege dropping ———
if "SUDO_UID" in os.environ and "SUDO_GID" in os.environ:
    os.setgid(int(os.environ["SUDO_GID"]))
    os.setuid(int(os.environ["SUDO_UID"]))

from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QLabel,
    QLineEdit, QDialogButtonBox, QPushButton
)
from PyQt5.QtCore import Qt

class InputDialog(QDialog):
    def __init__(self):
        super().__init__(flags=Qt.Window)
        self.setWindowTitle(title)
        self.exit_requested = False

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(prompt))

        self.line_edit = QLineEdit(self)
        layout.addWidget(self.line_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        exit_btn = QPushButton("Exit", self)
        exit_btn.clicked.connect(self._on_exit)
        layout.addWidget(exit_btn, alignment=Qt.AlignRight)

    def _on_exit(self):
        self.exit_requested = True
        self.reject()
InputDialog()
