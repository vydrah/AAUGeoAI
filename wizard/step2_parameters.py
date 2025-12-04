"""
Wizard Step 2: Parameter Configuration
"""

from qgis.PyQt.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QDoubleSpinBox, QGroupBox, QFormLayout, QComboBox
)
from qgis.PyQt.QtCore import pyqtSignal


class Step2ParametersPage(QWizardPage):
    """Wizard page for parameter configuration."""

    def __init__(self, parent=None):
        """Initialize the parameters page."""
        super().__init__(parent)
        self.setTitle("Parameter Configuration")
        self.setSubTitle("Configure classification parameters")
        
        self.algorithm = None
        self.init_ui()

    def initializePage(self):
        """Initialize page based on selected algorithm."""
        # Get algorithm from previous step
        wizard = self.wizard()
        if wizard:
            self.algorithm = wizard.get_algorithm()
            self.update_parameters_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Parameters group
        self.params_group = QGroupBox("Classification Parameters")
        self.params_layout = QFormLayout()
        self.params_group.setLayout(self.params_layout)
        layout.addWidget(self.params_group)

        # Common parameters (will be shown/hidden based on algorithm)
        self.num_clusters_spin = QSpinBox()
        self.num_clusters_spin.setMinimum(2)
        self.num_clusters_spin.setMaximum(50)
        self.num_clusters_spin.setValue(5)
        self.params_layout.addRow("Number of Clusters:", self.num_clusters_spin)

        self.max_iterations_spin = QSpinBox()
        self.max_iterations_spin.setMinimum(1)
        self.max_iterations_spin.setMaximum(1000)
        self.max_iterations_spin.setValue(100)
        self.params_layout.addRow("Max Iterations:", self.max_iterations_spin)

        # Algorithm-specific parameters (will be added dynamically)
        self.algorithm_params = {}

    def update_parameters_ui(self):
        """Update UI based on selected algorithm."""
        # Clear existing algorithm-specific parameters
        for widget in self.algorithm_params.values():
            if widget.parent():
                self.params_layout.removeRow(widget)
        self.algorithm_params.clear()

        if self.algorithm == "python":
            self.setup_python_params()
        elif self.algorithm == "otb":
            self.setup_otb_params()
        elif self.algorithm == "saga":
            self.setup_saga_params()
        elif self.algorithm == "grass":
            self.setup_grass_params()

    def setup_python_params(self):
        """Setup parameters for Python K-means."""
        # Initialization method
        init_combo = QComboBox()
        init_combo.addItems(["k-means++", "random"])
        self.params_layout.addRow("Initialization:", init_combo)
        self.algorithm_params["initialization"] = init_combo

        # Random seed
        seed_spin = QSpinBox()
        seed_spin.setMinimum(0)
        seed_spin.setMaximum(999999)
        seed_spin.setValue(42)
        self.params_layout.addRow("Random Seed:", seed_spin)
        self.algorithm_params["random_seed"] = seed_spin

    def setup_otb_params(self):
        """Setup parameters for OTB."""
        # OTB-specific parameters
        sampling_rate_spin = QDoubleSpinBox()
        sampling_rate_spin.setMinimum(0.01)
        sampling_rate_spin.setMaximum(1.0)
        sampling_rate_spin.setValue(0.1)
        sampling_rate_spin.setSingleStep(0.01)
        self.params_layout.addRow("Sampling Rate:", sampling_rate_spin)
        self.algorithm_params["sampling_rate"] = sampling_rate_spin

    def setup_saga_params(self):
        """Setup parameters for SAGA."""
        # SAGA-specific parameters
        method_combo = QComboBox()
        method_combo.addItems(["Iterative Minimum Distance", "Cluster Analysis"])
        self.params_layout.addRow("Method:", method_combo)
        self.algorithm_params["method"] = method_combo

    def setup_grass_params(self):
        """Setup parameters for GRASS."""
        # GRASS-specific parameters
        min_size_spin = QSpinBox()
        min_size_spin.setMinimum(1)
        min_size_spin.setMaximum(1000)
        min_size_spin.setValue(10)
        self.params_layout.addRow("Minimum Cluster Size:", min_size_spin)
        self.algorithm_params["min_size"] = min_size_spin

    def get_parameters(self):
        """Get all parameters as a dictionary."""
        params = {
            "num_clusters": self.num_clusters_spin.value(),
            "max_iterations": self.max_iterations_spin.value(),
            "algorithm": self.algorithm
        }

        # Add algorithm-specific parameters
        for key, widget in self.algorithm_params.items():
            if isinstance(widget, QSpinBox):
                params[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                params[key] = widget.value()
            elif isinstance(widget, QComboBox):
                params[key] = widget.currentText()

        return params

    def isComplete(self):
        """Check if the page is complete."""
        return self.algorithm is not None

