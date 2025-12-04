"""
AI Unsupervised Classification Plugin for QGIS
"""

def classFactory(iface):
    """Load AI Unsupervised Classification plugin class.
    
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .ai_plugin import AIUnsupervisedClassificationPlugin
    return AIUnsupervisedClassificationPlugin(iface)

