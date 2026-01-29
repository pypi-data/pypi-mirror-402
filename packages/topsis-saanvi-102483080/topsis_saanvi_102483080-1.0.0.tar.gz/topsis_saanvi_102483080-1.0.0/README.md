Project Description

Submitted by: Saanvi Wadhwa
Roll No: 102483080
Group: 3C15

## Overview

topsis-saanvi-102483080 is a Python package designed to solve multi-criteria decision-making (MCDM) problems using the TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) method.
The package allows users to evaluate multiple alternatives based on several criteria and ranks them according to their relative closeness to the ideal solution.

## Key Features
Command-line based execution
Supports any number of criteria and alternatives
Accepts weights and impacts as comma-separated inputs
Handles both benefit (+) and cost (-) criteria
Produces a ranked output in CSV format

## Installation
The package can be installed using pip.
From TestPyPI:
pip install -i https://test.pypi.org/simple/ topsis-saanvi-102483080 --extra-index-url https://pypi.org/simple


## How to Use

Provide the input CSV file followed by the weights and impacts.
Syntax:
topsis <input.csv> <weights> <impacts> <output.csv>

Example:
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+" result.csv

Note:
If weights or impacts contain spaces, enclose them within double quotes.

## Sample Input
Example Dataset
data.csv

The following dataset represents different investment funds evaluated across multiple parameters.

| Fund Name | P1   | P2   | P3  | P4   | P5    |
| --------- | ---- | ---- | --- | ---- | ----- |
| M1        | 0.84 | 0.71 | 6.7 | 42.1 | 12.59 |
| M2        | 0.91 | 0.83 | 7.0 | 31.7 | 10.11 |
| M3        | 0.79 | 0.62 | 4.8 | 46.7 | 13.23 |
| M4        | 0.78 | 0.61 | 6.4 | 42.4 | 12.55 |
| M5        | 0.94 | 0.88 | 3.6 | 62.2 | 16.91 |
| M6        | 0.88 | 0.77 | 6.5 | 51.5 | 14.91 |
| M7        | 0.66 | 0.44 | 5.3 | 48.9 | 13.83 |
| M8        | 0.93 | 0.86 | 3.4 | 37.0 | 10.55 |


## Output
The output file includes:
TOPSIS Score – numerical measure of preference
Rank – relative ranking of alternatives
Higher score indicates a better alternative.

## Assumptions
The first column contains alternative names.
Remaining columns must be numeric.
Number of weights must match number of criteria.
Impacts can only be + or -.

## License
This project is released under the MIT License and is intended for academic use.

## Author
Saanvi Wadhwa

