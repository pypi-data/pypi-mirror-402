# EDSMapPlotter

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fdossi/EDSMapPlotter/blob/main/EDSMapPlotter_Colab.ipynb)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17741072.svg)](https://doi.org/10.5281/zenodo.17741072)
![License](https://img.shields.io/github/license/fdossi/EDSMapPlotter)
![Release](https://img.shields.io/github/v/release/fdossi/EDSMapPlotter)

**EDSMapPlotter** is an open-source tool for automating the generation of heatmaps from raw Energy Dispersive Spectroscopy (EDS/EDX) microscopy data.

The software converts numeric matrices (`.csv` files exported from SEM microscopes) into high-resolution (300 DPI) images ready for scientific publication.

---

## 🚀 How to Use

### Option A: Run in the Cloud (Google Colab)
No installation required. Ideal for quick use or on computers without Python configured.
1. Click the **"Open in Colab"** badge above.
2. Upload your CSV files.
3. Download the generated maps automatically.

### Option B: Install via PyPI (Recommended)
Install directly from Python Package Index:
```bash
pip install edsmapplotter
```

Run the program:
```bash
edsmapplotter
```

### Option C: Local Installation (Developer)
To use the graphical interface (GUI) with drag-and-drop support on Windows/Linux/Mac:

1. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the script:
   ```bash
   python EDSMapPlotter.py
   ```

## Features

**Batch Processing**: Drag dozens of CSV files and convert them all at once.

**Automatic Element Detection**: The script reads the filename (e.g., Area1_Fe.csv) and names the graph correctly ("Fe").

**Visualization**: Support for multiple color maps (Viridis, Inferno, Blues, Reds, etc.).

**High Quality**: Fixed 300 DPI export.

## Input Format

The software expects `.csv` files containing only the intensity matrix (without text headers), which is the standard export format from many microanalysis software packages.

## Citation

If you use this tool in your research, please cite:

Dossi, F. (2025). *EDSMapPlotter: A Python tool for EDS map visualization* (Version v0.2.1) [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.17741072