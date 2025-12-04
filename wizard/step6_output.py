"""
Wizard Step 6: Output Options - Updated with new checkboxes and buttons
"""

from qgis.PyQt.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QCheckBox, QFileDialog, QSpinBox, QFormLayout, QMessageBox
)
from qgis.core import QgsProject, QgsMessageLog, Qgis
import os


class Step6OutputPage(QWizardPage):
    """Wizard page for output options with new features."""

    def __init__(self, parent=None):
        """Initialize the output options page."""
        super().__init__(parent)
        self.setTitle("Output Options")
        self.setSubTitle("Configure output settings and postprocessing")
        
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Output directory
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("Output Directory:"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Select output directory...")
        dir_layout.addWidget(self.output_dir_edit)
        self.dir_browse_button = QPushButton("Browse...")
        self.dir_browse_button.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(self.dir_browse_button)
        layout.addLayout(dir_layout)

        # Output options group
        output_group = QGroupBox("Output Files")
        output_layout = QVBoxLayout()
        output_group.setLayout(output_layout)

        self.save_raw_checkbox = QCheckBox("Save raw cluster raster (clusters_raw.tif)")
        self.save_raw_checkbox.setChecked(True)
        output_layout.addWidget(self.save_raw_checkbox)

        self.enable_postprocessing_checkbox = QCheckBox("Enable postprocessing (majority filter + small cluster removal)")
        self.enable_postprocessing_checkbox.setChecked(False)
        output_layout.addWidget(self.enable_postprocessing_checkbox)

        # Postprocessing parameters
        postprocessing_layout = QFormLayout()
        self.min_area_spin = QSpinBox()
        self.min_area_spin.setMinimum(1)
        self.min_area_spin.setMaximum(10000)
        self.min_area_spin.setValue(100)
        self.min_area_spin.setEnabled(False)
        postprocessing_layout.addRow("Minimum cluster area (pixels):", self.min_area_spin)
        output_layout.addLayout(postprocessing_layout)

        self.enable_postprocessing_checkbox.toggled.connect(
            lambda checked: self.min_area_spin.setEnabled(checked)
        )

        self.save_interpreted_checkbox = QCheckBox("Save interpreted raster (interpreted_layer.tif)")
        self.save_interpreted_checkbox.setChecked(True)
        output_layout.addWidget(self.save_interpreted_checkbox)

        self.save_report_checkbox = QCheckBox("Save interpretation report (interpretation_report.json)")
        self.save_report_checkbox.setChecked(True)
        output_layout.addWidget(self.save_report_checkbox)

        layout.addWidget(output_group)

        # LLM options
        llm_group = QGroupBox("LLM Interpretation")
        llm_layout = QVBoxLayout()
        llm_group.setLayout(llm_layout)

        self.enable_llm_checkbox = QCheckBox("Enable LLM interpretation")
        self.enable_llm_checkbox.setChecked(True)
        self.enable_llm_checkbox.toggled.connect(self.on_llm_toggled)
        llm_layout.addWidget(self.enable_llm_checkbox)

        # LLM buttons
        llm_button_layout = QHBoxLayout()
        self.preview_llm_button = QPushButton("Preview LLM Mapping")
        self.preview_llm_button.setEnabled(False)
        self.preview_llm_button.clicked.connect(self.preview_llm_mapping)
        llm_button_layout.addWidget(self.preview_llm_button)

        self.run_llm_button = QPushButton("Run LLM Interpretation")
        self.run_llm_button.setEnabled(False)
        self.run_llm_button.clicked.connect(self.run_llm_interpretation)
        llm_button_layout.addWidget(self.run_llm_button)

        llm_layout.addLayout(llm_button_layout)

        layout.addWidget(llm_group)

        # Add to map checkbox
        self.add_to_map_checkbox = QCheckBox("Add output layer to map")
        self.add_to_map_checkbox.setChecked(True)
        layout.addWidget(self.add_to_map_checkbox)

        layout.addStretch()

    def on_llm_toggled(self, enabled):
        """Handle LLM checkbox toggle."""
        self.preview_llm_button.setEnabled(enabled)
        self.run_llm_button.setEnabled(enabled)

    def browse_output_dir(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            ""
        )
        if directory:
            self.output_dir_edit.setText(directory)

    def preview_llm_mapping(self):
        """Preview LLM mapping (placeholder)."""
        QMessageBox.information(
            self,
            "Preview LLM Mapping",
            "This will show a preview of the LLM interpretation mapping.\n"
            "Feature coming soon."
        )

    def run_llm_interpretation(self):
        """Run LLM interpretation (placeholder)."""
        QMessageBox.information(
            self,
            "Run LLM Interpretation",
            "This will run the LLM interpretation now.\n"
            "Feature coming soon."
        )

    def get_output_options(self):
        """Get output options dictionary."""
        output_dir = self.output_dir_edit.text()
        if not output_dir:
            # Use temporary directory
            import tempfile
            output_dir = tempfile.mkdtemp(prefix="ai_classification_")
        
        return {
            "output_dir": output_dir,
            "save_raw": self.save_raw_checkbox.isChecked(),
            "enable_postprocessing": self.enable_postprocessing_checkbox.isChecked(),
            "min_area_pixels": self.min_area_spin.value(),
            "save_interpreted": self.save_interpreted_checkbox.isChecked(),
            "save_report": self.save_report_checkbox.isChecked(),
            "enable_llm": self.enable_llm_checkbox.isChecked(),
            "add_to_map": self.add_to_map_checkbox.isChecked()
        }

    def isComplete(self):
        """Check if the page is complete."""
        # Output directory is optional (will use temp if not set)
        return True
