"""
AI Unsupervised Classification Plugin for QGIS
Main plugin file
"""

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.core import QgsApplication, QgsMessageLog, Qgis
import os
import sys

# Import plugin components
from .ui.settings_dialog import SettingsDialog
from .ui.processing_log_dock import ProcessingLogDockWidget
from .wizard.classification_wizard import ClassificationWizard


class AIUnsupervisedClassificationPlugin:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        
        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'AIUnsupervisedClassification_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&AI Unsupervised Classification')
        self.settings_dialog = None
        self.processing_log_dock = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('AIUnsupervisedClassification', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=False,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to False.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param whats_this: Optional text to show in the Whats this popup.
        :type whats_this: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Create plugin menu
        self.plugin_menu = QMenu(self.menu)
        self.iface.pluginMenu().addMenu(self.plugin_menu)

        # Add "Start Classification Wizard" action
        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr(u'Start Classification Wizard'),
            callback=self.run_wizard,
            parent=self.iface.mainWindow(),
            add_to_menu=True,
            add_to_toolbar=False)

        # Add "Settings" action
        self.add_action(
            icon_path,
            text=self.tr(u'Settings'),
            callback=self.show_settings,
            parent=self.iface.mainWindow(),
            add_to_menu=True,
            add_to_toolbar=False)

        # Add separator
        self.plugin_menu.addSeparator()

        # Initialize and add Processing Log dock widget
        self.processing_log_dock = ProcessingLogDockWidget()
        self.iface.addDockWidget(Qt.BottomDockWidgetArea, self.processing_log_dock)
        self.processing_log_dock.setVisible(False)

        # Add toggle action for dock widget
        self.add_action(
            icon_path,
            text=self.tr(u'Show AI Processing Log'),
            callback=self.toggle_processing_log,
            parent=self.iface.mainWindow(),
            add_to_menu=True,
            add_to_toolbar=False)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&AI Unsupervised Classification'),
                action)
            self.iface.removeToolBarIcon(action)

        # Remove dock widget
        if self.processing_log_dock:
            self.iface.removeDockWidget(self.processing_log_dock)
            self.processing_log_dock = None

    def run_wizard(self):
        """Run the classification wizard."""
        if self.processing_log_dock:
            self.processing_log_dock.log_message("Starting Classification Wizard...")
            self.processing_log_dock.setVisible(True)

        wizard = ClassificationWizard(self.iface, self.processing_log_dock)
        wizard.exec_()

    def show_settings(self):
        """Show the settings dialog."""
        if self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self.iface.mainWindow())
        
        self.settings_dialog.exec_()

    def toggle_processing_log(self):
        """Toggle visibility of the processing log dock widget."""
        if self.processing_log_dock:
            self.processing_log_dock.setVisible(not self.processing_log_dock.isVisible())

