# TOPSIS Python Package

This package implements the Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS).

## Installation
pip install Topsis-Sana-10231010

## Usage
topsis <InputFile> <Weights> <Impacts> <OutputFile>

### Example
topsis data.csv "1,1,1,2" "+,+,-,+" output.csv

## Input Format
- CSV file with at least 3 columns
- First column: Alternatives
- Remaining columns: Numeric criteria

## Output
- CSV file with TOPSIS Score and Rank
