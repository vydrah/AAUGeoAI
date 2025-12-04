"""
Wizard Step 5: LLM Configuration Summary
"""

from qgis.PyQt.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QGroupBox, QFormLayout, QTextEdit, QCheckBox
)
from qgis.PyQt.QtCore import QSettings
from qgis.core import QgsMessageLog, Qgis


class Step5LLMPage(QWizardPage):
    """Wizard page for LLM configuration summary."""

    def __init__(self, parent=None):
        """Initialize the LLM configuration page."""
        super().__init__(parent)
        self.setTitle("LLM Configuration")
        self.setSubTitle("Review and configure AI interpretation settings")
        
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Enable AI interpretation checkbox
        self.enable_ai_checkbox = QCheckBox("Enable AI Interpretation")
        self.enable_ai_checkbox.setChecked(True)
        self.enable_ai_checkbox.toggled.connect(self.on_ai_toggled)
        layout.addWidget(self.enable_ai_checkbox)

        # LLM configuration group
        self.llm_group = QGroupBox("LLM Settings")
        self.llm_layout = QFormLayout()
        self.llm_group.setLayout(self.llm_layout)
        layout.addWidget(self.llm_group)

        # Provider
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["Ollama", "OpenRouter", "Gemini"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        self.llm_layout.addRow("Provider:", self.provider_combo)

        # Base URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("http://localhost:11434")
        self.llm_layout.addRow("Base URL:", self.base_url_edit)

        # API Key
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter API key")
        self.llm_layout.addRow("API Key:", self.api_key_edit)

        # Model
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g., llama2, gpt-4, claude-3")
        self.llm_layout.addRow("Model:", self.model_edit)

        # Load from settings button
        load_button = QPushButton("Load from Saved Settings")
        load_button.clicked.connect(self.load_settings)
        self.llm_layout.addRow("", load_button)

        # Configuration summary
        summary_label = QLabel("Configuration Summary:")
        layout.addWidget(summary_label)

        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMaximumHeight(150)
        layout.addWidget(self.summary_text)

        # Update summary when settings change
        self.provider_combo.currentTextChanged.connect(self.update_summary)
        self.base_url_edit.textChanged.connect(self.update_summary)
        self.api_key_edit.textChanged.connect(self.update_summary)
        self.model_edit.textChanged.connect(self.update_summary)
        self.enable_ai_checkbox.toggled.connect(self.update_summary)

        self.update_summary()

    def load_settings(self):
        """Load settings from QSettings."""
        settings = QSettings()
        self.provider_combo.setCurrentText(
            settings.value("ai_classification/provider", "Ollama", type=str)
        )
        self.base_url_edit.setText(
            settings.value("ai_classification/base_url", "http://localhost:11434", type=str)
        )
        self.api_key_edit.setText(
            settings.value("ai_classification/api_key", "", type=str)
        )
        self.model_edit.setText(
            settings.value("ai_classification/model", "llama2", type=str)
        )
        self.on_provider_changed()
        self.update_summary()

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

    def on_ai_toggled(self, enabled):
        """Handle AI interpretation toggle."""
        self.llm_group.setEnabled(enabled)
        self.update_summary()

    def update_summary(self):
        """Update configuration summary."""
        if not self.enable_ai_checkbox.isChecked():
            self.summary_text.setPlainText(
                "AI Interpretation: DISABLED\n"
                "Classification will run without AI interpretation."
            )
            return

        provider = self.provider_combo.currentText()
        base_url = self.base_url_edit.text()
        model = self.model_edit.text()
        api_key = self.api_key_edit.text()

        summary = f"AI Interpretation: ENABLED\n"
        summary += f"Provider: {provider}\n"
        summary += f"Base URL: {base_url}\n"
        summary += f"Model: {model}\n"
        summary += f"API Key: {'***' if api_key else '(not set)'}\n"
        
        # Validation
        if not model:
            summary += "\n⚠ Warning: Model name is required"
        if provider != "Ollama" and not api_key:
            summary += "\n⚠ Warning: API key is required for this provider"

        self.summary_text.setPlainText(summary)

    def get_llm_config(self):
        """Get LLM configuration."""
        return {
            "enabled": self.enable_ai_checkbox.isChecked(),
            "provider": self.provider_combo.currentText(),
            "base_url": self.base_url_edit.text(),
            "api_key": self.api_key_edit.text(),
            "model": self.model_edit.text()
        }

    def isComplete(self):
        """Check if the page is complete."""
        if not self.enable_ai_checkbox.isChecked():
            return True  # AI disabled is valid
        
        # If AI enabled, check required fields
        if not self.model_edit.text():
            return False
        
        provider = self.provider_combo.currentText()
        if provider != "Ollama" and not self.api_key_edit.text():
            return False
        
        return True

