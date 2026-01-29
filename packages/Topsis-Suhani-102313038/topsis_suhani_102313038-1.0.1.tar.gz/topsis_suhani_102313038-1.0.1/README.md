# Topsis-Suhani-102313038

## Description
This package implements the Technique for Order Preference by Similarity to Ideal Solution (TOPSIS) for multi-criteria decision making.

## Installation
```bash
pip install Topsis-Suhani-102313038
```

## Usage
Enter csv file name with .csv extension, then enter weights (comma separated), followed by impacts '+' or '-' (comma separated), and csv file where result is to be stored.
```bash
python -m topsis_suhani_102313038.topsis input.csv "1,1,1,1" "+,-,+,+" output.csv
```

## Input Format
- CSV file with alternatives and criteria
- Weights must be comma-separated
- Impacts must be + or -

  ## Output
  - Topsis Score
  - Ranking

## License 
This project is licensed under the **MIT License**.
[License](../LICENSE)