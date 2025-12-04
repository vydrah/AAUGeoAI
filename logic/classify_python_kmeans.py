"""
Python K-means Classification Backend - Complete Rewrite
Includes resampling, feature calculation, clustering, postprocessing, and LLM interpretation
"""

import numpy as np
from qgis.core import (
    QgsRasterLayer, QgsRasterDataProvider, QgsRectangle, QgsCoordinateReferenceSystem,
    QgsRasterFileWriter, QgsProcessingFeedback, QgsMessageLog, Qgis, QgsProject
)
from qgis import processing
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from scipy import ndimage
from scipy.ndimage import label, find_objects
import os
import tempfile
import json


def classify_python_kmeans(raster_layer, band_mapping, parameters, roi, output_dir, log_callback=None):
    """
    Complete K-means classification pipeline with resampling, features, clustering, and interpretation.
    
    :param raster_layer: Input raster layer
    :type raster_layer: QgsRasterLayer
    :param band_mapping: Dictionary mapping band codes to band numbers
    :type band_mapping: dict
    :param parameters: Classification parameters
    :type parameters: dict
    :param roi: ROI configuration
    :type roi: dict
    :param output_dir: Output directory for all result files
    :type output_dir: str
    :param log_callback: Optional logging callback function
    :type log_callback: callable
    
    :returns: Dictionary with classification result
    :rtype: dict
    """
    if log_callback:
        log_callback("=== Starting Python K-means Classification Pipeline ===", "INFO")
    
    try:
        # Step A1: Resample all bands to same resolution (10m)
        if log_callback:
            log_callback("Step A1: Resampling bands to 10m resolution...", "INFO")
        
        resampled_bands = resample_bands(raster_layer, band_mapping, roi, log_callback)
        
        if not resampled_bands:
            raise ValueError("Failed to resample bands")
        
        # Step A2: Calculate features (NDVI, MNDWI, NDBI)
        if log_callback:
            log_callback("Step A2: Calculating features (NDVI, MNDWI, NDBI)...", "INFO")
        
        features = calculate_features(resampled_bands, log_callback)
        
        # Step A3: K-means clustering
        if log_callback:
            log_callback("Step A3: Running K-means clustering...", "INFO")
        
        num_clusters = parameters.get('num_clusters', 5)
        max_iterations = parameters.get('max_iterations', 100)
        random_seed = parameters.get('random_seed', 42)
        
        X, valid_mask, shape = prepare_features(features, log_callback)
        
        kmeans = KMeans(
            n_clusters=num_clusters,
            max_iter=max_iterations,
            random_state=random_seed,
            init='k-means++',
            n_init=10
        )
        
        labels = kmeans.fit_predict(X)
        
        # Reshape labels
        labels_reshaped = reshape_labels_safe(labels, shape, valid_mask, log_callback)
        
        # Save raw clusters
        clusters_raw_path = os.path.join(output_dir, "clusters_raw.tif")
        create_output_raster(resampled_bands['reference_layer'], labels_reshaped, clusters_raw_path, log_callback)
        
        # Calculate and save cluster sizes
        cluster_sizes = calculate_cluster_sizes(labels, num_clusters)
        clusters_raw_json = {
            "num_clusters": num_clusters,
            "cluster_sizes": cluster_sizes,
            "total_pixels": int(np.sum(valid_mask))
        }
        with open(os.path.join(output_dir, "clusters_raw.json"), 'w') as f:
            json.dump(clusters_raw_json, f, indent=2)
        
        if log_callback:
            log_callback(f"Raw clusters saved: {clusters_raw_path}", "INFO")
            log_callback(f"Cluster sizes: {cluster_sizes}", "INFO")
        
        # Step A4: Postprocessing (if enabled)
        enable_postprocessing = parameters.get('enable_postprocessing', False)
        labels_post = labels_reshaped.copy()
        
        if enable_postprocessing:
            if log_callback:
                log_callback("Step A4: Applying postprocessing...", "INFO")
            
            # Majority filter
            min_area_pixels = parameters.get('min_area_pixels', 100)
            labels_post = apply_majority_filter(labels_post, log_callback)
            labels_post = remove_small_clusters(labels_post, min_area_pixels, log_callback)
            
            clusters_post_path = os.path.join(output_dir, "clusters_post.tif")
            create_output_raster(resampled_bands['reference_layer'], labels_post, clusters_post_path, log_callback)
            
            if log_callback:
                log_callback(f"Postprocessed clusters saved: {clusters_post_path}", "INFO")
        else:
            labels_post = labels_reshaped
        
        # Step A5: Calculate cluster statistics
        if log_callback:
            log_callback("Step A5: Calculating cluster statistics...", "INFO")
        
        stats = calculate_cluster_statistics(
            labels_post, features, resampled_bands, num_clusters, log_callback
        )
        
        stats_path = os.path.join(output_dir, "clusters_stats.json")
        with open(stats_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        if log_callback:
            log_callback(f"Statistics saved: {stats_path}", "INFO")
        
        # Step A6: LLM Interpretation
        enable_llm = parameters.get('enable_llm_interpretation', True)
        llm_result = None
        
        if enable_llm:
            if log_callback:
                log_callback("Step A6: Running LLM interpretation...", "INFO")
            
            llm_result = interpret_clusters_with_llm(
                stats, parameters.get('llm_config', {}), log_callback
            )
        
        # Step A7: Create interpreted layer
        if log_callback:
            log_callback("Step A7: Creating interpreted layer...", "INFO")
        
        interpreted_layer_path = os.path.join(output_dir, "interpreted_layer.tif")
        interpretation_report_path = os.path.join(output_dir, "interpretation_report.json")
        legend_path = os.path.join(output_dir, "legend.json")
        
        create_interpreted_layer(
            labels_post, llm_result, resampled_bands['reference_layer'],
            interpreted_layer_path, interpretation_report_path, legend_path,
            log_callback
        )
        
        # Load output layer
        output_layer = QgsRasterLayer(interpreted_layer_path, "Interpreted Classification")
        
        if not output_layer.isValid():
            # Fallback to raw clusters
            output_layer = QgsRasterLayer(clusters_raw_path, "Raw Clusters")
        
        if log_callback:
            log_callback("=== Classification Pipeline Complete ===", "INFO")
        
        return {
            'layer': output_layer,
            'labels': labels_post,
            'num_clusters': num_clusters,
            'output_path': interpreted_layer_path,
            'raw_path': clusters_raw_path,
            'post_path': clusters_post_path if enable_postprocessing else None,
            'stats_path': stats_path,
            'total_pixels': int(np.sum(valid_mask)),
            'cluster_sizes': cluster_sizes,
            'stats': stats,
            'llm_result': llm_result
        }
        
    except Exception as e:
        import traceback
        error_msg = f"Classification error: {str(e)}"
        traceback_str = traceback.format_exc()
        if log_callback:
            log_callback(error_msg, "ERROR")
            log_callback(traceback_str, "ERROR")
        raise


def resample_bands(raster_layer, band_mapping, roi, log_callback=None):
    """
    Resample all bands to 10m resolution using GDAL warp.
    
    :param raster_layer: Input raster layer
    :type raster_layer: QgsRasterLayer
    :param band_mapping: Dictionary mapping band codes to band numbers
    :type band_mapping: dict
    :param roi: ROI configuration
    :type roi: dict
    :param log_callback: Optional logging callback
    :type log_callback: callable
    
    :returns: Dictionary with resampled bands
    :rtype: dict
    """
    try:
        # Determine target extent
        if roi['type'] == 'full':
            extent = raster_layer.extent()
        elif roi['type'] == 'rectangle':
            extent = roi['geometry']
        elif roi['type'] == 'polygon':
            extent = roi['geometry'].boundingBox()
        elif roi['type'] == 'mask':
            extent = roi['layer'].extent()
        else:
            extent = raster_layer.extent()
        
        # Get CRS
        crs = raster_layer.crs()
        
        # Determine target resolution (10m)
        target_resolution = 10.0
        
        # Calculate target dimensions
        width = int((extent.xMaximum() - extent.xMinimum()) / target_resolution)
        height = int((extent.yMaximum() - extent.yMinimum()) / target_resolution)
        
        if log_callback:
            log_callback(f"Target resolution: {target_resolution}m, Size: {width}x{height}", "INFO")
        
        # Resample each band
        resampled_bands = {}
        temp_dir = tempfile.gettempdir()
        
        for band_code, band_number in band_mapping.items():
            if log_callback:
                log_callback(f"Resampling {band_code} (band {band_number})...", "DEBUG")
            
            # Create temporary output path
            temp_output = os.path.join(temp_dir, f"resampled_{band_code}_{os.getpid()}.tif")
            
            # Use GDAL warp to resample
            params = {
                'INPUT': raster_layer.source(),
                'SOURCE_CRS': crs,
                'TARGET_CRS': crs,
                'RESAMPLING': 0,  # Nearest neighbor (0) or bilinear (1)
                'TARGET_RESOLUTION': target_resolution,
                'OUTPUT': temp_output
            }
            
            # Set extent
            params['TARGET_EXTENT'] = f"{extent.xMinimum()},{extent.xMaximum()},{extent.yMinimum()},{extent.yMaximum()}"
            params['TARGET_EXTENT_CRS'] = crs
            
            try:
                result = processing.run("gdal:warpreproject", params)
                resampled_layer = QgsRasterLayer(result['OUTPUT'], f"Resampled_{band_code}")
                
                if resampled_layer.isValid():
                    resampled_bands[band_code] = resampled_layer
                    if log_callback:
                        log_callback(f"Successfully resampled {band_code}", "DEBUG")
                else:
                    raise ValueError(f"Failed to resample band {band_code}")
            except Exception as e:
                if log_callback:
                    log_callback(f"GDAL warp failed for {band_code}: {str(e)}", "WARNING")
                    log_callback("Falling back to direct band extraction...", "WARNING")
                
                # Fallback: extract band directly (assumes same resolution)
                provider = raster_layer.dataProvider()
                width = raster_layer.width()
                height = raster_layer.height()
                block = provider.block(band_number, extent, width, height)
                band_array = np.array(block.data())
                
                # Create temporary layer from array (simplified)
                # This is a fallback - proper implementation would create a proper raster
                resampled_bands[band_code] = {
                    'array': band_array,
                    'extent': extent,
                    'width': width,
                    'height': height
                }
        
        # Store reference layer (use first resampled layer)
        if resampled_bands:
            first_band = list(resampled_bands.values())[0]
            if isinstance(first_band, QgsRasterLayer):
                resampled_bands['reference_layer'] = first_band
            else:
                # Create a reference layer from the original
                resampled_bands['reference_layer'] = raster_layer
        
        return resampled_bands
        
    except Exception as e:
        if log_callback:
            log_callback(f"Resampling error: {str(e)}", "ERROR")
        raise


def calculate_features(resampled_bands, log_callback=None):
    """
    Calculate NDVI, MNDWI, and NDBI from resampled bands.
    
    Formulas:
    - NDVI = (B8 - B4) / (B8 + B4)
    - MNDWI = (B3 - B11) / (B3 + B11)
    - NDBI = (B11 - B8) / (B11 + B8)
    """
    features = {}
    
    # Extract band arrays
    def get_band_array(band_code):
        band_data = resampled_bands.get(band_code)
        if isinstance(band_data, QgsRasterLayer):
            provider = band_data.dataProvider()
            extent = band_data.extent()
            block = provider.block(1, extent, band_data.width(), band_data.height())
            return np.array(block.data()).astype(np.float32)
        elif isinstance(band_data, dict):
            return band_data.get('array', np.array([])).astype(np.float32)
        return None
    
    B2 = get_band_array('B2')
    B3 = get_band_array('B3')
    B4 = get_band_array('B4')
    B8 = get_band_array('B8')
    B11 = get_band_array('B11')
    
    # Store original bands
    if B2 is not None:
        features['B2'] = B2
    if B3 is not None:
        features['B3'] = B3
    if B4 is not None:
        features['B4'] = B4
    if B8 is not None:
        features['B8'] = B8
    if B11 is not None:
        features['B11'] = B11
    
    # Calculate NDVI = (B8 - B4) / (B8 + B4)
    if B8 is not None and B4 is not None:
        ndvi = np.divide(
            B8 - B4,
            B8 + B4 + 1e-10,
            out=np.zeros_like(B8, dtype=np.float32),
            where=(B8 + B4) != 0
        )
        features['NDVI'] = ndvi
        if log_callback:
            log_callback("Calculated NDVI", "DEBUG")
    
    # Calculate MNDWI = (B3 - B11) / (B3 + B11)
    if B3 is not None and B11 is not None:
        mndwi = np.divide(
            B3 - B11,
            B3 + B11 + 1e-10,
            out=np.zeros_like(B3, dtype=np.float32),
            where=(B3 + B11) != 0
        )
        features['MNDWI'] = mndwi
        if log_callback:
            log_callback("Calculated MNDWI", "DEBUG")
    
    # Calculate NDBI = (B11 - B8) / (B11 + B8)
    if B11 is not None and B8 is not None:
        ndbi = np.divide(
            B11 - B8,
            B11 + B8 + 1e-10,
            out=np.zeros_like(B11, dtype=np.float32),
            where=(B11 + B8) != 0
        )
        features['NDBI'] = ndbi
        if log_callback:
            log_callback("Calculated NDBI", "DEBUG")
    
    # Store shape information
    if B2 is not None:
        features['shape'] = B2.shape
    elif B3 is not None:
        features['shape'] = B3.shape
    elif B4 is not None:
        features['shape'] = B4.shape
    
    return features


def prepare_features(features, log_callback=None):
    """Prepare feature matrix [B2, B3, B4, B8, B11, NDVI, MNDWI, NDBI]."""
    feature_list = []
    feature_names = []
    
    # Add spectral bands in order
    for band_code in ['B2', 'B3', 'B4', 'B8', 'B11']:
        if band_code in features:
            feature_list.append(features[band_code].flatten())
            feature_names.append(band_code)
    
    # Add calculated indices
    for index_name in ['NDVI', 'MNDWI', 'NDBI']:
        if index_name in features:
            feature_list.append(features[index_name].flatten())
            feature_names.append(index_name)
    
    if log_callback:
        log_callback(f"Feature matrix: {', '.join(feature_names)}", "INFO")
    
    # Stack features
    X = np.column_stack(feature_list)
    
    # Remove NaN and infinite values
    valid_mask = np.isfinite(X).all(axis=1)
    X = X[valid_mask]
    
    if log_callback:
        log_callback(f"Valid pixels: {len(X)} / {len(valid_mask)}", "INFO")
    
    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    shape = features.get('shape', (X.shape[0], 1))
    
    return X_scaled, valid_mask, shape


def reshape_labels_safe(labels, shape, valid_mask, log_callback=None):
    """Safely reshape labels to match original raster dimensions."""
    total_pixels = shape[0] * shape[1] if len(shape) == 2 else np.prod(shape)
    valid_count = np.sum(valid_mask)
    
    if log_callback:
        log_callback(f"Reshaping: {len(labels)} labels, {valid_count} valid, {total_pixels} total", "DEBUG")
    
    # Create output array with NoData values
    if total_pixels != len(valid_mask):
        if log_callback:
            log_callback(f"Shape mismatch: adjusting from {len(valid_mask)} to {total_pixels}", "WARNING")
        
        # Truncate or pad valid_mask
        if len(valid_mask) > total_pixels:
            valid_mask = valid_mask[:total_pixels]
        else:
            padding = np.zeros(total_pixels - len(valid_mask), dtype=bool)
            valid_mask = np.concatenate([valid_mask, padding])
    
    labels_reshaped = np.full(total_pixels, -9999, dtype=np.int32)
    
    # Ensure labels fit
    if len(labels) > valid_count:
        labels = labels[:valid_count]
    elif len(labels) < valid_count:
        padding = np.full(valid_count - len(labels), -9999, dtype=np.int32)
        labels = np.concatenate([labels, padding])
    
    labels_reshaped[valid_mask] = labels
    labels_reshaped = labels_reshaped.reshape(shape)
    
    return labels_reshaped


def apply_majority_filter(labels, log_callback=None):
    """Apply 3x3 majority filter to remove salt-and-pepper noise."""
    if log_callback:
        log_callback("Applying 3x3 majority filter...", "DEBUG")
    
    # Use scipy's generic filter with mode function
    from scipy.stats import mode
    
    def majority_filter_func(values):
        # Get most common value (excluding NoData)
        valid_values = values[values != -9999]
        if len(valid_values) > 0:
            return mode(valid_values)[0][0]
        return -9999
    
    # Apply filter
    filtered = ndimage.generic_filter(
        labels.astype(np.float32),
        majority_filter_func,
        size=3,
        mode='constant',
        cval=-9999
    )
    
    return filtered.astype(np.int32)


def remove_small_clusters(labels, min_area_pixels, log_callback=None):
    """Remove connected components smaller than min_area_pixels."""
    if log_callback:
        log_callback(f"Removing clusters smaller than {min_area_pixels} pixels...", "DEBUG")
    
    # Label connected components
    labeled_array, num_features = label(labels != -9999)
    
    # Find objects
    objects = find_objects(labeled_array)
    
    removed_count = 0
    for i, obj in enumerate(objects):
        if obj is None:
            continue
        
        # Calculate size
        component_mask = (labeled_array == (i + 1))
        size = np.sum(component_mask)
        
        if size < min_area_pixels:
            # Remove small cluster
            labels[component_mask] = -9999
            removed_count += 1
    
    if log_callback:
        log_callback(f"Removed {removed_count} small clusters", "INFO")
    
    return labels


def calculate_cluster_statistics(labels, features, resampled_bands, num_clusters, log_callback=None):
    """Calculate detailed statistics for each cluster."""
    stats = {}
    total_pixels = np.sum(labels != -9999)
    
    for cluster_id in range(num_clusters):
        cluster_mask = (labels == cluster_id)
        cluster_pixels = np.sum(cluster_mask)
        
        if cluster_pixels == 0:
            continue
        
        cluster_stats = {
            "pixel_count": int(cluster_pixels),
            "percent_area": float(cluster_pixels / total_pixels * 100) if total_pixels > 0 else 0.0
        }
        
        # Calculate mean values for each feature
        for feature_name in ['B2', 'B3', 'B4', 'B8', 'B11', 'NDVI', 'MNDWI', 'NDBI']:
            if feature_name in features:
                feature_array = features[feature_name]
                if feature_array.shape == labels.shape:
                    cluster_values = feature_array[cluster_mask]
                    cluster_stats[f"mean_{feature_name}"] = float(np.nanmean(cluster_values))
                    
                    # Calculate std for indices
                    if feature_name in ['NDVI', 'MNDWI', 'NDBI']:
                        cluster_stats[f"std_{feature_name}"] = float(np.nanstd(cluster_values))
        
        stats[f"cluster_{cluster_id}"] = cluster_stats
    
    return stats


def interpret_clusters_with_llm(stats, llm_config, log_callback=None):
    """
    Interpret clusters using LLM with rule-based fallback.
    """
    if not llm_config or not llm_config.get('enabled', False):
        if log_callback:
            log_callback("LLM interpretation disabled, using rule-based fallback", "INFO")
        return rule_based_interpretation(stats, log_callback)
    
    try:
        from .llm_client import LLMClient
        from .llm_prompt import build_classification_prompt
        
        # Build prompt
        prompt = build_classification_prompt(stats, {'algorithm': 'k-means'})
        
        # Create client
        client = LLMClient(
            llm_config.get('provider', 'Ollama'),
            llm_config.get('base_url', 'http://localhost:11434'),
            llm_config.get('api_key', ''),
            llm_config.get('model', 'llama2')
        )
        
        # Generate response
        response = client.generate(prompt)
        
        if response:
            # Parse JSON response
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                llm_result = json.loads(json_match.group())
                if log_callback:
                    log_callback("LLM interpretation successful", "INFO")
                return llm_result
        
        # Fallback if LLM fails
        if log_callback:
            log_callback("LLM interpretation failed, using rule-based fallback", "WARNING")
        return rule_based_interpretation(stats, log_callback)
        
    except Exception as e:
        if log_callback:
            log_callback(f"LLM error: {str(e)}, using rule-based fallback", "WARNING")
        return rule_based_interpretation(stats, log_callback)


def rule_based_interpretation(stats, log_callback=None):
    """Rule-based cluster interpretation fallback."""
    if log_callback:
        log_callback("Applying rule-based interpretation...", "INFO")
    
    interpretation = {}
    
    for cluster_key, cluster_stats in stats.items():
        cluster_id = int(cluster_key.split('_')[1])
        
        mean_mndwi = cluster_stats.get('mean_MNDWI', 0.0)
        mean_ndvi = cluster_stats.get('mean_NDVI', 0.0)
        mean_ndbi = cluster_stats.get('mean_NDBI', 0.0)
        
        # Apply rules
        if mean_mndwi > 0.3:
            label = "Water"
            confidence = 0.8
            rationale = f"MNDWI > 0.3 ({mean_mndwi:.3f}) indicates water"
        elif mean_ndvi > 0.6:
            label = "Forest"
            confidence = 0.75
            rationale = f"NDVI > 0.6 ({mean_ndvi:.3f}) indicates dense vegetation"
        elif 0.3 <= mean_ndvi <= 0.6:
            label = "Grassland"
            confidence = 0.7
            rationale = f"NDVI 0.3-0.6 ({mean_ndvi:.3f}) indicates grassland"
        elif mean_ndbi > 0.2:
            label = "Built-up"
            confidence = 0.75
            rationale = f"NDBI > 0.2 ({mean_ndbi:.3f}) indicates built-up areas"
        elif mean_ndvi < 0.1 and mean_mndwi < 0:
            label = "Bare soil/rock"
            confidence = 0.7
            rationale = f"Low NDVI ({mean_ndvi:.3f}) and negative MNDWI ({mean_mndwi:.3f})"
        else:
            label = "Unknown"
            confidence = 0.5
            rationale = "Does not match clear land cover patterns"
        
        interpretation[f"cluster_{cluster_id}"] = {
            "label": label,
            "confidence": confidence,
            "rationale": rationale
        }
    
    return interpretation


def create_interpreted_layer(labels, llm_result, reference_layer, output_path, report_path, legend_path, log_callback=None):
    """Create interpreted layer with semantic labels."""
    if not llm_result:
        if log_callback:
            log_callback("No LLM result, using cluster IDs as labels", "WARNING")
        llm_result = {}
    
    # Create label mapping
    label_mapping = {}
    legend = {}
    
    for cluster_id in range(np.max(labels) + 1):
        cluster_key = f"cluster_{cluster_id}"
        if cluster_key in llm_result:
            label = llm_result[cluster_key].get('label', f'Cluster {cluster_id}')
            label_mapping[cluster_id] = label
            
            # Create legend entry
            legend[cluster_id] = {
                "label": label,
                "color": get_color_for_label(label),
                "confidence": llm_result[cluster_key].get('confidence', 0.5)
            }
        else:
            label_mapping[cluster_id] = f'Cluster {cluster_id}'
            legend[cluster_id] = {
                "label": f'Cluster {cluster_id}',
                "color": "#808080",
                "confidence": 0.5
            }
    
    # Apply mapping to labels
    interpreted = labels.copy()
    for cluster_id, label_name in label_mapping.items():
        interpreted[labels == cluster_id] = cluster_id  # Keep ID for now
    
    # Save interpreted raster
    create_output_raster(reference_layer, interpreted, output_path, log_callback)
    
    # Save report
    report = {
        "interpretation_method": "LLM" if llm_result else "Rule-based",
        "clusters": llm_result,
        "timestamp": str(np.datetime64('now'))
    }
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Save legend
    with open(legend_path, 'w') as f:
        json.dump(legend, f, indent=2)
    
    if log_callback:
        log_callback(f"Interpreted layer saved: {output_path}", "INFO")
        log_callback(f"Report saved: {report_path}", "INFO")
        log_callback(f"Legend saved: {legend_path}", "INFO")


def get_color_for_label(label):
    """Get color for land cover label."""
    color_map = {
        "Water": "#0066CC",
        "Forest": "#00CC00",
        "Grassland": "#90EE90",
        "Cropland": "#FFD700",
        "Built-up": "#808080",
        "Bare soil/rock": "#D2691E",
        "Wetland": "#008B8B",
        "Shadow": "#000000",
        "Unknown": "#FF00FF"
    }
    return color_map.get(label, "#808080")


def create_output_raster(reference_layer, labels, output_path, log_callback=None):
    """Create output raster from labels array."""
    try:
        from osgeo import gdal, osr
        
        # Get reference properties
        if isinstance(reference_layer, QgsRasterLayer):
            extent = reference_layer.extent()
            crs = reference_layer.crs()
            width = reference_layer.width()
            height = reference_layer.height()
        else:
            # Fallback
            extent = QgsRectangle()
            crs = QgsCoordinateReferenceSystem()
            height, width = labels.shape
        
        # Create output dataset
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(
            output_path,
            width,
            height,
            1,
            gdal.GDT_Int32
        )
        
        # Set geotransform
        pixel_size_x = (extent.xMaximum() - extent.xMinimum()) / width
        pixel_size_y = (extent.yMaximum() - extent.yMinimum()) / height
        
        geotransform = [
            extent.xMinimum(),
            pixel_size_x,
            0,
            extent.yMaximum(),
            0,
            -pixel_size_y
        ]
        out_ds.SetGeoTransform(geotransform)
        
        # Set projection
        srs = osr.SpatialReference()
        srs.ImportFromWkt(crs.toWkt())
        out_ds.SetProjection(srs.ExportToWkt())
        
        # Write data
        out_band = out_ds.GetRasterBand(1)
        out_band.WriteArray(labels)
        out_band.SetNoDataValue(-9999)
        out_band.FlushCache()
        
        out_ds = None
        
        if log_callback:
            log_callback(f"Raster saved: {output_path}", "INFO")
        
        return output_path
        
    except ImportError:
        if log_callback:
            log_callback("GDAL not available, cannot create raster", "ERROR")
        raise
    except Exception as e:
        if log_callback:
            log_callback(f"Error creating raster: {str(e)}", "ERROR")
        raise


def calculate_cluster_sizes(labels, num_clusters):
    """Calculate size of each cluster."""
    cluster_sizes = {}
    for i in range(num_clusters):
        cluster_sizes[i] = int(np.sum(labels == i))
    return cluster_sizes
