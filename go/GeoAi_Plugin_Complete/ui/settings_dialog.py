"""
Settings Dialog for AI Unsupervised Classification Plugin
"""

from qgis.PyQt.QtCore import QSettings, Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QGroupBox, QFormLayout, QMessageBox
)
from qgis.core import QgsMessageLog, Qgis
import os


class SettingsDialog(QDialog):
    """Settings dialog for LLM configuration."""

    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.setWindowTitle("AI Unsupervised Classification - Settings")
        self.setMinimumWidth(500)
        self.settings = QSettings()
        
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # LLM Provider Group
        provider_group = QGroupBox("LLM Provider Configuration")
        provider_layout = QFormLayout()
        provider_group.setLayout(provider_layout)

        # Provider selection
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Ollama", "OpenRouter", "Gemini"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addRow("Provider:", self.provider_combo)

        # Base URL (for Ollama)
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("http://localhost:11434")
        provider_layout.addRow("Base URL:", self.base_url_edit)

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter your API key")
        provider_layout.addRow("API Key:", self.api_key_edit)

        # Model name
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g., llama2, gpt-4, claude-3, gemini-pro")
        provider_layout.addRow("Model:", self.model_edit)

        layout.addWidget(provider_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)

        button_layout.addStretch()

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

        # Update UI based on provider
        self.on_provider_changed()

    def on_provider_changed(self):
        """Update UI when provider changes."""
        provider = self.provider_combo.currentText()
        
        if provider == "Ollama":
            self.base_url_edit.setEnabled(True)
            self.base_url_edit.setPlaceholderText("http://localhost:11434")
            self.api_key_edit.setPlaceholderText("Optional for local Ollama")
        elif provider == "OpenRouter":
            self.base_url_edit.setEnabled(False)
            self.base_url_edit.setText("https://openrouter.ai/api/v1")
            self.api_key_edit.setPlaceholderText("Enter your OpenRouter API key")
        elif provider == "Gemini":
            self.base_url_edit.setEnabled(False)
            self.base_url_edit.setText("https://generativelanguage.googleapis.com/v1beta")
            self.api_key_edit.setPlaceholderText("Enter your Google API key")

    def load_settings(self):
        """Load settings from QSettings."""
        self.provider_combo.setCurrentText(
            self.settings.value("ai_classification/provider", "Ollama", type=str)
        )
        self.base_url_edit.setText(
            self.settings.value("ai_classification/base_url", "http://localhost:11434", type=str)
        )
        self.api_key_edit.setText(
            self.settings.value("ai_classification/api_key", "", type=str)
        )
        self.model_edit.setText(
            self.settings.value("ai_classification/model", "llama2", type=str)
        )
        self.on_provider_changed()

    def save_settings(self):
        """Save settings to QSettings."""
        self.settings.setValue("ai_classification/provider", self.provider_combo.currentText())
        self.settings.setValue("ai_classification/base_url", self.base_url_edit.text())
        self.settings.setValue("ai_classification/api_key", self.api_key_edit.text())
        self.settings.setValue("ai_classification/model", self.model_edit.text())
        
        self.settings_changed.emit()
        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.accept()

    def test_connection(self):
        """Test the LLM connection."""
        from ..logic.llm_client import LLMClient
        
        provider = self.provider_combo.currentText()
        base_url = self.base_url_edit.text()
        api_key = self.api_key_edit.text()
        model = self.model_edit.text()

        if not model:
            QMessageBox.warning(self, "Test Connection", "Please enter a model name.")
            return

        if provider != "Ollama" and not api_key:
            QMessageBox.warning(self, "Test Connection", "Please enter an API key.")
            return

        try:
            client = LLMClient(provider, base_url, api_key, model)
            # Simple test prompt
            response = client.generate("Test connection. Reply with 'OK' if you can read this.")
            
            if response:
                QMessageBox.information(
                    self,
                    "Test Connection",
                    f"Connection successful!\n\nResponse: {response[:100]}..."
                )
            else:
                QMessageBox.warning(self, "Test Connection", "Connection failed: No response received.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Test Connection",
                f"Connection failed:\n{str(e)}"
            )

    def get_settings(self):
        """Get current settings as a dictionary."""
        return {
            "provider": self.provider_combo.currentText(),
            "base_url": self.base_url_edit.text(),
            "api_key": self.api_key_edit.text(),
            "model": self.model_edit.text()
        }

