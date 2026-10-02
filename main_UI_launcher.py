# -*- coding: utf-8 -*-

import json
import sys
from ExactPolymerReactionClass import ExactPolymerReactionPlan
from monomer_list_widget import ReorderableMonomerListWidget
from cleaning_list_widget import ReorderablecleaningListWidget
from add_component_dialog_box import AddComponentDialog
from PyQt5 import QtCore, QtGui, QtWidgets
from main import Campaign

class SingleReagentItemWidget(QtWidgets.QWidget):
    """Custom item widget containing a single Reagent dropdown and a Remove button."""

    removeRequested = QtCore.pyqtSignal(QtWidgets.QWidget)

    def __init__(self, index: int = 1, parent=None, reagents: list[str] = None):
        super().__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.label = QtWidgets.QLabel(f"Reagent {index}:", self)
        self.combo = QtWidgets.QComboBox(self)
        if reagents and isinstance(reagents, (list, tuple, dict)):
            self.combo.addItems(list(reagents.keys()) if isinstance(reagents, dict) else reagents)

        self.remove_btn = QtWidgets.QPushButton("✕", self)
        self.remove_btn.setToolTip("Remove reagent")
        self.remove_btn.setFixedWidth(28)
        self.remove_btn.clicked.connect(lambda: self.removeRequested.emit(self))

        layout.addWidget(self.label)
        layout.addWidget(self.combo, stretch=1)
        layout.addWidget(self.remove_btn)

    def set_label_index(self, index: int):
        self.label.setText(f"Reagent {index}:")

    def set_options(self, reagents):
        current_text = self.combo.currentText()
        self.combo.clear()
        items = list(reagents.keys()) if isinstance(reagents, dict) else reagents
        self.combo.addItems(items)
        idx = self.combo.findText(current_text)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)

    def get_reagent(self) -> str:
        return self.combo.currentText()


class OptimizerReagentListWidget(QtWidgets.QWidget):
    """Reorderable list widget specifically for the Reaction Optimizer containing single-dropdown reagent rows."""

    def __init__(self, parent=None, reagents: list[str] = None):
        super().__init__(parent)
        self.reagent_options = list(reagents.keys()) if isinstance(reagents, dict) else (reagents or [])

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.list_widget = QtWidgets.QListWidget(self)
        self.list_widget.setDragDropMode(QtWidgets.QListWidget.InternalMove)
        self.list_widget.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.list_widget.setSelectionMode(QtWidgets.QListWidget.SingleSelection)

        btn_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QPushButton("＋ Add Reagent", self)
        self.add_button.clicked.connect(self.add_reagent_item)

        self.remove_button = QtWidgets.QPushButton("－ Remove Selected", self)
        self.remove_button.clicked.connect(self.remove_selected_item)

        btn_layout.addWidget(self.add_button)
        btn_layout.addWidget(self.remove_button)

        main_layout.addWidget(self.list_widget)
        main_layout.addLayout(btn_layout)

    def set_dropdown_options(self, reagents, unused=None):
        self.reagent_options = list(reagents.keys()) if isinstance(reagents, dict) else (reagents or [])
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, SingleReagentItemWidget):
                widget.set_options(self.reagent_options)

    def add_reagent_item(self):
        index = self.list_widget.count() + 1
        item = QtWidgets.QListWidgetItem(self.list_widget)
        widget = SingleReagentItemWidget(index=index, parent=self, reagents=self.reagent_options)
        widget.removeRequested.connect(self.remove_item_widget)

        item.setSizeHint(widget.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, widget)

    def remove_item_widget(self, widget: QtWidgets.QWidget):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if self.list_widget.itemWidget(item) == widget:
                self.list_widget.takeItem(i)
                break
        self._reindex_labels()

    def remove_selected_item(self):
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            self.list_widget.takeItem(current_row)
            self._reindex_labels()

    def _reindex_labels(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, SingleReagentItemWidget):
                widget.set_label_index(i + 1)

    def get_monomer_order(self) -> list[str]:
        reagents = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, SingleReagentItemWidget):
                reagents.append(widget.get_reagent())
        return reagents


class Ui_MainWindow(QtWidgets.QWidget):
    def setupUi(self, MainWindow):
        self.reaction_plan = ExactPolymerReactionPlan()
        self.components_cache = {}  # Cache loaded components for dynamic widgets
        
        # Track reagent entries (Reagent List + its specific Volume Spinboxes)
        self.optimizer_reagent_entries = []
        
        # Track single global Temperature Spinboxes list
        self.global_temp_spinboxes = []

        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1400, 800)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # Root Layout to hold the Tab Container
        self.root_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.root_layout.setContentsMargins(5, 5, 5, 5)

        # Tab Widget Container
        self.tab_widget = QtWidgets.QTabWidget(self.centralwidget)
        self.root_layout.addWidget(self.tab_widget)

        # ---------------------------------------------------------------------
        # TAB 1: Exact Polymer
        # ---------------------------------------------------------------------
        self.exact_polymer_tab = QtWidgets.QWidget()
        self.main_layout = QtWidgets.QHBoxLayout(self.exact_polymer_tab)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(20)

        # LEFT COLUMN (Reaction Configuration Controls & Form Options)
        self.left_panel = QtWidgets.QVBoxLayout()
        self.left_panel.setSpacing(12)

        # Reaction Length Layout
        self.length_layout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel("Choose Reaction Length:", self.exact_polymer_tab)
        self.PolymerLength = QtWidgets.QSpinBox(self.exact_polymer_tab)
        self.PolymerLength.setMinimum(1)
        self.PolymerLength.setMaximum(16)
        self.length_layout.addWidget(self.label)
        self.length_layout.addWidget(self.PolymerLength)
        self.length_layout.addStretch()
        self.left_panel.addLayout(self.length_layout)

        # Option Checkboxes
        self.solid_supported_polymer = QtWidgets.QCheckBox(
            "solid_supported_polymer", self.exact_polymer_tab
        )
        self.orthogonally_protected_monomer = QtWidgets.QCheckBox(
            "orthogonally_protected_monomer", self.exact_polymer_tab
        )
        self.monomer_removal_solid_supported = QtWidgets.QCheckBox(
            "monomer_removal_solid_supported", self.exact_polymer_tab
        )
        self.activator_solid_supported = QtWidgets.QCheckBox(
            "activator_solid_supported", self.exact_polymer_tab
        )
        self.end_cap = QtWidgets.QCheckBox("end_cap", self.exact_polymer_tab)

        self.left_panel.addWidget(self.solid_supported_polymer)
        self.left_panel.addWidget(self.orthogonally_protected_monomer)
        self.left_panel.addWidget(self.monomer_removal_solid_supported)
        self.left_panel.addWidget(self.activator_solid_supported)
        self.left_panel.addWidget(self.end_cap)

        # Form Layout for Solution & Component Dropdowns
        self.form_layout = QtWidgets.QFormLayout()
        self.form_layout.setLabelAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self.form_layout.setSpacing(8)

        self.Monomer = QtWidgets.QComboBox(self.exact_polymer_tab)
        self.Monomer.addItem("None")
        self.Monomer.currentTextChanged.connect(
            lambda: self.set_atr("MonomerSolution", self.Monomer.currentText())
        )
        self.form_layout.addRow("Monomer Solution:", self.Monomer)

        self.CouplingReactionComponent = QtWidgets.QComboBox(self.exact_polymer_tab)
        self.CouplingReactionComponent.addItem("None")
        self.CouplingReactionComponent.currentTextChanged.connect(
            lambda: self.set_atr(
                "CouplingReactionComponent",
                self.CouplingReactionComponent.currentText(),
            )
        )
        self.form_layout.addRow(
            "Coupling Reaction Component:", self.CouplingReactionComponent
        )

        self.ExcessMonomerWash = QtWidgets.QComboBox(self.exact_polymer_tab)
        self.ExcessMonomerWash.addItem("None")
        self.ExcessMonomerWash.currentTextChanged.connect(
            lambda: self.set_atr(
                "ExcessMonomerWash", self.ExcessMonomerWash.currentText()
            )
        )
        self.form_layout.addRow("Excess Monomer Wash:", self.ExcessMonomerWash)

        self.ActivatorComponent = QtWidgets.QComboBox(self.exact_polymer_tab)
        self.ActivatorComponent.addItem("None")
        self.ActivatorComponent.currentTextChanged.connect(
            lambda: self.set_atr(
                "ActivatorComponent", self.ActivatorComponent.currentText()
            )
        )
        self.form_layout.addRow("Activator Component:", self.ActivatorComponent)

        self.ExcessActivatorWash = QtWidgets.QComboBox(self.exact_polymer_tab)
        self.ExcessActivatorWash.addItem("None")
        self.ExcessActivatorWash.currentTextChanged.connect(
            lambda: self.set_atr(
                "ExcessActivatorWash", self.ExcessActivatorWash.currentText()
            )
        )
        self.form_layout.addRow("Excess Activator Wash:", self.ExcessActivatorWash)

        self.CleavingComponent = QtWidgets.QComboBox(self.exact_polymer_tab)
        self.CleavingComponent.addItem("None")
        self.CleavingComponent.currentTextChanged.connect(
            lambda: self.set_atr(
                "CleavingComponent", self.CleavingComponent.currentText()
            )
        )
        self.form_layout.addRow("Cleaving Component:", self.CleavingComponent)

        self.EndCap = QtWidgets.QComboBox(self.exact_polymer_tab)
        self.EndCap.addItem("None")
        self.EndCap.currentTextChanged.connect(
            lambda: self.set_atr("EndCapComponent", self.EndCap.currentText())
        )
        self.form_layout.addRow("End Cap Component:", self.EndCap)

        self.MonomerAbsorber = QtWidgets.QComboBox(self.exact_polymer_tab)
        self.MonomerAbsorber.addItem("None")
        self.MonomerAbsorber.currentTextChanged.connect(
            lambda: self.set_atr(
                "MonomerAbsorberVial", self.MonomerAbsorber.currentText()
            )
        )
        self.form_layout.addRow("Monomer Absorber Vial:", self.MonomerAbsorber)

        self.ActivatorVial = QtWidgets.QComboBox(self.exact_polymer_tab)
        self.ActivatorVial.addItem("None")
        self.ActivatorVial.currentTextChanged.connect(
            lambda: self.set_atr("ActivatorVial", self.ActivatorVial.currentText())
        )
        self.form_layout.addRow("Activator Vial:", self.ActivatorVial)

        self.left_panel.addLayout(self.form_layout)

        # Action Buttons Layout
        self.buttons_layout = QtWidgets.QHBoxLayout()

        self.AddComponentButton = QtWidgets.QPushButton(
            "Add Component", self.exact_polymer_tab
        )
        self.AddComponentButton.setMinimumHeight(40)
        self.AddComponentButton.clicked.connect(self._open_add_component_dialog)

        self.ReloadComponentsButton = QtWidgets.QPushButton(
            "Reload Component", self.exact_polymer_tab
        )
        self.ReloadComponentsButton.setMinimumHeight(40)
        self.ReloadComponentsButton.clicked.connect(self.load_components)

        self.pushButton = QtWidgets.QPushButton("Start", self.exact_polymer_tab)
        self.pushButton.setMinimumHeight(40)
        self.pushButton.clicked.connect(self._on_exact_polymer_start_press)

        self.buttons_layout.addWidget(self.AddComponentButton)
        self.buttons_layout.addWidget(self.ReloadComponentsButton)
        self.buttons_layout.addWidget(self.pushButton)

        self.left_panel.addStretch()
        self.left_panel.addLayout(self.buttons_layout)

        # MIDDLE COLUMN ("Monomer Selection" Container)
        self.monomer_group = QtWidgets.QGroupBox(
            "Monomer Selection", self.exact_polymer_tab
        )
        self.monomer_panel = QtWidgets.QVBoxLayout(self.monomer_group)

        self.monomer_list = ReorderableMonomerListWidget(self.monomer_group)
        self.monomer_list.setObjectName("monomer_list")
        self.monomer_panel.addWidget(self.monomer_list)

        # RIGHT COLUMN ("Cleaning Routine" Container)
        self.cleaning_group = QtWidgets.QGroupBox(
            "Cleaning Routine", self.exact_polymer_tab
        )
        self.cleaning_panel = QtWidgets.QVBoxLayout(self.cleaning_group)

        self.cleaning_list = ReorderablecleaningListWidget(self.cleaning_group)
        self.cleaning_list.setObjectName("cleaning_list")
        self.cleaning_panel.addWidget(self.cleaning_list)

        # Assemble Main Layout Split
        self.main_layout.addLayout(self.left_panel, stretch=1)
        self.main_layout.addWidget(self.monomer_group, stretch=1)
        self.main_layout.addWidget(self.cleaning_group, stretch=1)

        # ---------------------------------------------------------------------
        # TAB 2: Reaction Optimizer
        # ---------------------------------------------------------------------
        self.optimizer_tab = QtWidgets.QWidget()
        self.opt_main_layout = QtWidgets.QHBoxLayout(self.optimizer_tab)
        self.opt_main_layout.setContentsMargins(15, 15, 15, 15)
        self.opt_main_layout.setSpacing(20)

        # LEFT COLUMN: Campaign Setup, Controls, Volumes, Temperatures, and Batch Size
        self.opt_left_panel = QtWidgets.QVBoxLayout()
        self.opt_left_panel.setSpacing(12)

        # --- CAMPAIGN CONFIGURATION BOX ---
        self.campaign_config_group = QtWidgets.QGroupBox("Campaign Setup", self.optimizer_tab)
        self.campaign_config_layout = QtWidgets.QFormLayout(self.campaign_config_group)
        self.campaign_config_layout.setSpacing(8)

        self.CampaignNameInput = QtWidgets.QLineEdit(self.campaign_config_group)
        self.CampaignNameInput.setPlaceholderText("e.g. testing_new_saving")
        self.CampaignNameInput.setText("testing_new_saving")
        self.campaign_config_layout.addRow("Campaign Name:", self.CampaignNameInput)

        self.MaxReactionsInput = QtWidgets.QSpinBox(self.campaign_config_group)
        self.MaxReactionsInput.setRange(1, 10000)
        self.MaxReactionsInput.setValue(4)
        self.campaign_config_layout.addRow("Max Reactions:", self.MaxReactionsInput)

        self.opt_left_panel.addWidget(self.campaign_config_group)

        self.OptAddComponentButton = QtWidgets.QPushButton(
            "Add Component", self.optimizer_tab
        )
        self.OptAddComponentButton.setMinimumHeight(40)
        self.OptAddComponentButton.clicked.connect(self._open_add_component_dialog)

        self.OptReloadComponentsButton = QtWidgets.QPushButton(
            "Reload Component", self.optimizer_tab
        )
        self.OptReloadComponentsButton.setMinimumHeight(40)
        self.OptReloadComponentsButton.clicked.connect(self.load_components)

        self.AddMonomerListButton = QtWidgets.QPushButton(
            "＋ Add Reagent List", self.optimizer_tab
        )
        self.AddMonomerListButton.setMinimumHeight(40)
        self.AddMonomerListButton.clicked.connect(self._add_optimizer_monomer_set)

        self.OptStartButton = QtWidgets.QPushButton("Start", self.optimizer_tab)
        self.OptStartButton.setMinimumHeight(40)
        self.OptStartButton.clicked.connect(self._on_optimizer_start_press)

        self.opt_left_panel.addWidget(self.OptAddComponentButton)
        self.opt_left_panel.addWidget(self.OptReloadComponentsButton)
        self.opt_left_panel.addWidget(self.AddMonomerListButton)
        self.opt_left_panel.addWidget(self.OptStartButton)

        # --- 1. PER-LIST VOLUMES PANEL ---
        self.volumes_main_group = QtWidgets.QGroupBox(
            "Allowed Volume Settings (mL)", self.optimizer_tab
        )
        self.volumes_main_layout = QtWidgets.QVBoxLayout(self.volumes_main_group)

        self.volumes_scroll = QtWidgets.QScrollArea(self.volumes_main_group)
        self.volumes_scroll.setWidgetResizable(True)
        self.volumes_scroll_content = QtWidgets.QWidget()

        self.volumes_container_layout = QtWidgets.QVBoxLayout(
            self.volumes_scroll_content
        )
        self.volumes_container_layout.setContentsMargins(5, 5, 5, 5)
        self.volumes_container_layout.setSpacing(10)
        self.volumes_container_layout.addStretch()

        self.volumes_scroll.setWidget(self.volumes_scroll_content)
        self.volumes_main_layout.addWidget(self.volumes_scroll)

        self.opt_left_panel.addWidget(self.volumes_main_group, stretch=2)

        # --- 2. SINGLE GLOBAL TEMPERATURES PANEL ---
        self.temperatures_main_group = QtWidgets.QGroupBox(
            "Allowed Temperature Settings (°C)", self.optimizer_tab
        )
        self.temperatures_main_layout = QtWidgets.QVBoxLayout(self.temperatures_main_group)

        self.add_global_temp_btn = QtWidgets.QPushButton(
            "＋ Add Target Temperature", self.temperatures_main_group
        )
        self.add_global_temp_btn.setFixedHeight(28)
        self.add_global_temp_btn.clicked.connect(lambda: self._add_global_temperature_row(20.0))
        self.temperatures_main_layout.addWidget(self.add_global_temp_btn)

        self.temperatures_scroll = QtWidgets.QScrollArea(self.temperatures_main_group)
        self.temperatures_scroll.setWidgetResizable(True)
        self.temperatures_scroll_content = QtWidgets.QWidget()

        self.temperatures_container_layout = QtWidgets.QVBoxLayout(
            self.temperatures_scroll_content
        )
        self.temperatures_container_layout.setContentsMargins(5, 5, 5, 5)
        self.temperatures_container_layout.setSpacing(6)
        self.temperatures_container_layout.addStretch()

        self.temperatures_scroll.setWidget(self.temperatures_scroll_content)
        self.temperatures_main_layout.addWidget(self.temperatures_scroll)

        self.opt_left_panel.addWidget(self.temperatures_main_group, stretch=2)

        # Seed global temperature entries
        self._add_global_temperature_row(20.0)

        # --- 3. BATCH SIZE INPUT BOX ---
        self.batch_size_group = QtWidgets.QGroupBox("Batch Size", self.optimizer_tab)
        self.batch_size_layout = QtWidgets.QHBoxLayout(self.batch_size_group)
        self.batch_size_layout.setContentsMargins(10, 8, 10, 8)

        self.batch_size_label = QtWidgets.QLabel("Batch Size:", self.batch_size_group)
        self.BatchSizeInput = QtWidgets.QSpinBox(self.batch_size_group)
        self.BatchSizeInput.setRange(1, 1000)
        self.BatchSizeInput.setValue(1)

        self.batch_size_layout.addWidget(self.batch_size_label)
        self.batch_size_layout.addWidget(self.BatchSizeInput)

        self.opt_left_panel.addWidget(self.batch_size_group, stretch=0)

        # RIGHT COLUMN: Scroll Area containing "Reagent List" widgets
        self.opt_scroll = QtWidgets.QScrollArea(self.optimizer_tab)
        self.opt_scroll.setWidgetResizable(True)
        self.opt_scroll_content = QtWidgets.QWidget()

        self.opt_lists_layout = QtWidgets.QHBoxLayout(self.opt_scroll_content)
        self.opt_lists_layout.setContentsMargins(10, 10, 10, 10)
        self.opt_lists_layout.setSpacing(15)

        self.opt_scroll.setWidget(self.opt_scroll_content)

        # Assemble Reaction Optimizer Split
        self.opt_main_layout.addLayout(self.opt_left_panel, stretch=1)
        self.opt_main_layout.addWidget(self.opt_scroll, stretch=3)

        # Seed with initial reagent list
        self._add_optimizer_monomer_set()

        # Add both tabs into Tab Container
        self.tab_widget.addTab(self.exact_polymer_tab, "Exact Polymer")
        self.tab_widget.addTab(self.optimizer_tab, "Reaction Optimizer")

        MainWindow.setCentralWidget(self.centralwidget)

        # Menubar & Statusbar
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        MainWindow.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        self.set_connections(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def _add_global_temperature_row(self, initial_val=20.0):
        """Adds a single temperature spinbox to the global temperature list."""
        row_widget = QtWidgets.QWidget(self.temperatures_scroll_content)
        row_layout = QtWidgets.QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)

        spinbox = QtWidgets.QDoubleSpinBox(row_widget)
        spinbox.setRange(-80.0, 200.0)
        spinbox.setDecimals(1)
        spinbox.setSingleStep(1.0)
        spinbox.setValue(initial_val)
        spinbox.setSuffix(" °C")

        del_btn = QtWidgets.QPushButton("✕", row_widget)
        del_btn.setFixedWidth(24)
        del_btn.setToolTip("Remove temperature")

        row_layout.addWidget(spinbox)
        row_layout.addWidget(del_btn)

        self.global_temp_spinboxes.append(spinbox)
        self.temperatures_container_layout.insertWidget(
            self.temperatures_container_layout.count() - 1, row_widget
        )

        del_btn.clicked.connect(
            lambda: self._remove_global_temperature_row(row_widget, spinbox)
        )

    def _remove_global_temperature_row(self, row_widget, spinbox):
        """Removes a temperature spinbox from the global temperature list."""
        if spinbox in self.global_temp_spinboxes:
            self.global_temp_spinboxes.remove(spinbox)

        self.temperatures_container_layout.removeWidget(row_widget)
        row_widget.deleteLater()

    def _add_optimizer_monomer_set(self):
        """Adds a new single-reagent list widget along with its specific volume container."""
        group_box = QtWidgets.QGroupBox("", self.opt_scroll_content)
        group_layout = QtWidgets.QVBoxLayout(group_box)

        # Sub-header bar with Remove List button
        top_bar = QtWidgets.QHBoxLayout()
        remove_btn = QtWidgets.QPushButton("Remove List", group_box)
        remove_btn.setFixedHeight(24)
        top_bar.addStretch()
        top_bar.addWidget(remove_btn)
        group_layout.addLayout(top_bar)

        # Single Reagent List Widget
        monomer_list = OptimizerReagentListWidget(group_box, reagents=self.components_cache)

        group_layout.addWidget(monomer_list)

        # --- VOLUMES CONTAINER FOR THIS SPECIFIC REAGENT LIST ---
        vol_group = QtWidgets.QGroupBox("", self.volumes_scroll_content)
        vol_layout = QtWidgets.QVBoxLayout(vol_group)
        vol_layout.setContentsMargins(8, 8, 8, 8)
        vol_layout.setSpacing(6)

        add_vol_btn = QtWidgets.QPushButton("＋ Add Volume", vol_group)
        add_vol_btn.setFixedHeight(24)
        vol_layout.addWidget(add_vol_btn)

        vol_spinboxes = []

        entry = {
            "group_box": group_box,
            "list_widget": monomer_list,
            "vol_group_box": vol_group,
            "vol_layout": vol_layout,
            "vol_spinboxes": vol_spinboxes,
        }

        def _add_volume_row(initial_val=10.0):
            row_widget = QtWidgets.QWidget(vol_group)
            row_layout = QtWidgets.QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)

            spinbox = QtWidgets.QDoubleSpinBox(row_widget)
            spinbox.setRange(0.0, 10000.0)
            spinbox.setDecimals(2)
            spinbox.setSingleStep(0.5)
            spinbox.setValue(initial_val)
            spinbox.setSuffix(" mL")

            del_btn = QtWidgets.QPushButton("✕", row_widget)
            del_btn.setFixedWidth(24)
            del_btn.setToolTip("Remove volume")

            row_layout.addWidget(spinbox)
            row_layout.addWidget(del_btn)

            vol_spinboxes.append(spinbox)
            vol_layout.insertWidget(vol_layout.count() - 1, row_widget)

            del_btn.clicked.connect(
                lambda: self._remove_volume_row(entry, row_widget, spinbox)
            )

        add_vol_btn.clicked.connect(lambda: _add_volume_row())

        # Seed with initial volume spinboxes
        _add_volume_row(10.0)

        remove_btn.clicked.connect(
            lambda: self._remove_optimizer_monomer_set(entry)
        )

        self.optimizer_reagent_entries.append(entry)

        # Place volume panel above stretch spacer
        self.volumes_container_layout.insertWidget(
            self.volumes_container_layout.count() - 1, vol_group
        )
        self.opt_lists_layout.addWidget(group_box)

        self._update_reagent_list_titles()

    def _remove_volume_row(self, entry, row_widget, spinbox):
        """Removes a single volume row entry."""
        if spinbox in entry["vol_spinboxes"]:
            entry["vol_spinboxes"].remove(spinbox)

        entry["vol_layout"].removeWidget(row_widget)
        row_widget.deleteLater()

    def _remove_optimizer_monomer_set(self, entry):
        """Removes a reagent list container and its volume group."""
        if entry in self.optimizer_reagent_entries:
            self.optimizer_reagent_entries.remove(entry)

        # Clean up Reagent List groupbox
        group_box = entry["group_box"]
        self.opt_lists_layout.removeWidget(group_box)
        group_box.deleteLater()

        # Clean up Volume groupbox
        vol_group = entry["vol_group_box"]
        self.volumes_container_layout.removeWidget(vol_group)
        vol_group.deleteLater()

        self._update_reagent_list_titles()

    def _update_reagent_list_titles(self):
        """Re-indexes group titles as 'reagent list 1', 'reagent list 2', etc."""
        for i, entry in enumerate(self.optimizer_reagent_entries, start=1):
            entry["group_box"].setTitle(f"reagent list {i}")
            entry["vol_group_box"].setTitle(f"reagent list {i} volumes:")

    def set_connections(self, MainWindow):
        for checkbox in self.centralwidget.findChildren(QtWidgets.QCheckBox):
            checkbox.toggled.connect(lambda: self._set_block_attributes(MainWindow))

    def _set_block_attributes(self, MainWindow):
        self.EndCap.setEnabled(self.end_cap.isChecked())
        self.MonomerAbsorber.setEnabled(
            self.monomer_removal_solid_supported.isChecked()
        )
        self.CleavingComponent.setEnabled(self.solid_supported_polymer.isChecked())
        self.ActivatorVial.setEnabled(self.activator_solid_supported.isChecked())

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(
            _translate("MainWindow", "Exact Polymer Reaction Manager")
        )

    def _open_add_component_dialog(self):
        """Instantiates and shows the AddComponentDialog modal."""
        dialog = AddComponentDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            component_data = dialog.get_data()
            print("New Component Configured:", component_data)

            comp_name = component_data.get("name", "").strip()
            if comp_name:
                new_component = {
                    comp_name: {
                        "type": "vial",
                        "hotplate": component_data["hotplate"],
                        "used": component_data["is_filled"],
                        "valve_connections": component_data["connections"],
                    }
                }
                with open(r".\CampaignSetup\components.json", "r") as file:
                    components = json.load(file)
                components.update(new_component)

                self._update_all_dropdowns(components)

                # Save to File
                with open(r".\CampaignSetup\components.json", "w") as file:
                    json.dump(components, file, indent=4)

    def load_components(self):
        try:
            with open(r".\CampaignSetup\components.json", "r") as file:
                components = json.load(file)
                self._update_all_dropdowns(components)
        except (FileNotFoundError, json.JSONDecodeError) as err:
            print(f"Error loading components: {err}")

    def _update_all_dropdowns(self, components):
        """Updates main window comboboxes and all dynamic monomer/cleaning widgets."""
        self.components_cache = components
        selectors = self.centralwidget.findChildren(QtWidgets.QComboBox)

        for component in components:
            for selector in selectors:
                selector.addItem(component)

        # Update Exact Polymer Tab Widgets
        self.monomer_list.set_dropdown_options(components, components)
        self.cleaning_list.set_dropdown_options(list(components.keys()))

        # Update all active reagent lists in Reaction Optimizer Tab
        for entry in self.optimizer_reagent_entries:
            entry["list_widget"].set_dropdown_options(components)

    def set_atr(self, start_value, new_value):
        self.reaction_plan.__setattr__(start_value, new_value)

    def _on_exact_polymer_start_press(self):
        """Signal handler for Start button on the Exact Polymer tab."""
        print("Starting Exact Polymer Workflow...")
        if hasattr(self.monomer_list, "get_monomer_order"):
            print("Monomers:", self.monomer_list.get_monomer_order())
        if hasattr(self.cleaning_list, "get_ordered_data"):
            print("Cleaning Routine:", self.cleaning_list.get_ordered_data())

    def _on_optimizer_start_press(self):
        """Generates a campaign configuration JSON file formatted for planner/optimizer consumption."""
        campaign_name = self.CampaignNameInput.text().strip() or "campaign_config"
        max_reactions = self.MaxReactionsInput.value()
        batch_size = self.BatchSizeInput.value()
        num_reagent_lists = len(self.optimizer_reagent_entries)

        # Build dynamic reaction_components mapping
        reaction_components = {}

        for i, entry in enumerate(self.optimizer_reagent_entries, start=1):
            monomer_widget = entry["list_widget"]
            reagents = monomer_widget.get_monomer_order() if hasattr(monomer_widget, "get_monomer_order") else []
            volumes = [sb.value() for sb in entry["vol_spinboxes"]]

            reaction_components[f"reagents_{i}"] = reagents
            reaction_components[f"reagent_volumes_{i}"] = volumes

        temperatures = [sb.value() for sb in self.global_temp_spinboxes]
        reaction_components["temperature"] = temperatures

        # Construct configuration JSON structure matching template
        config_data = {
            "campaign_name": campaign_name,
            "max_number_of_reactions": max_reactions,
            "number_of_reagent_lists": num_reagent_lists,
            "reaction_components": reaction_components,
            "planner_setup": {
                "objectives": ["yield", "time"],
                "objective_mode": ["max", "min"],
                "batch": batch_size,
                "columns_features": "all",
                "init_sampling_method": "cvt",
            },
            "syringe": "syringe_1",
        }

        json_filename = f"./CampaignSetup/Experiments/{campaign_name}.json"

        try:
            with open(json_filename, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)

            QtWidgets.QMessageBox.information(
                self,
                "JSON Export Successful",
                f"Successfully saved campaign configuration to '{json_filename}'.",
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to generate JSON file:\n{str(e)}",
            )
        core = Campaign()
        core.start()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()

    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)

    MainWindow.show()
    sys.exit(app.exec_())