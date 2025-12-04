"""
Wizard Step 1: Algorithm Selection - Updated with no default selection
"""

from qgis.PyQt.QtWidgets import (
    QWizardPage, QVBoxLayout, QLabel, QRadioButton, QButtonGroup,
    QGroupBox, QTextEdit
)
from qgis.core import QgsApplication, QgsMessageLog, Qgis


class Step1AlgorithmPage(QWizardPage):
    """Wizard page for algorithm selection - NO DEFAULT SELECTION."""

    def __init__(self, parent=None):
        """Initialize the algorithm selection page."""
        super().__init__(parent)
        self.setTitle("Algorithm Selection")
        self.setSubTitle("Select the classification algorithm to use (required)")
        
        self.selected_algorithm = None
        self.init_ui()
        self.detect_providers()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Algorithm selection group
        self.algorithm_group = QButtonGroup(self)
        
        # OTB option
        self.otb_radio = QRadioButton("OTB (Orfeo ToolBox)")
        self.otb_radio.setEnabled(False)
        self.algorithm_group.addButton(self.otb_radio, 0)
        layout.addWidget(self.otb_radio)

        # SAGA option
        self.saga_radio = QRadioButton("SAGA")
        self.saga_radio.setEnabled(False)
        self.algorithm_group.addButton(self.saga_radio, 1)
        layout.addWidget(self.saga_radio)

        # GRASS option
        self.grass_radio = QRadioButton("GRASS")
        self.grass_radio.setEnabled(False)
        self.algorithm_group.addButton(self.grass_radio, 2)
        layout.addWidget(self.grass_radio)

        # Python fallback option (always available)
        self.python_radio = QRadioButton("Python (K-means with NDVI/MNDWI/NDBI)")
        # NO DEFAULT SELECTION - user must choose
        self.algorithm_group.addButton(self.python_radio, 3)
        layout.addWidget(self.python_radio)

        # Info box (dynamic)
        info_label = QLabel("Algorithm Information:")
        layout.addWidget(info_label)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(120)
        self.info_text.setPlainText("Please select an algorithm to see information.")
        layout.addWidget(self.info_text)

        # Connect signals
        self.algorithm_group.buttonClicked.connect(self.on_algorithm_selected)
        
        # Initial info update
        self.update_info_text()

    def detect_providers(self):
        """Detect available classification providers."""
        status_messages = []
        available_count = 0

        # Check OTB
        otb_available = self.check_otb_available()
        if otb_available:
            self.otb_radio.setEnabled(True)
            status_messages.append("✓ OTB (Orfeo ToolBox) - Available")
            available_count += 1
        else:
            status_messages.append("✗ OTB (Orfeo ToolBox) - Not available")

        # Check SAGA
        saga_available = self.check_saga_available()
        if saga_available:
            self.saga_radio.setEnabled(True)
            status_messages.append("✓ SAGA - Available")
            available_count += 1
        else:
            status_messages.append("✗ SAGA - Not available")

        # Check GRASS
        grass_available = self.check_grass_available()
        if grass_available:
            self.grass_radio.setEnabled(True)
            status_messages.append("✓ GRASS - Available")
            available_count += 1
        else:
            status_messages.append("✗ GRASS - Not available")

        # Python is always available
        status_messages.append("✓ Python (K-means) - Always available")

    def check_otb_available(self):
        """Check if OTB is available."""
        try:
            from qgis.core import QgsApplication
            providers = QgsApplication.processingRegistry().providers()
            for provider in providers:
                if 'otb' in provider.id().lower():
                    return True
            return False
        except Exception:
            return False

    def check_saga_available(self):
        """Check if SAGA is available."""
        try:
            from qgis.core import QgsApplication
            providers = QgsApplication.processingRegistry().providers()
            for provider in providers:
                if 'saga' in provider.id().lower():
                    return True
            return False
        except Exception:
            return False

    def check_grass_available(self):
        """Check if GRASS is available."""
        try:
            from qgis.core import QgsApplication
            providers = QgsApplication.processingRegistry().providers()
            for provider in providers:
                if 'grass' in provider.id().lower():
                    return True
            return False
        except Exception:
            return False

    def on_algorithm_selected(self, button):
        """Handle algorithm selection."""
        if button == self.otb_radio:
            self.selected_algorithm = "otb"
        elif button == self.saga_radio:
            self.selected_algorithm = "saga"
        elif button == self.grass_radio:
            self.selected_algorithm = "grass"
        elif button == self.python_radio:
            self.selected_algorithm = "python"
        
        self.update_info_text()
        self.completeChanged.emit()

    def update_info_text(self):
        """Update info text based on selected algorithm."""
        if self.selected_algorithm == "python":
            self.info_text.setPlainText(
                "Python (always available):\n"
                "K-means clustering with NDVI/MNDWI/NDBI features, full control.\n"
                "Includes resampling, postprocessing, and LLM interpretation."
            )
        elif self.selected_algorithm == "saga":
            self.info_text.setPlainText(
                "SAGA:\n"
                "Uses SAGA's K-means. Falls back to Python if unavailable."
            )
        elif self.selected_algorithm == "grass":
            self.info_text.setPlainText(
                "GRASS:\n"
                "Uses GRASS i.cluster. Falls back to Python if unavailable."
            )
        elif self.selected_algorithm == "otb":
            self.info_text.setPlainText(
                "OTB (Orfeo ToolBox):\n"
                "Orfeo Toolbox. Nur wenn installiert."
            )
        else:
            self.info_text.setPlainText("Please select an algorithm to see information.")

    def get_algorithm(self):
        """Get the selected algorithm."""
        return self.selected_algorithm

    def isComplete(self):
        """Check if the page is complete - REQUIRES SELECTION."""
        return self.selected_algorithm is not None
