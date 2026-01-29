"""Core TOPSIS algorithm implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence, Tuple

import numpy as np


@dataclass
class TopsisResult:
	"""Result of TOPSIS calculation."""
	scores: np.ndarray  # closeness coefficient for each alternative
	ranks: np.ndarray   # 1-based ranks (1 is best)


def _normalize_matrix(matrix: np.ndarray) -> np.ndarray:
	"""Vector-normalize each column.

	The formula is: v_ij = x_ij / sqrt(sum_i x_ij^2)
	"""
	denom = np.linalg.norm(matrix, axis=0, keepdims=True)
	if np.any(denom == 0):
		raise ValueError("Column with all zeros cannot be normalized")
	return matrix / denom


def _apply_weights(matrix: np.ndarray, weights: Sequence[float]) -> np.ndarray:
	"""Multiply each column by its weight."""
	w = np.asarray(weights, dtype=float)
	if w.shape[0] != matrix.shape[1]:
		raise ValueError("Weights length must match number of columns")
	return matrix * w


def _ideal_best_worst(matrix: np.ndarray, impacts: Sequence[str]) -> Tuple[np.ndarray, np.ndarray]:
	"""Compute ideal best and ideal worst for each column given impacts.

	For benefit criteria (+): ideal best is max, ideal worst is min.
	For cost criteria (-): ideal best is min, ideal worst is max.
	"""
	impacts_arr = np.asarray(impacts)
	if impacts_arr.shape[0] != matrix.shape[1]:
		raise ValueError("Impacts length must match number of columns")

	ideal_best = np.empty(matrix.shape[1])
	ideal_worst = np.empty(matrix.shape[1])

	for j, impact in enumerate(impacts_arr):
		impact = impact.strip()
		if impact not in {"+", "-"}:
			raise ValueError("Impacts must be '+' or '-' only")
		column = matrix[:, j]
		if impact == "+":
			ideal_best[j] = column.max()
			ideal_worst[j] = column.min()
		else:
			ideal_best[j] = column.min()
			ideal_worst[j] = column.max()
	return ideal_best, ideal_worst


def topsis(matrix: np.ndarray, weights: Iterable[float], impacts: Iterable[str]) -> TopsisResult:
	"""Run TOPSIS on a numeric matrix.

	Args:
		matrix: 2D array of shape (alternatives, criteria) with numeric values.
		weights: iterable of floats, same length as criteria.
		impacts: iterable of '+'/'-' with same length as criteria.

	Returns:
		TopsisResult with scores and 1-based ranks.

	Raises:
		ValueError: If matrix is not 2D or has fewer than 2 criteria columns.
	"""
	matrix = np.asarray(matrix, dtype=float)
	if matrix.ndim != 2:
		raise ValueError("Input matrix must be 2D")
	if matrix.shape[1] < 2:
		raise ValueError("TOPSIS needs at least two criteria columns")

	# 1) Normalize
	norm_matrix = _normalize_matrix(matrix)

	# 2) Apply weights
	weighted = _apply_weights(norm_matrix, weights)

	# 3) Ideal best and worst
	ideal_best, ideal_worst = _ideal_best_worst(weighted, impacts)

	# 4) Distance to ideal best/worst
	dist_best = np.linalg.norm(weighted - ideal_best, axis=1)
	dist_worst = np.linalg.norm(weighted - ideal_worst, axis=1)

	# 5) Closeness coefficient: higher is better
	scores = dist_worst / (dist_best + dist_worst)

	# 6) Rank (1 = best). Use stable ranking: higher score gets lower rank number.
	order = (-scores).argsort(kind="stable")
	ranks = np.empty_like(order)
	ranks[order] = np.arange(1, len(scores) + 1)

	return TopsisResult(scores=scores, ranks=ranks)
