"""
QGIS Styling Functions for Classification Results
"""

from qgis.core import (
    QgsRasterLayer, QgsColorRampShader, QgsRasterShader, QgsSingleBandPseudoColorRenderer,
    QgsGradientColorRamp, QgsProject, QgsMessageLog, Qgis
)
from qgis.PyQt.QtGui import QColor
import json


def apply_styling(layer, llm_result, log_callback=None):
    """
    Apply styling to classification layer based on LLM result.
    
    :param layer: Raster layer to style
    :type layer: QgsRasterLayer
    :param llm_result: LLM interpretation result with cluster information
    :type llm_result: dict
    :param log_callback: Optional logging callback
    :type log_callback: callable
    """
    if not layer or not llm_result:
        if log_callback:
            log_callback("Cannot apply styling: missing layer or LLM result", "WARNING")
        return
    
    try:
        if log_callback:
            log_callback("Applying AI-generated styling...", "INFO")
        
        # Extract cluster information from LLM result
        clusters = llm_result.get('clusters', [])
        
        if not clusters:
            if log_callback:
                log_callback("No cluster information in LLM result", "WARNING")
            apply_default_styling(layer, log_callback)
            return
        
        # Create color ramp shader
        shader = QgsRasterShader()
        color_ramp = QgsColorRampShader()
        color_ramp.setColorRampType(QgsColorRampShader.Discrete)
        
        # Build color map from clusters
        color_map_items = []
        for cluster in clusters:
            cluster_id = cluster.get('id', 0)
            color_hex = cluster.get('color', '#808080')
            label = cluster.get('label', f'Cluster {cluster_id}')
            
            # Convert hex color to QColor
            color = QColor(color_hex)
            
            # Create color map item
            color_map_items.append(
                QgsColorRampShader.ColorRampItem(
                    cluster_id,
                    color,
                    label
                )
            )
            
            if log_callback:
                log_callback(f"Cluster {cluster_id}: {label} ({color_hex})", "DEBUG")
        
        color_ramp.setColorRampItemList(color_map_items)
        shader.setRasterShaderFunction(color_ramp)
        
        # Create renderer
        renderer = QgsSingleBandPseudoColorRenderer(
            layer.dataProvider(),
            1,  # Band number
            shader
        )
        
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        
        # Rename clusters in layer metadata if possible
        rename_clusters(layer, clusters, log_callback)
        
        if log_callback:
            log_callback("Styling applied successfully", "INFO")
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error applying styling: {str(e)}", "ERROR")
        # Fallback to default styling
        apply_default_styling(layer, log_callback)


def apply_default_styling(layer, log_callback=None):
    """
    Apply default styling when LLM result is not available.
    
    :param layer: Raster layer to style
    :type layer: QgsRasterLayer
    :param log_callback: Optional logging callback
    :type log_callback: callable
    """
    if log_callback:
        log_callback("Applying default styling...", "INFO")
    
    try:
        # Create a simple color ramp
        shader = QgsRasterShader()
        color_ramp = QgsColorRampShader()
        color_ramp.setColorRampType(QgsColorRampShader.Discrete)
        
        # Default colors for up to 10 clusters
        default_colors = [
            QColor(0, 0, 255),    # Blue
            QColor(0, 255, 0),    # Green
            QColor(255, 0, 0),    # Red
            QColor(255, 255, 0),  # Yellow
            QColor(255, 0, 255),  # Magenta
            QColor(0, 255, 255),  # Cyan
            QColor(128, 0, 0),    # Dark Red
            QColor(0, 128, 0),    # Dark Green
            QColor(0, 0, 128),    # Dark Blue
            QColor(128, 128, 128) # Gray
        ]
        
        color_map_items = []
        for i, color in enumerate(default_colors):
            color_map_items.append(
                QgsColorRampShader.ColorRampItem(
                    i,
                    color,
                    f'Cluster {i}'
                )
            )
        
        color_ramp.setColorRampItemList(color_map_items)
        shader.setRasterShaderFunction(color_ramp)
        
        renderer = QgsSingleBandPseudoColorRenderer(
            layer.dataProvider(),
            1,
            shader
        )
        
        layer.setRenderer(renderer)
        layer.triggerRepaint()
        
        if log_callback:
            log_callback("Default styling applied", "INFO")
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error applying default styling: {str(e)}", "ERROR")


def rename_clusters(layer, clusters, log_callback=None):
    """
    Rename clusters in layer metadata.
    
    :param layer: Raster layer
    :type layer: QgsRasterLayer
    :param clusters: List of cluster dictionaries
    :type clusters: list
    :param log_callback: Optional logging callback
    :type log_callback: callable
    """
    try:
        # Store cluster labels in layer custom properties
        cluster_labels = {}
        for cluster in clusters:
            cluster_id = cluster.get('id', 0)
            label = cluster.get('label', f'Cluster {cluster_id}')
            cluster_labels[str(cluster_id)] = label
        
        layer.setCustomProperty('classification_clusters', json.dumps(cluster_labels))
        
        if log_callback:
            log_callback(f"Stored cluster labels: {cluster_labels}", "DEBUG")
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error renaming clusters: {str(e)}", "WARNING")


def export_qml(layer, qml_path, llm_result, log_callback=None):
    """
    Export layer styling to QML file.
    
    :param layer: Raster layer
    :type layer: QgsRasterLayer
    :param qml_path: Path to save QML file
    :type qml_path: str
    :param llm_result: LLM interpretation result
    :type llm_result: dict
    :param log_callback: Optional logging callback
    :type log_callback: callable
    """
    try:
        if log_callback:
            log_callback(f"Exporting QML to {qml_path}...", "INFO")
        
        # Use QGIS built-in QML export
        # Note: This is a simplified version - full QML export would require
        # more detailed XML generation
        
        # For now, save cluster information as metadata
        if llm_result:
            with open(qml_path, 'w') as f:
                f.write('<?xml version="1.0" encoding="utf-8"?>\n')
                f.write('<qgis version="3.0.0">\n')
                f.write('  <pipe>\n')
                f.write('    <rasterrenderer>\n')
                
                # Write color map
                clusters = llm_result.get('clusters', [])
                if clusters:
                    f.write('      <rastershader>\n')
                    f.write('        <colorrampshader>\n')
                    
                    for cluster in clusters:
                        cluster_id = cluster.get('id', 0)
                        color_hex = cluster.get('color', '#808080')
                        label = cluster.get('label', f'Cluster {cluster_id}')
                        
                        f.write(f'          <item value="{cluster_id}" label="{label}" color="{color_hex}"/>\n')
                    
                    f.write('        </colorrampshader>\n')
                    f.write('      </rastershader>\n')
                
                f.write('    </rasterrenderer>\n')
                f.write('  </pipe>\n')
                f.write('</qgis>\n')
        
        if log_callback:
            log_callback(f"QML exported successfully", "INFO")
        
    except Exception as e:
        if log_callback:
            log_callback(f"Error exporting QML: {str(e)}", "ERROR")
        raise

