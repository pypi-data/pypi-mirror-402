## TOPSIS Implementation

---

## Overview

This Python package provides a clear and practical implementation of the **TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)** method for **Multi-Criteria Decision Making (MCDM)**.

Using this package, users can rank multiple alternatives based on several numerical criteria by assigning **weights** and **impacts** (benefit or cost) to each criterion. The package is designed as a **command-line tool** and works directly with CSV files.

---

## Project Information

| Field | Details |
|-----|--------|
| Course | Project-1 |
| Author | Nimish Agrawal |
| Roll No | 102483077 |
| Group | 3C34 |

---

## Features

- Easy-to-use command-line interface  
- Supports customizable weights and impacts  
- Handles benefit (`+`) and cost (`-`) criteria  
- Accepts CSV input and produces CSV output  
- Automatically computes TOPSIS score and rank  

---

## Installation

Use the Python package manager `pip` to install the package:

```bash
pip install Topsis-Nimish-102483077
```

```bash
topsis <input_file.csv> <weights> <impacts>
```

## Arguments

| Argument           |Description                                                                                                              |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| `<input_file.csv>` | Path to CSV file. First column must contain alternative names. Remaining columns must contain numerical criteria values. |
| `<weights>`        | Comma-separated weights for each criterion (example: `0.2,0.2,0.2,0.2,0.2`).                                             |
| `<impacts>`        | Comma-separated impacts for each criterion (`+` for benefit, `-` for cost).                                              |


## Example

The following dataset evaluates different investment funds based on five parameters.

| Fund | P1   | P2   | P3  | P4   | P5    |
| ---- | ---- | ---- | --- | ---- | ----- |
| M1   | 0.74 | 0.55 | 3.1 | 64.7 | 17.27 |
| M2   | 0.66 | 0.44 | 4.3 | 60.0 | 16.35 |
| M3   | 0.62 | 0.38 | 3.9 | 46.1 | 12.75 |
| M4   | 0.83 | 0.69 | 4.9 | 33.0 | 9.86  |
| M5   | 0.75 | 0.56 | 5.6 | 40.8 | 11.93 |
| M6   | 0.87 | 0.76 | 6.6 | 38.8 | 11.76 |
| M7   | 0.88 | 0.77 | 6.5 | 36.5 | 11.16 |
| M8   | 0.78 | 0.61 | 6.7 | 35.9 | 11.00 |

Weights and Impacts

Weights

0.2,0.2,0.2,0.2,0.2


Impacts

+,+,+,-,-

## Execution Command

```bash
topsis data.csv "0.2,0.2,0.2,0.2,0.2" "+,+,+,-,-"
```

## Output

The output file (output.csv) contains the original data along with two additional columns.

| Fund | P1 | P2 | P3 | P4 | P5 | Topsis Score | Rank |
| ---- | -- | -- | -- | -- | -- | ------------ | ---- |
| M1   | …  | …  | …  | …  | …  | 0.5123       | 6    |
| M2   | …  | …  | …  | …  | …  | 0.4786       | 8    |
| M3   | …  | …  | …  | …  | …  | 0.5639       | 5    |
| M4   | …  | …  | …  | …  | …  | 0.7214       | 1    |
| M5   | …  | …  | …  | …  | …  | 0.6042       | 4    |
| M6   | …  | …  | …  | …  | …  | 0.6897       | 2    |
| M7   | …  | …  | …  | …  | …  | 0.6588       | 3    |
| M8   | …  | …  | …  | …  | …  | 0.4951       | 7    |


Output Columns
| Column       | Meaning                               |
| ------------ | ------------------------------------- |
| Topsis Score | Calculated TOPSIS performance score   |
| Rank         | Rank based on TOPSIS score (1 = best) |


## Input File Requirements
- Input file must be a valid CSV  
- First column must contain alternative names  
- All remaining columns must contain numerical values  
- No categorical or missing values allowed 


## Error Handling

The package validates inputs and raises errors for:

- Mismatch between the number of criteria and weights  
- Mismatch between the number of criteria and impacts  
- Invalid impact values (only `+` or `-` allowed)  
- Incorrect CSV structure  

## License

This project is licensed under the **MIT License**.  
See the [LICENSE](https://opensource.org/licenses/MIT) file for details.

## Contact
For questions or feedback, please contact:
Nimish Agrawal
📧 nimish4agrawal@gmail.com