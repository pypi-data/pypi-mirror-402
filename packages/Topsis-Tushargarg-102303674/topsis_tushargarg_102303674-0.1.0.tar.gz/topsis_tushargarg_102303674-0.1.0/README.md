# TOPSIS Package

## Installation
pip install Topsis-Tushargarg-102303674

## Usage
topsis <InputFile> <Weights> <Impacts> <OutputFile>

Example:
topsis data.csv "1,1,1,1,1" "+,+,-,+,+" result.csv

## Input Format
- First column: alternative name
- Remaining columns: numeric criteria

## Output
- Adds TOPSIS Score and Rank
