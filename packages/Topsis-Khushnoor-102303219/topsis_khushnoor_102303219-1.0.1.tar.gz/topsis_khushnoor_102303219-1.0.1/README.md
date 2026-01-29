# TOPSIS-Khushnoor-102303219

**Project:** UCS654 – Project 1  
**Submitted by:** Khushnoor Kaur  
**Roll No:** 102303219  

TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) is a
multi-criteria decision-making (MCDM) method used to rank alternatives based on
their distance from the ideal best and ideal worst solutions.

---

## Installation

```bash
pip install topsis-khushnoor-102303219
```

## Usage

This package provides a command-line tool called topsis.
```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

Example
```bash
topsis sample.csv "1,1,1,2" "+,+,-,+" result.csv


## Input Format

The input file must be a CSV file with:
* First column as alternative names
* Remaining columns as numerical criteria

Sample Input (sample.csv)

| Model | Storage space | Camera | Price | Looks |
|-------|---------------|--------|-------|-------|
| M1    | 16            | 12     | 250   | 5     |
| M2    | 16            | 8      | 200   | 3     |
| M3    | 32            | 16     | 300   | 4     |

## Output

The output file will contain the original columns plus the Topsis Score and Rank.

| P-Score  | Rank |
|----------|------|
| 0.534277 | 2    |
| 0.308368 | 3    |
| 0.691632 | 1    |

## Other notes:

* The first column (alternatives) is ignored during TOPSIS computation.
* All criteria values must be numerical.
* Weights and impacts must match the number of criteria.
* Impacts must be either + (benefit) or - (cost).

## License:

[MIT](https://choosealicense.com/licenses/mit/)


