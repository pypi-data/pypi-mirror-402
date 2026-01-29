### By Harsaihaj Singh (Roll No: 102303957)

This Python package implements the TOPSIS (Technique for Order Preference by
Similarity to Ideal Solution) method for solving Multi-Criteria Decision Making problems.

---

## Installation

pip install Topsis-Harsaihaj-102303957

---

## Input File Format

First column: Alternatives  
Remaining columns: Numeric criteria

Example CSV:

| Device | Battery | Performance | Cost | Weight |
|--------|---------|-------------|------|--------|
| D1 | 4000 | 7 | 300 | 1.8 |
| D2 | 4500 | 6 | 280 | 2.0 |
| D3 | 4200 | 8 | 350 | 1.9 |
| D4 | 3800 | 5 | 260 | 1.7 |
| D5 | 4600 | 7 | 310 | 2.1 |

---

## Weights and Impacts

Weights vector:
0.25,0.25,0.25,0.25

Impacts vector:
+,+,-,-

---

## Command Line Usage

topsis <inputfile> <weights> <impacts> <outputfile>

Example:

topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,-" result.csv

---

## Output File Example

Result CSV will contain Topsis Score and Rank:

| Device | Score | Rank |
|--------|--------|------|
| D1 | 0.562 | 2 |
| D2 | 0.431 | 4 |
| D3 | 0.688 | 1 |
| D4 | 0.317 | 5 |
| D5 | 0.501 | 3 |

Higher score means better alternative.

---

## Error Handling

Program validates:

File existence  
Numeric values  
Correct weights count  
Correct impacts  
Invalid symbols

---

## Conclusion

TOPSIS helps rank alternatives based on multiple criteria and is useful in
decision-making problems.
