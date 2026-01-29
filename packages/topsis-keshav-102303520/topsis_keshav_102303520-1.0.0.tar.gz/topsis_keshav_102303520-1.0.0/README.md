# TOPSIS Python Package

This package implements the TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) method.

## Installation
pip install topsis-keshav-102303520


## Usage
topsis <input_file.csv> <weights> <impacts> <output_file.csv>


### Example
topsis data.csv "1,1,1,1" "+,+,+,+" output.csv


## Input Format
- First column: Object names
- Remaining columns: Numeric criteria

## Output
- Adds Topsis Score
- Adds Rank