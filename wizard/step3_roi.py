"""
Wizard Step 3: ROI Selection - Fixed with working MapTools
"""

from qgis.PyQt.QtWidgets import (
    QWizardPage, QVBoxLayout, QHBoxLayout, QRadioButton, QButtonGroup,
    QPushButton, QLabel, QComboBox, QTextEdit
)
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsRasterLayer, QgsRectangle,
    QgsMessageLog, Qgis, QgsGeometry, QgsPointXY, QgsWkbTypes
)
from qgis.gui import QgsMapTool, QgsRubberBand, QgsMapToolExtent, QgsMapToolCapture
from qgis.PyQt.QtGui import QColor


class Step3ROIPage(QWizardPage):
    """Wizard page for ROI selection with working MapTools."""

    def __init__(self, parent=None):
        """Initialize the ROI selection page."""
        super().__init__(parent)
        self.setTitle("ROI Selection")
        self.setSubTitle("Select the region of interest for classification")
        
        self.roi_type = None
        self.roi_geometry = None
        self.roi_layer = None
        self.map_tool = None
        self.rubber_band = None
        self.original_map_tool = None
        
        self.init_ui()

    def initializePage(self):
        """Initialize page when shown."""
        self.refresh_mask_layers()
        # Store original map tool
        wizard = self.wizard()
        if hasattr(wizard, 'iface'):
            self.original_map_tool = wizard.iface.mapCanvas().mapTool()

    def cleanupPage(self):
        """Clean up when leaving page."""
        self.restore_map_tool()

    def init_ui(self):
        """Initialize the UI components."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ROI type selection
        self.roi_group = QButtonGroup(self)
        
        # Full canvas option
        self.full_radio = QRadioButton("Full Canvas")
        self.roi_group.addButton(self.full_radio, 0)
        layout.addWidget(self.full_radio)

        # Rectangle option
        self.rect_radio = QRadioButton("Rectangle (draw on map)")
        self.roi_group.addButton(self.rect_radio, 1)
        layout.addWidget(self.rect_radio)

        # Polygon option
        self.polygon_radio = QRadioButton("Polygon (draw on map)")
        self.roi_group.addButton(self.polygon_radio, 2)
        layout.addWidget(self.polygon_radio)

        # Mask layer option
        self.mask_radio = QRadioButton("Mask Layer")
        self.roi_group.addButton(self.mask_radio, 3)
        layout.addWidget(self.mask_radio)

        # Mask layer selection
        mask_layout = QHBoxLayout()
        mask_layout.addWidget(QLabel("Mask Layer:"))
        self.mask_combo = QComboBox()
        self.mask_combo.setEnabled(False)
        self.mask_combo.currentIndexChanged.connect(self.on_mask_layer_changed)
        mask_layout.addWidget(self.mask_combo)
        self.refresh_mask_button = QPushButton("Refresh")
        self.refresh_mask_button.setEnabled(False)
        self.refresh_mask_button.clicked.connect(self.refresh_mask_layers)
        mask_layout.addWidget(self.refresh_mask_button)
        layout.addLayout(mask_layout)

        # Draw buttons
        button_layout = QHBoxLayout()
        self.draw_rect_button = QPushButton("Draw Rectangle")
        self.draw_rect_button.setEnabled(False)
        self.draw_rect_button.clicked.connect(self.start_draw_rectangle)
        button_layout.addWidget(self.draw_rect_button)

        self.draw_polygon_button = QPushButton("Draw Polygon")
        self.draw_polygon_button.setEnabled(False)
        self.draw_polygon_button.clicked.connect(self.start_draw_polygon)
        button_layout.addWidget(self.draw_polygon_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.setEnabled(False)
        self.clear_button.clicked.connect(self.clear_drawing)
        button_layout.addWidget(self.clear_button)

        layout.addLayout(button_layout)

        # Status text with WKT preview
        status_label = QLabel("Status:")
        layout.addWidget(status_label)
        
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        self.status_text.setMaximumHeight(120)
        self.status_text.setPlainText("Please select a ROI type.")
        layout.addWidget(self.status_text)

        # Connect signals
        self.roi_group.buttonClicked.connect(self.on_roi_type_changed)

    def on_roi_type_changed(self, button):
        """Handle ROI type change."""
        self.restore_map_tool()
        
        if button == self.full_radio:
            self.roi_type = "full"
            self.draw_rect_button.setEnabled(False)
            self.draw_polygon_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            self.mask_combo.setEnabled(False)
            self.refresh_mask_button.setEnabled(False)
            
            # Get full canvas extent
            wizard = self.wizard()
            if hasattr(wizard, 'iface'):
                active_layer = wizard.iface.activeLayer()
                if isinstance(active_layer, QgsRasterLayer):
                    self.roi_geometry = active_layer.extent()
                    self.status_text.setPlainText(
                        f"Full Canvas: {active_layer.name()}\n"
                        f"Extent: {self.roi_geometry.xMinimum():.2f}, {self.roi_geometry.yMinimum():.2f} to "
                        f"{self.roi_geometry.xMaximum():.2f}, {self.roi_geometry.yMaximum():.2f}"
                    )
                else:
                    self.status_text.setPlainText("Will use full canvas extent of active raster layer")
            else:
                self.status_text.setPlainText("Will use full canvas extent")
                
        elif button == self.rect_radio:
            self.roi_type = "rectangle"
            self.draw_rect_button.setEnabled(True)
            self.draw_polygon_button.setEnabled(False)
            self.clear_button.setEnabled(True)
            self.mask_combo.setEnabled(False)
            self.refresh_mask_button.setEnabled(False)
            self.status_text.setPlainText("Click 'Draw Rectangle' and draw on the map canvas")
            
        elif button == self.polygon_radio:
            self.roi_type = "polygon"
            self.draw_rect_button.setEnabled(False)
            self.draw_polygon_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            self.mask_combo.setEnabled(False)
            self.refresh_mask_button.setEnabled(False)
            self.status_text.setPlainText("Click 'Draw Polygon' and draw on the map canvas (right-click to finish)")
            
        elif button == self.mask_radio:
            self.roi_type = "mask"
            self.draw_rect_button.setEnabled(False)
            self.draw_polygon_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            self.mask_combo.setEnabled(True)
            self.refresh_mask_button.setEnabled(True)
            self.status_text.setPlainText("Select a mask layer from the dropdown")
        
        self.completeChanged.emit()

    def refresh_mask_layers(self):
        """Refresh available mask layers."""
        self.mask_combo.clear()
        self.mask_combo.addItem("(Select layer)")
        
        project = QgsProject.instance()
        for layer in project.mapLayers().values():
            if isinstance(layer, (QgsVectorLayer, QgsRasterLayer)):
                self.mask_combo.addItem(layer.name(), layer.id())

    def on_mask_layer_changed(self):
        """Handle mask layer selection."""
        if self.mask_combo.currentIndex() > 0:
            layer_id = self.mask_combo.currentData()
            self.roi_layer = QgsProject.instance().mapLayer(layer_id)
            if self.roi_layer:
                self.status_text.setPlainText(f"Selected mask layer: {self.roi_layer.name()}")
        else:
            self.roi_layer = None
        self.completeChanged.emit()

    def start_draw_rectangle(self):
        """Start drawing rectangle on map."""
        wizard = self.wizard()
        if not hasattr(wizard, 'iface'):
            return
        
        canvas = wizard.iface.mapCanvas()
        
        # Create custom map tool that works in modal dialog
        self.map_tool = RectangleMapTool(canvas, self)
        self.map_tool.extentDrawn.connect(self.on_rectangle_drawn)
        canvas.setMapTool(self.map_tool)
        
        self.status_text.setPlainText("Draw a rectangle on the map canvas (click and drag)")

    def start_draw_polygon(self):
        """Start drawing polygon on map."""
        wizard = self.wizard()
        if not hasattr(wizard, 'iface'):
            return
        
        canvas = wizard.iface.mapCanvas()
        
        # Create custom map tool
        self.map_tool = PolygonMapTool(canvas, self)
        self.map_tool.geometryCreated.connect(self.on_polygon_drawn)
        canvas.setMapTool(self.map_tool)
        
        self.status_text.setPlainText("Draw a polygon on the map canvas (left-click to add points, right-click to finish)")

    def on_rectangle_drawn(self, extent):
        """Handle rectangle drawn."""
        self.roi_geometry = extent
        wkt = extent.asWktPolygon()
        self.status_text.setPlainText(
            f"Rectangle drawn:\n"
            f"Extent: {extent.xMinimum():.2f}, {extent.yMinimum():.2f} to "
            f"{extent.xMaximum():.2f}, {extent.yMaximum():.2f}\n"
            f"WKT: {wkt[:100]}..."
        )
        self.restore_map_tool()
        self.completeChanged.emit()

    def on_polygon_drawn(self, geometry):
        """Handle polygon drawn."""
        self.roi_geometry = geometry
        wkt = geometry.asWkt()
        self.status_text.setPlainText(
            f"Polygon drawn with {geometry.numPoints()} vertices\n"
            f"WKT: {wkt[:200]}..."
        )
        self.restore_map_tool()
        self.completeChanged.emit()

    def clear_drawing(self):
        """Clear drawn geometry."""
        self.roi_geometry = None
        if self.rubber_band:
            self.rubber_band.reset()
        self.status_text.setPlainText("Drawing cleared")
        self.restore_map_tool()
        self.completeChanged.emit()

    def restore_map_tool(self):
        """Restore original map tool."""
        if self.map_tool:
            wizard = self.wizard()
            if hasattr(wizard, 'iface'):
                if self.original_map_tool:
                    wizard.iface.mapCanvas().setMapTool(self.original_map_tool)
                else:
                    wizard.iface.mapCanvas().unsetMapTool(self.map_tool)
            self.map_tool = None

    def get_roi(self):
        """Get ROI information."""
        return {
            "type": self.roi_type,
            "geometry": self.roi_geometry,
            "layer": self.roi_layer
        }

    def isComplete(self):
        """Check if the page is complete."""
        if not self.roi_type:
            return False
        
        if self.roi_type == "full":
            return True
        elif self.roi_type == "mask":
            return self.roi_layer is not None
        else:
            return self.roi_geometry is not None


class RectangleMapTool(QgsMapToolExtent):
    """Map tool for drawing rectangles that works in modal dialogs."""
    
    extentDrawn = pyqtSignal(object)
    
    def __init__(self, canvas, parent_page):
        """Initialize the rectangle map tool."""
        super().__init__(canvas)
        self.parent_page = parent_page
        self.rubber_band = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 100))
        self.rubber_band.setWidth(2)
    
    def canvasPressEvent(self, event):
        """Handle canvas press event."""
        super().canvasPressEvent(event)
    
    def canvasMoveEvent(self, event):
        """Handle canvas move event."""
        super().canvasMoveEvent(event)
    
    def canvasReleaseEvent(self, event):
        """Handle canvas release event."""
        super().canvasReleaseEvent(event)
        if self.isActive():
            extent = self.extent()
            if extent and not extent.isEmpty():
                self.extentDrawn.emit(extent)
                self.deactivate()


class PolygonMapTool(QgsMapToolCapture):
    """Map tool for drawing polygons that works in modal dialogs."""
    
    geometryCreated = pyqtSignal(object)
    
    def __init__(self, canvas, parent_page):
        """Initialize the polygon map tool."""
        super().__init__(canvas, QgsMapToolCapture.CaptureMode.CapturePolygon)
        self.parent_page = parent_page
        self.rubber_band = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 100))
        self.rubber_band.setWidth(2)
        self.points = []
    
    def canvasPressEvent(self, event):
        """Handle canvas press event."""
        if event.button() == Qt.LeftButton:
            point = self.toMapCoordinates(event.pos())
            self.points.append(point)
            self.rubber_band.addPoint(point)
        elif event.button() == Qt.RightButton and len(self.points) >= 3:
            # Finish polygon
            geom = QgsGeometry.fromPolygonXY([[QgsPointXY(p) for p in self.points]])
            self.geometryCreated.emit(geom)
            self.rubber_band.reset()
            self.points = []
            self.deactivate()
    
    def canvasMoveEvent(self, event):
        """Handle canvas move event."""
        if self.points:
            point = self.toMapCoordinates(event.pos())
            if self.rubber_band.numberOfVertices() > len(self.points):
                self.rubber_band.removeLastPoint()
            self.rubber_band.addPoint(point)
