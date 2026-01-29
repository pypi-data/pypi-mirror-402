# TOPSIS Package

A Python package implementing **TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)** for **Multi-Criteria Decision Making (MCDM)** analysis. Rank alternatives based on multiple numeric criteria with a simple command-line interface.

**Author:** Harshit Kansal (Roll No: 102303554)

---

## What is TOPSIS?

TOPSIS is a multi-criteria decision analysis method that ranks alternatives based on their geometric distance from ideal solutions. The best alternative should have:
- The **shortest distance** from the positive ideal solution
- The **longest distance** from the negative ideal solution

---

## Installation

Install the package from PyPI:

```bash
pip install topsis-harshit-kansal-102303554
```

---

## Quick Start

### CLI Usage

```bash
topsis-hk <input_csv> <weights> <impacts> <output_csv>
```

### Example Command

```bash
topsis-hk sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+" output.csv
```

---

## Input Format

### CSV File Structure

Your input CSV must have:
- **First column:** Alternative names/IDs
- **Remaining columns:** Numeric criteria values only

Example (`sample.csv`):

| Model | Storage | Camera | Price | Rating |
|-------|---------|--------|-------|--------|
| M1    | 16      | 12     | 250   | 5      |
| M2    | 16      | 8      | 200   | 3      |
| M3    | 32      | 16     | 300   | 4      |
| M4    | 32      | 8      | 275   | 4      |
| M5    | 16      | 16     | 225   | 2      |

### Weights Vector

Comma-separated numeric values indicating criterion importance:

```
"0.25,0.25,0.25,0.25"
```

### Impacts Vector

Comma-separated `+` or `-` values indicating if a criterion is beneficial (`+`) or non-beneficial (`-`):

```
"+,+,-,+"
```

- `+` : Higher is better (Storage, Camera, Rating)
- `-` : Lower is better (Price)

---

## Output

The output CSV contains all original columns plus two new columns:

| Column Name | Description |
|---|---|
| `Topsis Score (102303554)` | TOPSIS score for each alternative |
| `Rank (Harshit)` | Rank of each alternative (1 = best) |

### Sample Output

| Model | Storage | Camera | Price | Rating | Topsis Score (102303554) | Rank (Harshit) |
|-------|---------|--------|-------|--------|--------------------------|----------------|
| M1    | 16      | 12     | 250   | 5      | 0.7234                   | 2              |
| M2    | 16      | 8      | 200   | 3      | 0.4521                   | 5              |
| M3    | 32      | 16     | 300   | 4      | 0.6892                   | 3              |
| M4    | 32      | 8      | 275   | 4      | 0.5643                   | 4              |
| M5    | 16      | 16     | 225   | 2      | 0.8123                   | 1              |

---

## Validation Rules

The package enforces the following validations:

- Input file must be a valid CSV
- First column contains alternative names (non-numeric)
- All other columns contain numeric values only
- Number of weights must match number of criteria columns
- Number of impacts must match number of criteria columns
- Impact values must be either `+` or `-`
- Weights must be numeric and positive (> 0)

---

## Algorithm Steps

TOPSIS performs the following steps:

1. **Normalize** the decision matrix
2. **Weight** the normalized decision matrix
3. **Calculate** ideal best and ideal worst solutions
4. **Compute** Euclidean distances from each alternative to ideal solutions
5. **Calculate** TOPSIS score for each alternative
6. **Rank** alternatives in descending order of TOPSIS score

---

## Requirements

- Python >= 3.8
- numpy
- pandas

---

## Keywords

`TOPSIS` `MCDM` `Multi-Criteria Decision Making` `Decision Analysis` `Optimization` `Ranking`

---

## Author

**Harshit Kansal**  
Roll No: 102303554

---

## License

This package is part of a college assignment project.
