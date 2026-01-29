# Topsis-Bhavuk-102303140

A Python package for solving **Multiple Criteria Decision Making (MCDM)** problems using  
**TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)**.

---

## Project Information

**For:** Project-1 (UCS633)  
**Submitted by:** Bhavuk Mahajan 
**Roll No:** 102303140 

---

## Installation

Use the package manager `pip` to install the package.

```bash
pip install Topsis-Bhavuk-102303140
```

## Usage

Enter csv filename followed by `.csv` extension, then enter the **weights vector**
with values separated by commas, followed by the **impacts vector** with comma
separated signs (+,-).

```bash
topsis sample.csv "1,1,1,1" "+,-,+,+"
```


or vectors can be entered without quotes:
```bash
topsis sample.csv 1,1,1,1 +,-,+,+
```

To view usage help:
```bash
topsis /h
```
## Example
sample.csv

A CSV file showing data for different mobile handsets having varying features.

| Model | Storage (GB) | Camera (MP) | Price ($) | Looks (out of 5) |
|------|--------------|-------------|-----------|-----------------|
| M1 | 16 | 12 | 250 | 5 |
| M2 | 16 | 8 | 200 | 3 |
| M3 | 32 | 16 | 300 | 4 |
| M4 | 32 | 8 | 275 | 4 |
| M5 | 16 | 16 | 225 | 2 |


**Weights vector**

0.25,0.25,0.25,0.25


**Impacts vector**

+,+,-,+

## Input
```bash
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+"
```


## Output

TOPSIS RESULTS
-------------------------

| P-Score  | Rank |
|----------|------|
| 0.691632 | 1 |
| 0.534737 | 2 |
| 0.534277 | 3 |
| 0.401046 | 4 |
| 0.308368 | 5 |


## Other Notes

The first column and first row are removed before processing.

CSV file must contain only numerical values.

No categorical values are allowed.

## License

MIT License