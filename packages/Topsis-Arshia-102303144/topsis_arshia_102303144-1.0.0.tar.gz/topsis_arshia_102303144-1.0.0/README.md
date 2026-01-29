# Topsis-Arshia-102303144

## Project Description
**Topsis-Arshia-102303144** is a Python package for solving Multiple Criteria Decision Making (MCDM) problems using the **Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS)**.

TOPSIS ranks alternatives based on their distance from an ideal best and an ideal worst solution. This package provides a simple command-line interface to perform TOPSIS analysis on CSV data files.

---

## Course & Student Details
**Course:** Project-1 (UCS654)  
**Submitted by:** Arshia Anand  
**Roll No:** 102303144  
**Group:** 3C15  

---

## Installation
Install via PyPI using pip:

```bash
pip install Topsis-Arshia-102303144
```
## Usage

Run the TOPSIS analysis using:

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

## Arguments

InputDataFile: CSV file containing the dataset

Weights: Comma-separated numeric weights for each criterion

Impacts: Comma-separated impacts (+ for benefit, - for cost)

OutputResultFileName: Output CSV file containing TOPSIS scores and ranks

## Example
```bash
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+" result.csv
```

## Sample Input File (sample.csv)
```csv
Model,Storage,Camera,Price,Looks
M1,16,12,250,5
M2,16,8,200,3
M3,32,16,300,4
M4,32,8,275,4
M5,16,16,225,2
```

## Sample Output
```txt
Topsis Score  Rank
0.691632      1
0.534737      2
0.534277      3
0.401046      4
0.308368      5
```

## Important Notes

Input file must contain at least three columns

From the 2nd column to the last column, all values must be numeric

Number of weights must equal the number of impacts

Number of weights and impacts must match the number of criteria

Impacts must be either + (benefit) or - (cost)

Weights and impacts must be separated by commas (,)

## License

MIT License. See the LICENSE file for details.