# Topsis-Avneet-102303289

**Name:** Avneet Sandhu  
**Roll No:** 102303289  
**Group:** 3C22  

---

## Project Description

This package implements the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** method as a **command-line tool**.

TOPSIS is a Multi-Criteria Decision Making (MCDM) technique used to rank alternatives based on their distance from the ideal best and ideal worst solutions. It helps in making optimal decisions when multiple conflicting criteria are involved.

This project is developed as part of the **Predictive Analytics assignment**.

---

## Installation

Install the package from PyPI:

```bash
pip install Topsis-Avneet-102303289
```

---

## Usage

After installing the package, run TOPSIS from the command line:

```bash
topsis <InputDataFile> <Weights> <Impacts> <ResultFileName>
```

### Arguments:

1. **InputDataFile**: Path to the input CSV file containing the decision matrix
2. **Weights**: Comma-separated numerical weights for each criterion (e.g., `1,1,1,1,1`)
3. **Impacts**: Comma-separated impacts for each criterion (`+` for beneficial, `-` for non-beneficial)
4. **ResultFileName**: Name of the output CSV file to store results

### Example Command:

```bash
topsis data.csv 1,1,1,1,1 -,+,+,+,+ output.csv
```

---

## Example Dataset

### Input File: `data.csv`

| Fund Name | P1   | P2   | P3  | P4   | P5    |
|-----------|------|------|-----|------|-------|
| M1        | 0.88 | 0.77 | 3.3 | 49.9 | 13.71 |
| M2        | 0.61 | 0.37 | 4.1 | 63.8 | 17.22 |
| M3        | 0.68 | 0.46 | 5.8 | 55.7 | 15.66 |
| M4        | 0.65 | 0.42 | 3.5 | 34.7 | 9.82  |
| M5        | 0.93 | 0.86 | 5.0 | 55.3 | 15.52 |
| M6        | 0.91 | 0.83 | 3.2 | 50.6 | 13.89 |
| M7        | 0.91 | 0.83 | 4.6 | 64.3 | 17.66 |
| M8        | 0.92 | 0.85 | 5.3 | 36.5 | 10.89 |

### Command:

```bash
topsis data.csv 0.2,0.2,0.2,0.2,0.2 -,+,+,+,+ output.csv
```

**Weights:** `0.2,0.2,0.2,0.2,0.2` (Equal importance to all criteria)  
**Impacts:** `-,+,+,+,+` (P1 is non-beneficial, P2-P5 are beneficial)

---

## Output

### Output File: `output.csv`

| Fund Name | P1   | P2   | P3  | P4   | P5    | Topsis Score | Rank |
|-----------|------|------|-----|------|-------|--------------|------|
| M1        | 0.88 | 0.77 | 3.3 | 49.9 | 13.71 | 0.475101     | 7    |
| M2        | 0.61 | 0.37 | 4.1 | 63.8 | 17.22 | 0.522999     | 4    |
| M3        | 0.68 | 0.46 | 5.8 | 55.7 | 15.66 | 0.588975     | 3    |
| M4        | 0.65 | 0.42 | 3.5 | 34.7 | 9.82  | 0.239258     | 8    |
| M5        | 0.93 | 0.86 | 5.0 | 55.3 | 15.52 | 0.668589     | 2    |
| M6        | 0.91 | 0.83 | 3.2 | 50.6 | 13.89 | 0.49709      | 6    |
| M7        | 0.91 | 0.83 | 4.6 | 64.3 | 17.66 | 0.700458     | 1    |
| M8        | 0.92 | 0.85 | 5.3 | 36.5 | 10.89 | 0.507755     | 5    |

### Result Summary:

- **Best Alternative:** M7 (Rank 1, Score: 0.700458)
- **Worst Alternative:** M4 (Rank 8, Score: 0.239258)

---

## Input File Requirements

- File must be in CSV format
- First column should contain object/alternative names
- Must have at least 3 columns (1 for names + 2 or more criteria)
- All criteria values must be numeric
- No missing values allowed

---

## How TOPSIS Works

1. **Normalization**: Convert the decision matrix to a normalized form
2. **Weighted Normalization**: Multiply normalized values by their respective weights
3. **Ideal Solutions**: Determine ideal best and ideal worst values for each criterion
4. **Distance Calculation**: Calculate Euclidean distance from ideal best and ideal worst
5. **Performance Score**: Calculate TOPSIS score using the formula:
   ```
   Score = Distance_from_worst / (Distance_from_best + Distance_from_worst)
   ```
6. **Ranking**: Rank alternatives based on their scores (higher is better)

---

## 🛡️ Error Handling

The package includes comprehensive validation:

- Correct number of command-line arguments
- Input file existence check
- CSV format validation
- Minimum column requirement (at least 3)
- Numeric data validation
- Weights and impacts count matching criteria count
- Impact values must be either `+` or `-`
- All weights must be positive numbers

---

## License

MIT License

---

## Author

**Avneet Sandhu**  
Roll No: 102303289  
Course: Predictive Analytics  
Group: 3C22

---

