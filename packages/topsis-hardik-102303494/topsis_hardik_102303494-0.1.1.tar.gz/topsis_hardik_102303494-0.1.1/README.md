# topsis-hardik-102303494

## Project Description

**topsis-hardik-102303494** is a Python library for solving **Multiple Criteria Decision Making (MCDM)** problems using the  
**Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS)**.

This project has been developed as part of **Project-1 (UCS654)**  
and demonstrates how TOPSIS can be implemented as a **command-line Python package** and distributed via **PyPI**.

---

## Student Details

- **Name:** Hardik  
- **Roll Number:** 102303494  
- **Course:** UCS654  
- **Project:** Project-1 (TOPSIS)

---

## Installation
Install the package using `pip`:
```bash
pip install topsis-hardik-102303494
```

# TOPSIS CLI Usage

## Command Format
```bash
topsis <input_file.csv> <weights> <impacts> <output_file.csv>
```

## Parameters
- **input_file.csv**: CSV file with dataset (first column: names, remaining: numeric criteria)
- **weights**: Comma-separated numeric weights (use quotes if needed)
- **impacts**: Comma-separated impacts (`+` for benefit, `-` for cost)
- **output_file.csv**: CSV file for results

## Example

### Input (sample.csv)

| Model | Storage (GB) | Camera (MP) | Price ($) | Looks |
|-------|--------------|-------------|-----------|-------|
| M1    | 16           | 12          | 250       | 5     |
| M2    | 16           | 8           | 200       | 3     |
| M3    | 32           | 16          | 300       | 4     |
| M4    | 32           | 8           | 275       | 4     |
| M5    | 16           | 16          | 225       | 2     |

### Command
```bash
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+" output.csv
```

### Output

| Model | Topsis Score | Rank |
|-------|--------------|------|
| M1    | 0.534277     | 3    |
| M2    | 0.308368     | 5    |
| M3    | 0.691632     | 1    |
| M4    | 0.534737     | 2    |
| M5    | 0.401046     | 4    |

*Rank 1 = Best Alternative*
