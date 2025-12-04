"""
Classification Wizard - Main wizard class orchestrating all 6 steps
"""

from qgis.PyQt.QtWidgets import QWizard, QWizardPage
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.core import QgsMessageLog, Qgis, QgsProject
from qgis import processing

# Import wizard steps
from .step1_algorithm import Step1AlgorithmPage
from .step2_parameters import Step2ParametersPage
from .step3_roi import Step3ROIPage
from .step4_bands import Step4BandsPage
from .step5_llm import Step5LLMPage
from .step6_output import Step6OutputPage

# Import classification and LLM modules
from ..logic.classify_python_kmeans import classify_python_kmeans
from ..logic.classify_saga import classify_saga
from ..logic.classify_otb import classify_otb
from ..logic.classify_grass import classify_grass
from ..logic.llm_prompt import build_classification_prompt
from ..logic.llm_client import LLMClient
from ..logic.qgis_styling import apply_styling, export_qml


class ClassificationWorker(QThread):
    """Worker thread for classification processing."""
    
    progress = pyqtSignal(int, int, str)  # step, total, message
    finished = pyqtSignal(bool, str)  # success, message
    log_message = pyqtSignal(str, str)  # message, level

    def __init__(self, config, processing_log=None):
        """Initialize the worker.
        
        :param config: Configuration dictionary with all wizard settings
        :type config: dict
        :param processing_log: Processing log dock widget
        :type processing_log: ProcessingLogDockWidget
        """
        super().__init__()
        self.config = config
        self.processing_log = processing_log

    def run(self):
        """Run the classification process."""
        try:
            self.log("Starting classification process...", "INFO")
            
            # Step 1: Prepare data
            self.progress.emit(1, 6, "Preparing data...")
            self.log(f"Algorithm: {self.config['algorithm']}", "INFO")
            self.log(f"Bands: {self.config['band_mapping']}", "INFO")
            self.log(f"ROI: {self.config['roi']}", "INFO")
            
            # Step 2: Run classification
            self.progress.emit(2, 6, "Running classification...")
            classification_result = self.run_classification()
            
            if not classification_result:
                self.finished.emit(False, "Classification failed")
                return
            
            # Add algorithm info to result
            classification_result['algorithm'] = self.config['algorithm']
            
            # Statistics and LLM are now handled in the classification backend
            # Step 3: Apply styling if needed
            self.progress.emit(3, 4, "Applying styling...")
            llm_result = classification_result.get('llm_result')
            if llm_result and classification_result.get('layer'):
                from ..logic.qgis_styling import apply_styling
                apply_styling(classification_result['layer'], llm_result, self.log)
            
            # Step 4: Add to map if requested
            self.progress.emit(4, 4, "Finalizing...")
            if self.config['output_options'].get('add_to_map', True):
                layer = classification_result.get('layer')
                if layer:
                    QgsProject.instance().addMapLayer(layer)
                    self.log("Added classification layer to map", "INFO")
            
            self.finished.emit(True, "Classification completed successfully!")
            
        except Exception as e:
            import traceback
            error_msg = str(e)
            traceback_str = traceback.format_exc()
            self.log(f"ERROR: {error_msg}", "ERROR")
            self.log(traceback_str, "ERROR")
            self.finished.emit(False, error_msg)

    def run_classification(self):
        """Run the classification algorithm."""
        algorithm = self.config['algorithm']
        self.log(f"Using backend: {algorithm}", "INFO")
        
        # Get output directory
        output_dir = self.config['output_options'].get('output_dir', None)
        if not output_dir:
            import tempfile
            output_dir = tempfile.mkdtemp(prefix="ai_classification_")
            self.log(f"Using temporary output directory: {output_dir}", "INFO")
        
        # Merge parameters with output options
        parameters = self.config['parameters'].copy()
        parameters['enable_postprocessing'] = self.config['output_options'].get('enable_postprocessing', False)
        parameters['min_area_pixels'] = self.config['output_options'].get('min_area_pixels', 100)
        parameters['enable_llm_interpretation'] = self.config['output_options'].get('enable_llm', True)
        parameters['llm_config'] = self.config.get('llm_config', {})
        
        if algorithm == "python":
            return classify_python_kmeans(
                self.config['band_mapping']['layer'],
                self.config['band_mapping']['bands'],
                parameters,
                self.config['roi'],
                output_dir,
                self.log
            )
        elif algorithm == "saga":
            # SAGA fallback to Python for now
            self.log("SAGA not fully implemented, using Python fallback", "WARNING")
            return classify_python_kmeans(
                self.config['band_mapping']['layer'],
                self.config['band_mapping']['bands'],
                parameters,
                self.config['roi'],
                output_dir,
                self.log
            )
        elif algorithm == "otb":
            # OTB fallback to Python for now
            self.log("OTB not fully implemented, using Python fallback", "WARNING")
            return classify_python_kmeans(
                self.config['band_mapping']['layer'],
                self.config['band_mapping']['bands'],
                parameters,
                self.config['roi'],
                output_dir,
                self.log
            )
        elif algorithm == "grass":
            # GRASS fallback to Python for now
            self.log("GRASS not fully implemented, using Python fallback", "WARNING")
            return classify_python_kmeans(
                self.config['band_mapping']['layer'],
                self.config['band_mapping']['bands'],
                parameters,
                self.config['roi'],
                output_dir,
                self.log
            )
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")


    def log(self, message, level="INFO"):
        """Log a message."""
        if self.processing_log:
            self.processing_log.log_message(message, level)
        self.log_message.emit(message, level)


    def log_llm_prompt(self, prompt):
        """Log LLM prompt."""
        if self.processing_log:
            self.processing_log.log_llm_prompt(prompt)

    def log_llm_response(self, response):
        """Log LLM response."""
        if self.processing_log:
            self.processing_log.log_llm_response(response)


class ClassificationWizard(QWizard):
    """Main classification wizard."""

    def __init__(self, iface, processing_log=None, parent=None):
        """Initialize the wizard.
        
        :param iface: QGIS interface
        :type iface: QgsInterface
        :param processing_log: Processing log dock widget
        :type processing_log: ProcessingLogDockWidget
        :param parent: Parent widget
        :type parent: QWidget
        """
        super().__init__(parent)
        self.iface = iface
        self.processing_log = processing_log
        self.setWindowTitle("AI Unsupervised Classification Wizard")
        self.setWizardStyle(QWizard.ModernStyle)
        
        # Initialize pages
        self.init_pages()
        
        # Worker thread
        self.worker = None

    def init_pages(self):
        """Initialize wizard pages."""
        # Step 1: Algorithm selection
        self.step1 = Step1AlgorithmPage(self)
        self.addPage(self.step1)
        
        # Step 2: Parameters
        self.step2 = Step2ParametersPage(self)
        self.addPage(self.step2)
        
        # Step 3: ROI
        self.step3 = Step3ROIPage(self)
        self.addPage(self.step3)
        
        # Step 4: Bands
        self.step4 = Step4BandsPage(self)
        self.addPage(self.step4)
        
        # Step 5: LLM Config
        self.step5 = Step5LLMPage(self)
        self.addPage(self.step5)
        
        # Step 6: Output
        self.step6 = Step6OutputPage(self)
        self.addPage(self.step6)

    def get_algorithm(self):
        """Get selected algorithm from step 1."""
        return self.step1.get_algorithm()

    def accept(self):
        """Handle wizard completion."""
        # Collect all configuration
        config = {
            "algorithm": self.step1.get_algorithm(),
            "parameters": self.step2.get_parameters(),
            "roi": self.step3.get_roi(),
            "band_mapping": self.step4.get_band_mapping(),
            "llm_config": self.step5.get_llm_config(),
            "output_options": self.step6.get_output_options()
        }
        
        # Validate configuration
        if not self.validate_config(config):
            return
        
        # Start classification worker
        self.worker = ClassificationWorker(config, self.processing_log)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.log_message.connect(self.on_log_message)
        
        if self.processing_log:
            self.processing_log.setVisible(True)
            self.processing_log.log_message("Starting classification...", "INFO")
        
        self.worker.start()
        
        # Show progress dialog or keep wizard open
        # For now, just accept and let worker run
        super().accept()

    def validate_config(self, config):
        """Validate configuration."""
        # Basic validation
        if not config.get('algorithm'):
            return False
        if not config.get('band_mapping', {}).get('layer'):
            return False
        # Output directory is optional (will use temp if not set)
        return True

    def on_progress(self, step, total, message):
        """Handle progress update."""
        if self.processing_log:
            self.processing_log.log_progress(step, total, message)

    def on_finished(self, success, message):
        """Handle worker completion."""
        if self.processing_log:
            if success:
                self.processing_log.log_message(message, "INFO")
            else:
                self.processing_log.log_message(message, "ERROR")
        
        if success:
            self.iface.messageBar().pushSuccess("Classification", message)
        else:
            self.iface.messageBar().pushCritical("Classification Error", message)

    def on_log_message(self, message, level):
        """Handle log message."""
        if self.processing_log:
            self.processing_log.log_message(message, level)

