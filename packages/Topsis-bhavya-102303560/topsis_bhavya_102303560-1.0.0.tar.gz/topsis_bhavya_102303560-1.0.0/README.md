# TOPSIS  
**BY:** Bhavya, <102303560>

TOPSIS stands for **Technique for Order of Preference by Similarity to Ideal Solution**.  
It is a **multi-criteria decision making (MCDM)** technique used to rank alternatives based on their distance from an ideal best and an ideal worst solution.

The main idea behind TOPSIS is that the best alternative should have the **minimum distance from the positive ideal solution** and the **maximum distance from the negative ideal solution**.

This package provides a **Python implementation of the TOPSIS algorithm**, allowing users to apply it easily on real-world datasets through the command line.

---

## Installation – User Manual

**Topsis-bhavya-<102303560>** requires **Python 3** to run.

### Dependencies  
The following Python libraries are used:
- `pandas`
- `numpy`

These dependencies are automatically installed with the package.

---

## Package Installation

The package is available on **PyPI**:
https://pypi.org/project/Topsis-bhavya-<102303560>/


Install the package using the following command:


pip install Topsis-bhavya-<102303560>

---

## Usage

After installation, open the command prompt / terminal and run:

python topsis <input_file> <weights> <impacts> <output_file>

Example
topsis sample.csv "1,1,1,1" "+,+,-,+" result.csv
