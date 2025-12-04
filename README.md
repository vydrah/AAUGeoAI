# AI Unsupervised Classification QGIS Plugin

A QGIS plugin that combines unsupervised satellite image classification with AI interpretation using Large Language Models (LLMs).

## Features

- **Multiple Classification Backends**: OTB, SAGA, GRASS, and Python fallback (K-means with NDVI/MNDWI/NDBI features)
- **AI Interpretation**: Integration with Ollama, OpenAI (via OpenRouter), Claude, and Gemini
- **Interactive Wizard**: 6-step guided workflow for classification setup
- **Flexible ROI Selection**: Full canvas, rectangle, polygon, or mask layer
- **Automatic Band Detection**: Supports Sentinel-2 and Landsat band mapping
- **Live Processing Log**: Real-time status updates and AI reasoning display
- **Smart Styling**: AI-generated cluster colors and labels with QML export

## Installation

1. Copy this plugin folder to your QGIS plugins directory:
   - Windows: `C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - macOS: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

2. Enable the plugin in QGIS: `Plugins → Manage and Install Plugins → Installed → AI Unsupervised Classification`

## Usage

1. **Configure Settings**: `Plugins → AI Unsupervised Classification → Settings`
   - Select LLM provider (Ollama, OpenRouter, Gemini)
   - Enter API key and model name
   - Test connection

2. **Start Classification**: `Plugins → AI Unsupervised Classification → Start Classification Wizard`
   - Follow the 6-step wizard
   - Select algorithm, configure parameters, choose ROI, map bands
   - Review LLM configuration and output options
   - Execute classification

3. **Monitor Progress**: The AI Processing Log dock widget shows real-time status

## Requirements

- QGIS 3.0 or higher
- Python 3.x
- Optional: OTB, SAGA, GRASS (for respective classification backends)
- LLM API access (Ollama, OpenAI, Claude, or Gemini)

## License

[Specify your license here]

