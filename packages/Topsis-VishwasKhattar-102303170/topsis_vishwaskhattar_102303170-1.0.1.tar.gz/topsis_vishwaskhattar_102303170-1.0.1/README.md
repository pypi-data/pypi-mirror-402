# TOPSIS Command Line Tool

This project is a Python implementation of the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** method.  
TOPSIS is a popular multi-criteria decision-making technique used to rank alternatives based on their distance from an ideal best and an ideal worst solution.

This tool is implemented as a **command-line utility** and can be installed directly using `pip`.

---

## Why TOPSIS?

In many real-world problems, decisions depend on multiple criteria.  
For example:
- Choosing the best mobile phone based on price, battery, and camera
- Selecting a fund based on risk, return, and stability
- Ranking suppliers based on cost, quality, and delivery time

TOPSIS helps by:
- Normalizing different criteria
- Applying user-defined weights
- Ranking alternatives objectively

---

## Installation

You can install the package from PyPI using:

```bash
pip install Topsis-VishwasKhattar-102303170


How to Use (After Installation)
Once installed, the TOPSIS tool can be executed directly from the command line.

Command Format:
topsis <InputDataFile> <Weights> <Impacts> <OutputFile>


Input Details
1. Input CSV File

The input file must be a CSV file
The first column should contain names of alternatives
All remaining columns must contain numeric values only

Example input file (data.csv):
Phone,Price,Battery,Camera
A,20000,4000,48
B,25000,5000,64
C,18000,4500,50



2. Weights
Weights define the importance of each criterion.
"1,1,2"


Meaning:
Price → weight 1
Battery → weight 1
Camera → weight 2 (more important)


3. Impacts
Impacts define whether a criterion is beneficial or non-beneficial.
+ → Higher value is better
- → Lower value is better

Example:
"- , + , +"

Meaning:
Price → lower is better
Battery → higher is better
Camera → higher is better

Complete Example
topsis data.csv "1,1,2" "-,+,+" output.csv


This command:
Reads data from data.csv
Applies the given weights
Uses the specified impacts
Calculates TOPSIS scores
Ranks the alternatives
Saves the result in output.csv



Output File
The output is a CSV file containing:
All original input columns
A new column Topsis Score
A new column Rank


Example output format:
Phone,Price,Battery,Camera,Topsis Score,Rank
A,20000,4000,48,0.42,2
B,25000,5000,64,0.78,1
C,18000,4500,50,0.36,3


Higher Topsis Score means a better alternative
Rank 1 represents the best choice


Error Handling:
The program performs input validation and raises errors if:
Input file is missing
Criteria columns contain non-numeric values
Number of weights does not match criteria
Number of impacts does not match criteria
Invalid impact symbols are provided



Implementation Details:
Vector normalization is used
Weighted normalized decision matrix is computed
Euclidean distance is used for distance calculation
Ranking is based on relative closeness to the ideal solution



