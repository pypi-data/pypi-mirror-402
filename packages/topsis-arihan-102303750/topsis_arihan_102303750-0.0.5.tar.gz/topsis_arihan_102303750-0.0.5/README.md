# USER MANUAL  
## TOPSIS – Arihan (102303750)

---

## 1. Overview

`topsis-arihan-102303750` is a Python command-line tool that implements the  
**Technique for Order Preference by Similarity to Ideal Solution (TOPSIS)**.

TOPSIS is a **Multi-Criteria Decision Making (MCDM)** technique used to rank a set of alternatives based on multiple evaluation criteria.  
The alternative closest to the ideal best solution and farthest from the ideal worst solution is ranked highest.

---

## 2. System Requirements

- Python version **3.7 or higher**
- Operating System: Windows / macOS / Linux
- Python packages: `numpy`, `pandas`

---

## 3. Installation

Install the package from PyPI using `pip`:

```bash
pip install topsis-arihan-102303750
```
After installation, the command topsis becomes available in the terminal.

## 4. Command-Line Usage

### 4.1 General Syntax
Enter CSV filename followed by .csv extension, then enter the weights vector with vector values separated by commas, followed by the impacts vector with comma separated signs (+,-)

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputFile>
```
## Example

```bash
topsis data.csv "1,1,1,1,2" "+,+,-,+,+" output.csv
```
### 4.2 Description of Parameters

**InputDataFile**  
CSV file containing the alternatives and criteria.

**Weights**  
Comma-separated numeric values representing the importance of each criterion.

**Impacts**  
Comma-separated symbols indicating the nature of each criterion:  
`+` → Benefit criterion (higher value is better)  
`-` → Cost criterion (lower value is better)

**OutputFile**  
Name of the CSV file where results will be saved.

---

## 5. Example Usage

### 5.1 Input File (`data.csv`)

```csv
Fund Name,P1,P2,P3,P4,P5
M1,0.84,0.71,6.7,42.1,12.59
M2,0.91,0.83,7.0,31.7,10.11
M3,0.79,0.62,4.8,46.7,13.23
M4,0.78,0.61,6.4,42.4,12.55
M5,0.94,0.88,3.6,62.2,16.91
M6,0.88,0.77,6.5,51.5,14.91
M7,0.66,0.44,5.3,48.9,13.83
M8,0.93,0.86,3.4,37.0,10.55
```

The first column is treated as an identifier (Fund Name).  
All remaining columns must contain numeric criteria.

---

### 5.2 Weights and Impacts Used

Weights:  
`1,1,1,1,2`

Impacts:  
`+,+,-,+,+`

---

### 5.3 Command Executed

```bash
topsis data.csv "1,1,1,1,2" "+,+,-,+,+" output.csv
```

---

## 6. Output Description

The output file contains:
- Original data
- Topsis Score (closeness coefficient)
- Rank (1 indicates the best alternative)

### 6.1 Output File (`output.csv`)

```csv
Fund Name,P1,P2,P3,P4,P5,Topsis Score,Rank
M1,0.84,0.71,6.7,42.1,12.59,0.38,6
M2,0.91,0.83,7.0,31.7,10.11,0.31,8
M3,0.79,0.62,4.8,46.7,13.23,0.48,3
M4,0.78,0.61,6.4,42.4,12.55,0.34,7
M5,0.94,0.88,3.6,62.2,16.91,0.98,1
M6,0.88,0.77,6.5,51.5,14.91,0.59,2
M7,0.66,0.44,5.3,48.9,13.83,0.44,5
M8,0.93,0.86,3.4,37.0,10.55,0.46,4
```
## 7. Assumptions and Constraints

- Input CSV must contain only numeric values after the first column.
- Number of weights and impacts must match the number of criteria.
- Higher TOPSIS score implies better ranking.
- Missing or categorical values are not supported.

---

## 8. Error Handling

The program performs validation and displays appropriate error messages for:
- Incorrect number of command-line arguments.
- File not found.
- Non-numeric values in criteria columns.
- Mismatch in number of criteria, weights, and impacts.
- Invalid impact symbols (only `+` and `-` allowed).
