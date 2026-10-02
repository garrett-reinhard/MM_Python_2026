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


class CustomItemWidget(QWidget):
    """Custom widget containing Monomer & Solvent dropdowns, a Concentration box, and a Remove button."""

    removeRequested = Signal(QWidget)
    valueChanged = Signal()

    def __init__(
        self,
        monomers: list[str] = None,
        solvents: list[str] = None,
        parent=None,
    ):
        super().__init__(parent)

        # Monomer Dropdown
        self.monomer_label = QLabel("Monomer:")
        self.monomer_combo = QComboBox()
        if monomers:
            self.monomer_combo.addItems(monomers)

        # Solvent Dropdown
        self.solvent_label = QLabel("Solvent:")
        self.solvent_combo = QComboBox()
        if solvents:
            self.solvent_combo.addItems(solvents)

        # Concentration Float Entry Box
        self.conc_label = QLabel("Concentration (M):")
        self.conc_spinbox = QDoubleSpinBox()
        self.conc_spinbox.setRange(0.0, 100.0)
        self.conc_spinbox.setDecimals(3)
        self.conc_spinbox.setSingleStep(0.1)
        self.conc_spinbox.setValue(1.000)

        # Individual Remove Button
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setToolTip("Remove this item")
        self.remove_btn.setFixedWidth(28)
        self.remove_btn.clicked.connect(lambda: self.removeRequested.emit(self))

        # Connect signals for value tracking
        self.monomer_combo.currentIndexChanged.connect(self.valueChanged)
        self.solvent_combo.currentIndexChanged.connect(self.valueChanged)
        self.conc_spinbox.valueChanged.connect(self.valueChanged)

        # Layout setup
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.addWidget(self.monomer_label)
        layout.addWidget(self.monomer_combo)
        layout.addSpacing(10)
        layout.addWidget(self.solvent_label)
        layout.addWidget(self.solvent_combo)
        layout.addSpacing(10)
        layout.addWidget(self.conc_label)
        layout.addWidget(self.conc_spinbox)
        layout.addSpacing(10)
        layout.addWidget(self.remove_btn)

    def set_options(self, monomers: list[str] = None, solvents: list[str] = None):
        """Updates options for this item, preserving current selection if still valid."""
        if monomers is not None:
            current_monomer = self.monomer_combo.currentText()
            self.monomer_combo.clear()
            self.monomer_combo.addItems(monomers)
            idx = self.monomer_combo.findText(current_monomer)
            if idx >= 0:
                self.monomer_combo.setCurrentIndex(idx)

        if solvents is not None:
            current_solvent = self.solvent_combo.currentText()
            self.solvent_combo.clear()
            self.solvent_combo.addItems(solvents)
            idx = self.solvent_combo.findText(current_solvent)
            if idx >= 0:
                self.solvent_combo.setCurrentIndex(idx)

    def get_monomer(self) -> str:
        """Returns the currently selected monomer text."""
        return self.monomer_combo.currentText()

    def get_data(self) -> dict:
        """Returns the current state of the widget inputs."""
        return {
            "monomer": self.monomer_combo.currentText(),
            "solvent": self.solvent_combo.currentText(),
            "concentration": self.conc_spinbox.value(),
        }


class ReorderableListWidget(QWidget):
    """A composite widget containing a drag-and-drop QListWidget along with Add and Remove controls."""

    def __init__(
        self,
        monomers: list[str] = None,
        solvents: list[str] = None,
        parent=None,
    ):
        super().__init__(parent)

        self.monomer_options = monomers or []
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
        self, monomers: list[str] = None, solvents: list[str] = None, update_existing: bool = True
    ):
        """Sets the dropdown lists for new items and optionally updates existing list items."""
        if monomers is not None:
            self.monomer_options = monomers
        if solvents is not None:
            self.solvent_options = solvents

        if update_existing:
            for i in range(self.list_widget.count()):
                item = self.list_widget.item(i)
                widget = self.list_widget.itemWidget(item)
                if isinstance(widget, CustomItemWidget):
                    widget.set_options(monomers, solvents)

    def add_custom_item(self):
        """Adds a new custom widget item populated with current dropdown options."""
        item = QListWidgetItem(self.list_widget)
        custom_widget = CustomItemWidget(
            monomers=self.monomer_options,
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

    def get_monomer_order(self) -> list[str]:
        """Returns a list of monomer selections in their current list order from top to bottom."""
        monomers = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, CustomItemWidget):
                monomers.append(widget.get_monomer())
        return monomers

    def get_ordered_data(self) -> list[dict]:
        """Returns a list of data dictionaries corresponding to current item ordering."""
        data = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, CustomItemWidget):
                data.append(widget.get_data())
        return data


class MainWindow(QWidget):
    """Main application window demonstrating monomer ordering retrieval."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag & Drop Solution List")
        self.resize(700, 400)

        self.solution_list = ReorderableListWidget()

        monomer_list = ["Styrene", "MMA", "Acrylamide", "Vinyl Acetate", "Isoprene"]
        solvent_list = ["Water", "Toluene", "THF", "Acetone", "DMF", "Hexane"]

        self.solution_list.set_dropdown_options(
            monomers=monomer_list,
            solvents=solvent_list
        )

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.solution_list)

        # Add initial sample items
        self.solution_list.add_custom_item()
        self.solution_list.add_custom_item()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Demonstrating the new function usage
    # Returns: ['Styrene', 'Styrene']
    print("Monomer sequence order:", window.solution_list.get_monomer_order())

    sys.exit(app.exec_())