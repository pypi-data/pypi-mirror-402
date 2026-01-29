# Topsis-Gurshaan-Bajwa-102303264

### By Gurshaan Bajwa (Roll No: 102303264)

This Python package implements the TOPSIS (Technique for Order Preference by
Similarity to Ideal Solution) method for solving Multi-Criteria Decision Making (MCDM) problems.

---

## Installation

```bash
pip install Topsis-Gurshaan-Bajwa-102303264
```

---

## Input File Format

First column: Alternatives  
Remaining columns: Numeric criteria

Example CSV:

| Model | Storage | Camera | Price | Looks |
|--------|--------|--------|--------|--------|
| M1 | 16 | 12 | 250 | 5 |
| M2 | 16 | 8 | 200 | 3 |
| M3 | 32 | 16 | 300 | 4 |
| M4 | 32 | 8 | 275 | 4 |
| M5 | 16 | 16 | 225 | 2 |

---

## Weights and Impacts

Weights vector:
```
0.25,0.25,0.25,0.25
```

Impacts vector:
```
+,+,-,+
```

---

## Command Line Usage

```
topsis <inputfile> <weights> <impacts> <outputfile>
```

Example:

```bash
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+" result.csv
```

---

## Output File Example

Result CSV will contain Topsis Score and Rank:

| Model | Score | Rank |
|--------|--------|------|
| M1 | 0.534 | 3 |
| M2 | 0.308 | 5 |
| M3 | 0.692 | 1 |
| M4 | 0.535 | 2 |
| M5 | 0.401 | 4 |

Higher score means better alternative.

---

## Error Handling

Program validates:

- File existence  
- Numeric values  
- Correct weights count  
- Correct impacts  
- Invalid symbols  

---

## Conclusion

TOPSIS helps rank alternatives based on multiple criteria and is useful in
decision-making problems.
