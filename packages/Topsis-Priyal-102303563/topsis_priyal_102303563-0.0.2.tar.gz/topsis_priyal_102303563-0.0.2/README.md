# TOPSIS Python Package

## Overview

This package provides a command-line implementation of the TOPSIS
(Technique for Order Preference by Similarity to Ideal Solution) method
using Python.

TOPSIS is a multi-criteria decision-making (MCDM) technique used to rank
alternatives when multiple and often conflicting criteria are involved.

This package allows users to provide their own dataset, assign weights
and impacts to criteria, and obtain a final ranking based on TOPSIS
scores.

---

## What is TOPSIS?

TOPSIS is based on the concept that the best alternative should have the
shortest distance from the ideal best solution and the farthest distance
from the ideal worst solution.

In simple terms:
- The ideal best solution has the most desirable values for all criteria
- The ideal worst solution has the least desirable values for all criteria
- Each alternative is evaluated based on its closeness to the ideal best
  and its distance from the ideal worst
- Alternatives are ranked using the calculated TOPSIS score

TOPSIS is widely used in decision analysis, engineering, management,
finance, and data analysis applications.

---

## What Does This Package Do?

This package performs the following steps:
- Reads input data from a CSV file
- Normalizes the criteria values
- Applies user-defined weights
- Considers impacts (benefit or cost criteria)
- Calculates TOPSIS score for each alternative
- Ranks alternatives based on their TOPSIS score
- Saves the results to an output CSV file

All functionality is provided through a command-line interface.

---

## Installation

Install the package from PyPI using the following command:

pip install Topsis-Priyal-102303563

---

## Usage

Run the TOPSIS analysis using:

topsis <input_file.csv> "<weights>" "<impacts>" <output_file.csv>

### Example

topsis input.csv "1,1,1,2" "+,+,+,-" output.csv

---

## Input File Format

The input file must be a CSV file with:
- First column containing the names of alternatives
- Remaining columns containing numeric criteria values only

### Example input.csv

Fund,P1,P2,P3,P4
M1,0.67,0.45,0.52,16.25
M2,0.60,0.36,0.63,14.47
M3,0.82,0.63,0.51,18.40

---

## Weights and Impacts

### Weights
- Numeric values representing the importance of each criterion
- Must be provided in the same order as criteria columns
- Must be comma-separated

Example:
1,1,1,2

### Impacts
- "+" indicates a benefit criterion (higher value is better)
- "-" indicates a cost criterion (lower value is better)
- Must be comma-separated

Example:
+,+,+,-

---

## Output File

The output CSV file contains:
- All original data columns
- An additional column named "Topsis Score"
- An additional column named "Rank"

A higher TOPSIS score indicates a better alternative.

---

## Error Handling

The package includes validation and error handling for:
- Incorrect number of command-line arguments
- Missing or invalid input files
- Non-numeric values in criteria columns
- Mismatch in number of weights, impacts, and criteria
- Invalid impact symbols

Clear error messages are displayed when incorrect inputs are provided.

---

## Conclusion

This package provides a simple and accurate implementation of the TOPSIS
method for multi-criteria decision making. It is suitable for academic
use, learning purposes, and basic decision analysis tasks.

---

## Author

Priyal Gupta  

