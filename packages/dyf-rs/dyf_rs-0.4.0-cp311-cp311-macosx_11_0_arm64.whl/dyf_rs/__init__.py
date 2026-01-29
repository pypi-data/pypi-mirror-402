"""
DYF-RS - Density Yields Features (Rust Core)

This is the Rust-accelerated core for the dyf package.
Install the 'dyf' package for the full Python interface.

Example:
    >>> from dyf_rs import DensityClassifier
    >>> classifier = DensityClassifier(embedding_dim=384)
    >>> classifier.fit(embeddings)
    >>> print(classifier.report())
"""

from ._core import (
    PyDensityClassifier as DensityClassifier,
    PyDensityReport as DensityReport,
    PyBridgeAnalysis as BridgeAnalysis,
)

from importlib.metadata import version as _get_version
__version__ = _get_version("dyf-rs")
__all__ = ["DensityClassifier", "DensityReport", "BridgeAnalysis"]
