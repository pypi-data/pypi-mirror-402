# TOPSIS - Python Package

**By:** Bhavya  
**Roll Number:** 102303560  
**Course:** UCS654 - Predictive Analytics using Statistics  

---

## Project Description

**TOPSIS** (Technique for Order of Preference by Similarity to Ideal Solution) is a
multi-criteria decision-making (MCDM) method used to rank alternatives based on
their distance from an ideal best and an ideal worst solution.

This Python package provides an easy-to-use command-line implementation of the
TOPSIS algorithm. It allows users to input a dataset along with weights and
impacts and produces a ranked output based on TOPSIS scores.

---

## Installation

Install the package using pip:

```bash
pip install Topsis-bhavya-102303560
```
---

## Usage

Run the following command:
python topsis <inputFile> <weights> <impacts> <outputFile>

Example: python topsis sample.csv "1,1,1,1" "+,+,-,+" result.csv

---

## Input File Format

- The input file must contain at least three columns.
- The first column should contain alternative names.
- All other columns must contain numeric values only.
- The number of weights and impacts must match the number of criteria.

### Sample Input File

| Model | Storage | Camera | Price | Looks |
| ----- | ------- | ------ | ----- | ----- |
| M1    | 16      | 12     | 250   | 5     |
| M2    | 16      | 8      | 200   | 3     |
| M3    | 32      | 16     | 300   | 4     |
| M4    | 32      | 8      | 275   | 4     |
| M5    | 16      | 16     | 225   | 2     |


## Output

The output file contains: 
- Topsis Score
- Rank

The alternative with Rank 1 is considered the best choice.
