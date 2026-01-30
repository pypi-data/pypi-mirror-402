"""
EDSMapPlotter - EDS/EDX Heatmap Generation Tool

A Python tool for automating the generation of publication-quality heatmaps
from raw Energy Dispersive Spectroscopy (EDS/EDX) microscopy data.
"""

__version__ = "0.2.1"
__author__ = "Fabio Dossi"
__license__ = "MIT"

from .core import gerar_eds_map, COLORMAP_OPTIONS
from .gui import run_gui

__all__ = ["gerar_eds_map", "COLORMAP_OPTIONS", "run_gui"]
