# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets


class AddConnectionDialog(QtWidgets.QDialog):
    """Sub-dialog to select Valve (1-24) and Port (1-8)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Connection")
        self.resize(250, 150)

        layout = QtWidgets.QVBoxLayout(self)
        form_layout = QtWidgets.QFormLayout()

        # Valve SpinBox (1 to 24)
        self.valve_spinbox = QtWidgets.QSpinBox(self)
        self.valve_spinbox.setRange(1, 24)
        self.valve_spinbox.setValue(1)
        form_layout.addRow("Valve (1-24):", self.valve_spinbox)

        # Port SpinBox (1 to 8)
        self.port_spinbox = QtWidgets.QSpinBox(self)
        self.port_spinbox.setRange(1, 8)
        self.port_spinbox.setValue(1)
        form_layout.addRow("Port (1-8):", self.port_spinbox)

        layout.addLayout(form_layout)

        # Dialog Standard Buttons (OK / Cancel)
        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            self,
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout.addWidget(self.buttonBox)

    def get_selection(self) -> tuple[int, int]:
        """Returns selected (valve, port)."""
        return self.valve_spinbox.value(), self.port_spinbox.value()


class AddComponentDialog(QtWidgets.QDialog):
    """Dialog for defining component settings, valve connections, and hotplates."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Store connections as tuples/lists of integers: [(valve_int, port_int), ...]
        self.connection_data: list[list[int]] = []
        self.connection_labels: list[QtWidgets.QLabel] = []
        self.setupUi()

    def setupUi(self):
        self.setObjectName("AddComponentDialog")
        self.setWindowTitle("Add Component")
        self.resize(480, 350)

        # Main Root Layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(12)

        # Top Content Split (Left / Right)
        self.content_layout = QtWidgets.QHBoxLayout()
        self.content_layout.setSpacing(15)

        # --- LEFT PANEL: Component Name & Dynamic Valves List ---
        self.left_panel = QtWidgets.QVBoxLayout()
        self.left_panel.setSpacing(8)

        self.name_label = QtWidgets.QLabel("Component Name:", self)
        self.ComponentName = QtWidgets.QLineEdit(self)
        self.ComponentName.setPlaceholderText("Enter name...")
        self.left_panel.addWidget(self.name_label)
        self.left_panel.addWidget(self.ComponentName)

        # Valves Dynamic Display Box
        self.valves_group = QtWidgets.QGroupBox("Valve Connections", self)
        self.valves_container_layout = QtWidgets.QVBoxLayout(self.valves_group)

        self.valves_scroll = QtWidgets.QScrollArea(self)
        self.valves_scroll.setWidgetResizable(True)
        self.scroll_content = QtWidgets.QWidget()

        self.Valves = QtWidgets.QVBoxLayout(self.scroll_content)
        self.Valves.setContentsMargins(5, 5, 5, 5)
        self.Valves.setSpacing(4)
        self.Valves.addStretch()

        self.valves_scroll.setWidget(self.scroll_content)
        self.valves_container_layout.addWidget(self.valves_scroll)

        self.left_panel.addWidget(self.valves_group)

        # Connection Management Buttons
        self.conn_btn_layout = QtWidgets.QHBoxLayout()
        self.AddConnection = QtWidgets.QPushButton("Add Connection", self)
        self.RemoveConnection = QtWidgets.QPushButton("Remove Connection", self)

        # Signal connections
        self.AddConnection.clicked.connect(self._on_add_connection_click)
        self.RemoveConnection.clicked.connect(self._on_remove_connection_click)

        self.conn_btn_layout.addWidget(self.AddConnection)
        self.conn_btn_layout.addWidget(self.RemoveConnection)
        self.left_panel.addLayout(self.conn_btn_layout)

        # --- RIGHT PANEL: Hotplate Selector & Flags ---
        self.right_panel = QtWidgets.QVBoxLayout()
        self.right_panel.setSpacing(12)

        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setSpacing(8)

        self.HotplateSelector = QtWidgets.QComboBox(self)
        self.HotplateSelector.addItems(
            [
                "hotplate_1",
                "hotplate_2",
                "hotplate_3",
                "hotplate_4",
            ]
        )
        self.form_layout.addRow("Hotplate:", self.HotplateSelector)

        self.right_panel.addLayout(self.form_layout)

        self.IsUsed = QtWidgets.QCheckBox("Already Filled?", self)
        self.right_panel.addWidget(self.IsUsed)
        self.right_panel.addStretch()

        # Assemble Main Panels
        self.content_layout.addLayout(self.left_panel, stretch=3)
        self.content_layout.addLayout(self.right_panel, stretch=2)
        self.main_layout.addLayout(self.content_layout)

        # OK / Cancel Buttons
        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            self,
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttonBox)

        QtCore.QMetaObject.connectSlotsByName(self)

    def _on_add_connection_click(self):
        """Pops up selection dialog and appends result to the connection display."""
        dialog = AddConnectionDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            valve, port = dialog.get_selection()

            # Store numerical pair
            self.connection_data.append([valve, port])

            # Format UI visual label string
            label_text = f"Valve {valve} — Port {port}"
            lbl = QtWidgets.QLabel(label_text, self)
            lbl.setStyleSheet(
                "padding: 2px; background-color: #e8e8e8; border-radius: 3px;"
            )

            # Insert label above layout stretch
            self.Valves.insertWidget(self.Valves.count() - 1, lbl)
            self.connection_labels.append(lbl)

    def _on_remove_connection_click(self):
        """Removes the last added connection from layout and data structures."""
        if self.connection_labels:
            lbl = self.connection_labels.pop()
            self.Valves.removeWidget(lbl)
            lbl.deleteLater()

        if self.connection_data:
            self.connection_data.pop()

    def get_data(self) -> dict:
        """Returns dialog outputs with connections represented as [[valve_int, port_int], ...]."""
        return {
            "name": self.ComponentName.text(),
            "hotplate": self.HotplateSelector.currentText(),
            "is_filled": self.IsUsed.isChecked(),
            "connections": self.connection_data,
        }


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    dialog = AddComponentDialog()
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        print("Component Data Saved:", dialog.get_data())