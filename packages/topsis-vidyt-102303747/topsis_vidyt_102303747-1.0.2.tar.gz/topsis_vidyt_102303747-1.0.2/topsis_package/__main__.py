"""CLI module for TOPSIS."""

import csv
import sys
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from topsis_package.core import topsis


def load_data_file(file_path: str) -> List[List[str]]:
	"""Load data from CSV or XLSX file.
	
	Returns a list of rows (each row is a list of strings).
	"""
	path = Path(file_path)
	if not path.exists():
		raise FileNotFoundError(f"File not found: {file_path}")
	
	if path.suffix.lower() == ".xlsx":
		df = pd.read_excel(file_path, sheet_name=0)
		rows = [df.columns.tolist()]
		for _, row in df.iterrows():
			rows.append([str(x) for x in row.tolist()])
		return rows
	elif path.suffix.lower() == ".csv":
		with open(file_path, newline="", encoding="utf-8") as f:
			reader = csv.reader(f)
			rows = list(reader)
		return rows
	else:
		raise ValueError("File must be CSV or XLSX")


def main() -> None:
	"""Main CLI entry point."""
	def error(msg: str) -> None:
		print(f"Error: {msg}")
		sys.exit(1)

	if len(sys.argv) != 5:
		error("Usage: python -m topsis_package <InputDataFile> <Weights> <Impacts> <OutputResultFile>")

	input_path, weights_raw, impacts_raw, output_path = sys.argv[1:]

	# Parse weights
	try:
		weights = [float(w.strip()) for w in weights_raw.split(",")]
	except ValueError:
		error("Weights must be numeric and separated by commas")

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
	for r_idx, row in enumerate(data_rows, start=2):
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
	except Exception as exc:
		error(str(exc))

	# Write output
	out_header = header + ["Topsis Score", "Rank"]
	with open(output_path, "w", newline="", encoding="utf-8") as f_out:
		writer = csv.writer(f_out)
		writer.writerow(out_header)
		for id_val, row_vals, score, rank in zip(ids, matrix, result.scores, result.ranks):
			writer.writerow([id_val, *row_vals, f"{score:.6f}", int(rank)])

	print(f"Result written to {output_path}")


if __name__ == "__main__":
	main()
