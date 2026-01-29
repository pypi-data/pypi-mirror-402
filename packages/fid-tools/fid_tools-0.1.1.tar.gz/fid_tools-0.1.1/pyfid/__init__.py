"""
pyfid - Functional Information Decomposition (FID)

A library for analyzing how multiple input variables contribute to predicting
an output using information-theoretic concepts.

Based on the paper:
    "Functional Information Decomposition: A First-Principles Approach to
    Analyzing Functional Relationships"
    Bohm, Ragusa, Hintze, and Adami (2026)

Usage:
    from pyfid import TPM, display_fid

    tpm = TPM.from_data([input1, input2, output])
    result = tpm.fid()
    display_fid(result)
"""

__version__ = "0.1.0"

from .core import (
    # Main class
    TPM,

    # Utility functions
    entropy,

    # Display functions
    display_fid,
    display_fid_with_bounds,
    get_metric,

    # Plotting functions
    plot_fid_clouds,
    plot_fid_clouds_3d,
    plot_fid_relationships,
)

__all__ = [
    "TPM",
    "entropy",
    "display_fid",
    "display_fid_with_bounds",
    "get_metric",
    "plot_fid_clouds",
    "plot_fid_clouds_3d",
    "plot_fid_relationships",
]
