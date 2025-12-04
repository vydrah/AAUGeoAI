"""
AI Processing Log DockWidget for AI Unsupervised Classification Plugin
"""

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
)
from qgis.core import QgsMessageLog, Qgis
from datetime import datetime


class ProcessingLogDockWidget(QDockWidget):
    """Dock widget for displaying AI processing log."""

    def __init__(self, parent=None):
        """Initialize the processing log dock widget."""
        super().__init__("AI Processing Log", parent)
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
        
        self.init_ui()

    def init_ui(self):
        """Initialize the UI components."""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        # Text edit for log messages
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Courier")
        self.log_text.setFontPointSize(9)
        layout.addWidget(self.log_text)

        # Clear button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.clear_button = QPushButton("Clear Log")
        self.clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)

        self.setWidget(widget)

    def log_message(self, message, level="INFO"):
        """Add a message to the log.
        
        :param message: Message to log
        :type message: str
        :param level: Log level (INFO, WARNING, ERROR, DEBUG)
        :type level: str
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format message with timestamp and level
        formatted_message = f"[{timestamp}] [{level}] {message}"
        
        # Append to text edit
        self.log_text.append(formatted_message)
        
        # Also log to QGIS message log
        if level == "ERROR":
            QgsMessageLog.logMessage(message, "AI Classification", Qgis.Critical)
        elif level == "WARNING":
            QgsMessageLog.logMessage(message, "AI Classification", Qgis.Warning)
        else:
            QgsMessageLog.logMessage(message, "AI Classification", Qgis.Info)
        
        # Auto-scroll to bottom
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def log_backend(self, backend_name):
        """Log which backend is being used."""
        self.log_message(f"Using classification backend: {backend_name}", "INFO")

    def log_bands(self, bands):
        """Log detected bands.
        
        :param bands: Dictionary of band mappings
        :type bands: dict
        """
        band_info = ", ".join([f"{k}: {v}" for k, v in bands.items()])
        self.log_message(f"Detected bands: {band_info}", "INFO")

    def log_roi(self, roi_type, roi_info):
        """Log ROI information.
        
        :param roi_type: Type of ROI (full, rectangle, polygon, mask)
        :type roi_type: str
        :param roi_info: Additional ROI information
        :type roi_info: str
        """
        self.log_message(f"ROI Type: {roi_type} - {roi_info}", "INFO")

    def log_progress(self, step, total, message=""):
        """Log classification progress.
        
        :param step: Current step
        :type step: int
        :param total: Total steps
        :type total: int
        :param message: Additional message
        :type message: str
        """
        progress_msg = f"Progress: {step}/{total}"
        if message:
            progress_msg += f" - {message}"
        self.log_message(progress_msg, "INFO")

    def log_statistics(self, stats):
        """Log cluster statistics.
        
        :param stats: Statistics dictionary
        :type stats: dict
        """
        self.log_message("Cluster Statistics:", "INFO")
        for key, value in stats.items():
            self.log_message(f"  {key}: {value}", "DEBUG")

    def log_llm_prompt(self, prompt):
        """Log LLM prompt.
        
        :param prompt: Prompt text
        :type prompt: str
        """
        self.log_message("LLM Prompt:", "INFO")
        self.log_message(prompt, "DEBUG")

    def log_llm_response(self, response):
        """Log LLM response.
        
        :param response: Response text or JSON
        :type response: str
        """
        self.log_message("LLM Response:", "INFO")
        self.log_message(str(response), "DEBUG")

    def log_styling(self, styling_info):
        """Log styling information.
        
        :param styling_info: Styling information
        :type styling_info: str
        """
        self.log_message(f"Styling applied: {styling_info}", "INFO")

    def log_error(self, error, traceback=None):
        """Log an error with optional traceback.
        
        :param error: Error message
        :type error: str
        :param traceback: Optional traceback string
        :type traceback: str
        """
        self.log_message(f"ERROR: {error}", "ERROR")
        if traceback:
            self.log_message(f"Traceback:\n{traceback}", "ERROR")

    def clear_log(self):
        """Clear the log."""
        self.log_text.clear()
        self.log_message("Log cleared", "INFO")

