import sys
from qtpy.QtCore import Qt, Signal
from qtpy.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class CustomCleaningItemWidget(QWidget):
    """Custom widget containing a Solvent dropdown, Volume box (mL), and a Remove button."""

    removeRequested = Signal(QWidget)
    valueChanged = Signal()

    def __init__(
        self,
        parent=None,
        solvents: list[str] = None,
    ):
        super().__init__(parent)

        # Solvent Dropdown
        self.solvent_label = QLabel("Solvent:")
        self.solvent_combo = QComboBox()
        if solvents and isinstance(solvents, (list, tuple)):
            self.solvent_combo.addItems(solvents)

        # Volume Entry Box (mL)
        self.vol_label = QLabel("Volume (mL):")
        self.vol_spinbox = QDoubleSpinBox()
        self.vol_spinbox.setRange(0.0, 10000.0)
        self.vol_spinbox.setDecimals(2)
        self.vol_spinbox.setSingleStep(1.0)
        self.vol_spinbox.setValue(10.00)

        # Individual Remove Button
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setToolTip("Remove this item")
        self.remove_btn.setFixedWidth(28)
        self.remove_btn.clicked.connect(lambda: self.removeRequested.emit(self))

        # Connect signals for value tracking
        self.solvent_combo.currentIndexChanged.connect(self.valueChanged)
        self.vol_spinbox.valueChanged.connect(self.valueChanged)

        # Layout setup
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(self.solvent_label)
        layout.addWidget(self.solvent_combo)
        layout.addSpacing(10)
        layout.addWidget(self.vol_label)
        layout.addWidget(self.vol_spinbox)
        layout.addSpacing(10)
        layout.addWidget(self.remove_btn)

    def set_options(self, solvents: list[str] = None):
        """Updates options for this item, preserving current selection if still valid."""
        if solvents is not None and isinstance(solvents, (list, tuple)):
            current_solvent = self.solvent_combo.currentText()
            self.solvent_combo.clear()
            self.solvent_combo.addItems(solvents)
            idx = self.solvent_combo.findText(current_solvent)
            if idx >= 0:
                self.solvent_combo.setCurrentIndex(idx)

    def get_solvent(self) -> str:
        """Returns the currently selected solvent text."""
        return self.solvent_combo.currentText()

    def get_data(self) -> dict:
        """Returns the current state of the widget inputs."""
        return {
            "solvent": self.solvent_combo.currentText(),
            "volume_ml": self.vol_spinbox.value(),
        }


class ReorderablecleaningListWidget(QWidget):
    """A composite widget containing a drag-and-drop QListWidget along with Add and Remove controls."""

    def __init__(
        self,
        solvents: list[str] = None,
        parent=None,
    ):
        super().__init__(parent)

        self.solvent_options = solvents or []

        # Inner list widget handling drag and drop
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.setAcceptDrops(True)

        # Control Buttons
        self.add_button = QPushButton("＋ Add Item")
        self.add_button.clicked.connect(self.add_custom_item)

        self.remove_selected_button = QPushButton("－ Remove Selected")
        self.remove_selected_button.clicked.connect(self.remove_selected_item)

        # Button Layout
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_button)
        btn_layout.addWidget(self.remove_selected_button)

        # Container Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(btn_layout)

    def set_dropdown_options(
        self, solvents: list[str] = None, update_existing: bool = True
    ):
        """Sets the dropdown lists for new items and optionally updates existing list items."""
        if solvents is not None:
            self.solvent_options = solvents

        if update_existing:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                widget = self.list_widget.itemWidget(item)
                if isinstance(widget, CustomCleaningItemWidget):
                    widget.set_options(solvents)

    def add_custom_item(self):
        """Adds a new custom widget item populated with current dropdown options."""
        item = QListWidgetItem(self.list_widget)
        custom_widget = CustomCleaningItemWidget(
            solvents=self.solvent_options,
        )

        custom_widget.removeRequested.connect(self.remove_item_widget)
        item.setSizeHint(custom_widget.sizeHint())

        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, custom_widget)

    def remove_item_widget(self, custom_widget: QWidget):
        """Removes an item given its custom widget reference."""
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if self.list_widget.itemWidget(item) == custom_widget:
                self.list_widget.takeItem(i)
                break

    def remove_selected_item(self):
        """Removes the currently selected item."""
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            self.list_widget.takeItem(current_row)

    def get_ordered_data(self) -> list[dict]:
        """Returns a list of data dictionaries corresponding to current item ordering."""
        data = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, CustomCleaningItemWidget):
                data.append(widget.get_data())
        return data