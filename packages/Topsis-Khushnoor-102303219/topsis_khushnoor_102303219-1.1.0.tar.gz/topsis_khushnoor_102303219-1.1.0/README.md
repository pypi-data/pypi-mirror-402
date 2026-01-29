# TOPSIS-Khushnoor-102303219

*for: Project-1 (UCS654) submitted by: Khushnoor Kaur Roll no: 102303219*

TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) is a multi-criteria decision-making method used for ranking and selecting alternatives.

## Installation
```bash
pip install TOPSIS-Khushnoor-102303219

## Usage

Enter the CSV filename followed by the .csv extension, then enter the weights vector and the impacts vector (separated by commas).
```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>

Example: topsis sample.csv "1,1,1,2" "+,+,-,+" result.csv

## Sample Input (sample.csv)

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

* The first column and first row are removed by the library before processing.
* Ensure the CSV follows the format shown in sample.csv.
* Make sure the CSV does not contain categorical values.

## License:

[MIT](https://choosealicense.com/licenses/mit/)


