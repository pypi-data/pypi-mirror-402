# TOPSIS Ranking Tool  
### By Karanveer Singh (Roll No: 102303670)

This command-line tool applies the TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) method to rank alternatives based on multiple quantitative criteria.

---

## Installation

pip install Topsis-Karanveer-102303670

---

## Input Data Format

The input must be a CSV file with the following structure:

Column 1: Alternatives  
Column 2 onwards: Numerical criteria values

Example:

| City | AirQuality | Cost | Transport | Safety |
|------|------------|------|-----------|--------|
| C1 | 72 | 32000 | 7 | 8 |
| C2 | 88 | 47000 | 9 | 6 |
| C3 | 65 | 28000 | 6 | 9 |
| C4 | 80 | 36000 | 8 | 8 |

---

## Weights and Impacts

Weights (comma separated):

0.30,0.20,0.25,0.25

Impacts (comma separated):

+,-,+,+

---

## Usage

topsis <input_file.csv> <weights> <impacts> <output_file.csv>

Example:

topsis city.csv "0.30,0.20,0.25,0.25" "+,-,+,+" ranks.csv

---

## Output Format

The output CSV will contain:

City, Score, Rank

Example:

C1, 0.51, 3  
C2, 0.56, 2  
C3, 0.44, 4  
C4, 0.67, 1

Higher score means better rank.

---

## Error Handling

The program checks for:

Incorrect number of arguments  
Non-numeric values in criteria columns  
Invalid impact symbols (+ or - only)  
Incorrect CSV format

Appropriate error messages are displayed for invalid input.

---

## Conclusion

This tool helps in decision making by converting multiple evaluation criteria into a single composite score using the TOPSIS method.