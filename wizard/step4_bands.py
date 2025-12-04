"""
Wizard Step 4: Band Mapping
"""

from qgis.PyQt.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QFormLayout, QTextEdit, QCheckBox
)
from qgis.core import QgsProject, QgsRasterLayer, QgsMessageLog, Qgis


class Step4BandsPage(QWizardPage):
    """Wizard page for band mapping."""

    def __init__(self, parent=None):
        """Initialize the band mapping page."""
        super().__init__(parent)
        self.setTitle("Band Mapping")
        self.setSubTitle("Map spectral bands for classification")
        
        self.band_mapping = {}
        self.raster_layer = None
        self.init_ui()

    def initializePage(self):
        """Initialize page when shown."""
        # Try to detect raster layer from canvas
        self.detect_raster_layer()
        if self.raster_layer:
            self.auto_detect_bands()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Raster layer selection
        layer_layout = QHBoxLayout()
        layer_layout.addWidget(QLabel("Raster Layer:"))
        self.layer_combo = QComboBox()
        self.layer_combo.currentIndexChanged.connect(self.on_layer_changed)
        layer_layout.addWidget(self.layer_combo)
        self.refresh_layer_button = QPushButton("Refresh")
        self.refresh_layer_button.clicked.connect(self.refresh_layers)
        layer_layout.addWidget(self.refresh_layer_button)
        layout.addLayout(layer_layout)

        # Band mapping group
        self.bands_group = QGroupBox("Band Mapping")
        self.bands_layout = QFormLayout()
        self.bands_group.setLayout(self.bands_layout)
        layout.addWidget(self.bands_group)

        # Standard Sentinel-2 / Landsat bands
        self.band_combos = {}
        standard_bands = [
            ("B2", "Blue"),
            ("B3", "Green"),
            ("B4", "Red"),
            ("B8", "NIR"),
            ("B11", "SWIR")
        ]

        for band_code, band_name in standard_bands:
            combo = QComboBox()
            combo.addItem("(Not used)")
            combo.currentIndexChanged.connect(self.on_band_changed)
            self.bands_layout.addRow(f"{band_code} ({band_name}):", combo)
            self.band_combos[band_code] = combo

        # Auto-detect button
        auto_layout = QHBoxLayout()
        self.auto_detect_button = QPushButton("Auto-detect Bands")
        self.auto_detect_button.clicked.connect(self.auto_detect_bands)
        auto_layout.addWidget(self.auto_detect_button)
        auto_layout.addStretch()
        layout.addLayout(auto_layout)

        # Status text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(100)
        layout.addWidget(self.status_text)

        self.refresh_layers()

    def refresh_layers(self):
        """Refresh available raster layers."""
        self.layer_combo.clear()
        self.layer_combo.addItem("(Select layer)")
        
        project = QgsProject.instance()
        for layer in project.mapLayers().values():
            if isinstance(layer, QgsRasterLayer):
                self.layer_combo.addItem(layer.name(), layer.id())

    def on_layer_changed(self):
        """Handle raster layer selection."""
        if self.layer_combo.currentIndex() > 0:
            layer_id = self.layer_combo.currentData()
            self.raster_layer = QgsProject.instance().mapLayer(layer_id)
            if self.raster_layer:
                self.update_band_combos()
                self.auto_detect_bands()
        else:
            self.raster_layer = None
        self.completeChanged.emit()

    def detect_raster_layer(self):
        """Try to detect raster layer from active layer."""
        wizard = self.wizard()
        if not hasattr(wizard, 'iface'):
            return
        iface = wizard.iface
        active_layer = iface.activeLayer()
        if isinstance(active_layer, QgsRasterLayer):
            self.raster_layer = active_layer
            # Set in combo
            for i in range(self.layer_combo.count()):
                if self.layer_combo.itemData(i) == active_layer.id():
                    self.layer_combo.setCurrentIndex(i)
                    break

    def update_band_combos(self):
        """Update band combo boxes with available bands."""
        if not self.raster_layer:
            return

        band_count = self.raster_layer.bandCount()
        
        for combo in self.band_combos.values():
            # Clear existing items except first
            while combo.count() > 1:
                combo.removeItem(1)
            
            # Add band options
            for i in range(1, band_count + 1):
                combo.addItem(f"Band {i}")

    def auto_detect_bands(self):
        """Auto-detect bands based on Sentinel-2 / Landsat naming."""
        if not self.raster_layer:
            self.status_text.setPlainText("Please select a raster layer first")
            return

        # Try to detect from layer name or band names
        layer_name = self.raster_layer.name().upper()
        band_count = self.raster_layer.bandCount()

        # Common Sentinel-2 / Landsat band order
        # Sentinel-2: B2, B3, B4, B8, B11 (bands 1, 2, 3, 7, 11)
        # Landsat 8: B2, B3, B4, B5, B6 (bands 2, 3, 4, 5, 6)
        
        detected = False
        status_messages = []

        # Try Sentinel-2 pattern
        if "SENTINEL" in layer_name or band_count >= 12:
            # Sentinel-2 typical order: B2=1, B3=2, B4=3, B8=7, B11=11
            if band_count >= 11:
                self.band_combos["B2"].setCurrentIndex(1)  # Band 1
                self.band_combos["B3"].setCurrentIndex(2)  # Band 2
                self.band_combos["B4"].setCurrentIndex(3)  # Band 3
                self.band_combos["B8"].setCurrentIndex(7)  # Band 7
                self.band_combos["B11"].setCurrentIndex(11)  # Band 11
                detected = True
                status_messages.append("Detected Sentinel-2 band pattern")
        
        # Try Landsat pattern
        elif "LANDSAT" in layer_name or (band_count >= 7 and band_count <= 11):
            # Landsat 8 typical order: B2=2, B3=3, B4=4, B5=5, B6=6
            if band_count >= 6:
                self.band_combos["B2"].setCurrentIndex(2)  # Band 2
                self.band_combos["B3"].setCurrentIndex(3)  # Band 3
                self.band_combos["B4"].setCurrentIndex(4)  # Band 4
                self.band_combos["B8"].setCurrentIndex(5)  # Band 5 (NIR)
                if band_count >= 6:
                    self.band_combos["B11"].setCurrentIndex(6)  # Band 6 (SWIR)
                detected = True
                status_messages.append("Detected Landsat band pattern")

        # Fallback: use first available bands
        if not detected and band_count >= 3:
            self.band_combos["B2"].setCurrentIndex(1)  # Band 1
            self.band_combos["B3"].setCurrentIndex(2)  # Band 2
            self.band_combos["B4"].setCurrentIndex(3)  # Band 3
            if band_count >= 4:
                self.band_combos["B8"].setCurrentIndex(4)  # Band 4
            if band_count >= 5:
                self.band_combos["B11"].setCurrentIndex(5)  # Band 5
            status_messages.append("Using first available bands (auto-detection failed)")

        if status_messages:
            self.status_text.setPlainText("\n".join(status_messages))
        else:
            self.status_text.setPlainText("Could not auto-detect bands. Please map manually.")

        self.on_band_changed()

    def on_band_changed(self):
        """Handle band selection change."""
        self.band_mapping = {}
        for band_code, combo in self.band_combos.items():
            if combo.currentIndex() > 0:
                band_number = combo.currentIndex()  # 1-based
                self.band_mapping[band_code] = band_number
        
        # Update status
        if self.band_mapping:
            mapping_str = ", ".join([f"{k}=Band {v}" for k, v in self.band_mapping.items()])
            self.status_text.setPlainText(f"Mapped bands: {mapping_str}")
        else:
            self.status_text.setPlainText("No bands mapped")
        
        self.completeChanged.emit()

    def get_band_mapping(self):
        """Get band mapping dictionary."""
        return {
            "layer": self.raster_layer,
            "bands": self.band_mapping.copy()
        }

    def isComplete(self):
        """Check if the page is complete."""
        return self.raster_layer is not None and len(self.band_mapping) >= 3

