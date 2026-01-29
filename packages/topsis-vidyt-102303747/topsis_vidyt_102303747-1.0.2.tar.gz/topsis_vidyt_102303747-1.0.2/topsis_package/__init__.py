"""
TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) Implementation.

A Python implementation of the TOPSIS multi-criteria decision-making algorithm.
Supports both CSV and XLSX input files.

Usage:
    python -m topsis_package.cli <InputDataFile> <Weights> <Impacts> <OutputResultFile>

Example:
    python -m topsis_package.cli data.xlsx "0.2,0.2,0.2,0.2,0.2" "+,+,+,+,+" output.csv
"""

__version__ = "1.0.0"
__author__ = "Vidyt"
__description__ = "TOPSIS decision-making algorithm implementation"

from topsis_package.core import topsis, TopsisResult

__all__ = ["topsis", "TopsisResult"]
