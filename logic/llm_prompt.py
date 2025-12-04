"""
LLM Prompt Builder for Classification Interpretation
"""

import json
import re


def build_classification_prompt(statistics, classification_result):
    """
    Build a JSON prompt for LLM interpretation of classification results.
    Uses the specified template format.
    
    :param statistics: Cluster statistics dictionary
    :type statistics: dict
    :param classification_result: Classification result dictionary
    :type classification_result: dict
    
    :returns: Formatted prompt string
    :rtype: str
    """
    # Format cluster statistics for prompt
    cluster_stats_text = ""
    for cluster_key, cluster_data in statistics.items():
        if cluster_key.startswith('cluster_'):
            cluster_id = cluster_key.replace('cluster_', '')
            cluster_stats_text += f"\nCluster {cluster_id}:\n"
            cluster_stats_text += f"  Pixel count: {cluster_data.get('pixel_count', 0)}\n"
            cluster_stats_text += f"  Percent area: {cluster_data.get('percent_area', 0):.2f}%\n"
            cluster_stats_text += f"  Mean NDVI: {cluster_data.get('mean_NDVI', 0):.3f}\n"
            cluster_stats_text += f"  Mean NDBI: {cluster_data.get('mean_NDBI', 0):.3f}\n"
            cluster_stats_text += f"  Mean MNDWI: {cluster_data.get('mean_MNDWI', 0):.3f}\n"
            cluster_stats_text += f"  Mean B2: {cluster_data.get('mean_B2', 0):.1f}\n"
            cluster_stats_text += f"  Mean B3: {cluster_data.get('mean_B3', 0):.1f}\n"
            cluster_stats_text += f"  Mean B4: {cluster_data.get('mean_B4', 0):.1f}\n"
            cluster_stats_text += f"  Mean B8: {cluster_data.get('mean_B8', 0):.1f}\n"
            cluster_stats_text += f"  Mean B11: {cluster_data.get('mean_B11', 0):.1f}\n"
    
    prompt = f"""You are a remote-sensing expert. I will provide statistics for K-means clusters generated from a Sentinel-2 image. 

Choose a semantic land-cover class for each cluster from:
[Water, Forest, Grassland, Cropland, Built-up, Bare soil/rock, Wetland, Shadow, Unknown]

Use NDVI, NDBI, MNDWI and band means to infer class.

{cluster_stats_text}

Return JSON:
{{
  "cluster_0": {{"label": "...", "confidence": 0.0-1.0, "rationale": "..."}},
  "cluster_1": {{"label": "...", "confidence": 0.0-1.0, "rationale": "..."}},
  ...
}}

Return ONLY valid JSON, no additional text."""
    
    return prompt


def parse_llm_response(response_text):
    """
    Parse LLM response and extract JSON.
    
    :param response_text: Raw LLM response text
    :type response_text: str
    
    :returns: Parsed JSON dictionary
    :rtype: dict
    """
    import re
    
    # Try to extract JSON from response
    # Look for JSON object in the response
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    
    if json_match:
        json_str = json_match.group()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Try to fix common JSON issues
            json_str = fix_json(json_str)
            return json.loads(json_str)
    else:
        # If no JSON found, try parsing the whole response
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            raise ValueError("Could not parse LLM response as JSON")


def fix_json(json_str):
    """Fix common JSON formatting issues."""
    # Remove trailing commas
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # Fix single quotes to double quotes
    json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
    json_str = re.sub(r":\s*'([^']*)'", r': "\1"', json_str)
    
    return json_str

