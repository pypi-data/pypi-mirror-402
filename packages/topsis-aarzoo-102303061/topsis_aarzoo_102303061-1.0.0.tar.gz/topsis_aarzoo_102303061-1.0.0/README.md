Project Description 
Submitted by: Aarzoo  
Roll Number: 102303061  

This is a Python package that solves Multiple Criteria Decision Making (MCDM) problems using the Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS).  
It ranks alternatives based on their closeness to the ideal best and ideal worst solutions.

Installation

Install the package using pip:

pip install topsis-aarzoo-102303061

Usage

Provide the input CSV file followed by the weights vector and impacts vector.

python <program.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>

Example:

python topsis.py data.csv "1,1,1,2" "+,+,-,+" output-result.csv

Input

- CSV file
- First column contains alternatives
- Remaining columns contain numeric criteria values
- Number of weights and impacts must match the number of criteria

Output

- CSV file with two additional columns:
  - Topsis Score
  - Rank

Notes

- Input CSV should not contain categorical values
- Weights and impacts must be correctly specified

License

MIT
