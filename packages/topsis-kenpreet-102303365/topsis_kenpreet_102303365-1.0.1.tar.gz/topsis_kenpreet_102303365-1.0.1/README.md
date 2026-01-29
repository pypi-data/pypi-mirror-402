# TOPSIS Python Package

This package implements the TOPSIS  method as a command-line tool.

TOPSIS is a multi-criteria decision-making technique used to rank alternatives based on their distance from an ideal best and an ideal worst solution.

---

# Installation

Install the package from PyPI using:

```bash
pip install topsis-kenpreet-102303365

# Usage
topsis <input_file.csv> "<weights>" "<impacts>" <output_file.csv>
# Example
topsis data.csv "1,1,1,1,1" "+,+,-,+,+" result.csv

