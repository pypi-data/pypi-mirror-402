"""
nprobust: Nonparametric Robust Estimation and Inference Methods

This package provides tools for data-driven statistical analysis using
local polynomial regression and kernel density estimation methods.

Based on:
    Calonico, Cattaneo and Farrell (2018): "On the Effect of Bias Estimation
    on Coverage Accuracy in Nonparametric Inference",
    Journal of the American Statistical Association.

    Calonico, Cattaneo and Farrell (2019): "nprobust: Nonparametric Kernel-Based
    Estimation and Robust Bias-Corrected Inference",
    Journal of Statistical Software.
"""

from .lprobust import lprobust
from .lpbwselect import lpbwselect
from .kdrobust import kdrobust
from .kdbwselect import kdbwselect
from .nprobust_plot import nprobust_plot

__version__ = "0.5.0"
__author__ = "Translated from R package by Calonico, Cattaneo, and Farrell"

__all__ = [
    'lprobust',
    'lpbwselect',
    'kdrobust',
    'kdbwselect',
    'nprobust_plot'
]
