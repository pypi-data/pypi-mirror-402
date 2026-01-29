"""Simple TOPSIS implementation (step-by-step).

This file is built in two phases:
1) Implement the core TOPSIS calculation as regular Python functions.
2) Wrap it in a CLI that reads CSV, validates inputs, and writes results.

Right now we focus on step 1 so you can see how the algorithm works.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import numpy as np
import pandas as pd


@dataclass
class TopsisResult:
	scores: np.ndarray  # closeness coefficient for each alternative
	ranks: np.ndarray   # 1-based ranks (1 is best)


def _normalize_matrix(matrix: np.ndarray) -> np.ndarray:
	"""Vector-normalize each column.

	The formula is: v_ij = x_ij / sqrt(sum_i x_ij^2)
	"""

	# Compute the L2 norm for each column; keepdims to broadcast cleanly.
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


def load_data_file(file_path: str) -> List[List[str]]:
	"""Load data from CSV or XLSX file.
	
	Returns a list of rows (each row is a list of strings).
	"""
	path = Path(file_path)
	if not path.exists():
		raise FileNotFoundError(f"File not found: {file_path}")
	
	if path.suffix.lower() == ".xlsx":
		# Load XLSX using pandas
		df = pd.read_excel(file_path, sheet_name=0)
		# Convert to list of lists (including header)
		rows = [df.columns.tolist()]
		for _, row in df.iterrows():
			rows.append([str(x) for x in row.tolist()])
		return rows
	elif path.suffix.lower() == ".csv":
		# Load CSV using csv module
		with open(file_path, newline="", encoding="utf-8") as f:
			reader = csv.reader(f)
			rows = list(reader)
		return rows
	else:
		raise ValueError("File must be CSV or XLSX")


if __name__ == "__main__":
	def error(msg: str) -> None:
		print(f"Error: {msg}")
		sys.exit(1)

	# Expect: script input.csv "1,1,2" "+,-,+" output.csv
	if len(sys.argv) != 5:
		error("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFile>")

	input_path, weights_raw, impacts_raw, output_path = sys.argv[1:]

	# Parse weights
	try:
		weights = [float(w.strip()) for w in weights_raw.split(",")]
	except ValueError:
		error("Weights must be numeric and separated by commas")
	if any(np.isnan(weights)):
		error("Weights must be valid numbers")

	# Parse impacts
	impacts = [i.strip() for i in impacts_raw.split(",")]
	if not impacts:
		error("Impacts must be provided")
	if any(i not in {"+", "-"} for i in impacts):
		error("Impacts must be either '+' or '-' and separated by commas")

	# Load data file (CSV or XLSX)
	try:
		rows = load_data_file(input_path)
	except FileNotFoundError:
		error("Input file not found")
	except ValueError as e:
		error(str(e))

	if not rows:
		error("Input file is empty")

	# First row is header; first column assumed identifier, rest criteria
	header = rows[0]
	data_rows = rows[1:]

	if len(header) < 3:
		error("Input file must contain at least three columns (id + >=2 criteria)")

	if not data_rows:
		error("Input file must contain data rows")

	num_criteria = len(header) - 1
	if len(weights) != num_criteria or len(impacts) != num_criteria:
		error("Number of weights, impacts, and criteria columns must match")

	ids: List[str] = []
	matrix: List[List[float]] = []
	for r_idx, row in enumerate(data_rows, start=2):  # start=2 for 1-based line number incl header
		if len(row) != len(header):
			error(f"Row {r_idx} has {len(row)} columns; expected {len(header)}")
		ids.append(row[0])
		try:
			values = [float(x) for x in row[1:]]
		except ValueError:
			error(f"Non-numeric value found in row {r_idx} (criteria columns must be numeric)")
		matrix.append(values)

	matrix_np = np.asarray(matrix, dtype=float)

	# Run TOPSIS
	try:
		result = topsis(matrix_np, weights, impacts)
	except Exception as exc:  # surface any algorithm/validation errors
		error(str(exc))

	# Write output with appended columns
	out_header = header + ["Topsis Score", "Rank"]
	with open(output_path, "w", newline="", encoding="utf-8") as f_out:
		writer = csv.writer(f_out)
		writer.writerow(out_header)
		for id_val, row_vals, score, rank in zip(ids, matrix, result.scores, result.ranks):
			writer.writerow([id_val, *row_vals, f"{score:.6f}", int(rank)])

	print(f"Result written to {output_path}")
