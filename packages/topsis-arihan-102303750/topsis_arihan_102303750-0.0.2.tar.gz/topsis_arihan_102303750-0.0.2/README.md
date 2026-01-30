# TOPSIS – Arihan (102303750)

## Introduction
This Python package implements **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)**, a multi-criteria decision-making (MCDM) technique.  
TOPSIS is used to rank alternatives based on their distance from the ideal best and ideal worst solutions.

---

## Problem Statement
Given multiple alternatives and evaluation criteria, TOPSIS helps determine the best alternative by:
- Maximizing benefit criteria
- Minimizing cost criteria  

The alternative closest to the ideal solution is ranked highest.

---

## Installation
Install the package from PyPI using pip:

```bash
pip install topsis-arihan-102303750
```

## Usage
```bash
topsis data.csv "3,1,2,4" "+,-,+,+" output.csv
```
## Sample Input (`data.csv`)
```csv
Student,Marks,Attendance(%),Assignments,ProjectScore
S1,85,92,80,78
S2,78,88,85,82
S3,90,95,92,90
S4,72,80,75,70
S5,88,90,88,85
S6,65,75,70,68
S7,82,85,80,76
S8,95,98,96,94
S9,70,82,78,72
S10,86,89,84,81
```

## Sample Output (`output.csv`)
```csv
Student,Marks,Attendance(%),Assignments,ProjectScore,Topsis Score,Rank
S1,85,92,80,78,0.49,6
S2,78,88,85,82,0.50,5
S3,90,95,92,90,0.81,2
S4,72,80,75,70,0.19,9
S5,88,90,88,85,0.69,3
S6,65,75,70,68,0.13,10
S7,82,85,80,76,0.42,7
S8,95,98,96,94,0.87,1
S9,70,82,78,72,0.20,8
S10,86,89,84,81,0.57,4
```