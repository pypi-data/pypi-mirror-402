 # Topsis-manleen-102303599


## Overview
This project implements the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** algorithm as a Python package.

TOPSIS is a multi-criteria decision-making (MCDM) technique used to rank alternatives based on their distance from an ideal best and an ideal worst solution.

This package provides:
- A clean command-line interface (CLI)
- Input validation for weights and impacts
- CSV-based input and output handling
- Easy integration as a Python module

## Installation
The package can be installed locally using `pip`.

Ensure that Python (version 3.8 or higher) is installed on your system.

```powershell
pip install topsis-engine

## Usage

After installation, the TOPSIS package can be executed from the command line using Python's module interface.

### Command Syntax

```powershell
python -m topsis_engine.cli <input_file> <weights> <impacts> <output_file>

## Input Format

The input file must be a **CSV file** where:

- The **first column** contains the names/IDs of the alternatives.
- The remaining columns contain **numerical values** for each criterion.
- All criteria values must be **numeric**.
- There must be **at least two criteria**.

### Sample Input (`data.csv`)

| Fund Name | P1  | P2  | P3 | P4  | P5  |
|----------|-----|-----|----|-----|-----|
| M1       | 0.84| 0.71| 6.7| 42.1| 12.59 |
| M2       | 0.91| 0.83| 7.0| 31.7| 10.11 |
| M3       | 0.79| 0.62| 4.8| 46.7| 13.23 |

### Weights Format
- Comma-separated numeric values
- Number of weights **must match** number of criteria

Example:
1,1,1,1,1

### Impacts Format
- Comma-separated symbols
- Use `+` for beneficial criteria
- Use `-` for non-beneficial criteria

Example:
+,+,+,+,+


## Output Format

The output is generated as a **CSV file** containing the TOPSIS results.

### Output File Details
- All original columns from the input file are preserved
- Two additional columns are added:
  - **TOPSIS Score** – Relative closeness to the ideal solution
  - **Rank** – Ranking of alternatives (1 = best)

### Sample Output (`output.csv`)

| Fund Name | P1   | P2   | P3  | P4  | P5   | TOPSIS Score | Rank |
|----------|------|------|-----|-----|------|--------------|------|
| M2       | 0.91 | 0.83 | 7.0 | 31.7| 10.11| 0.742        | 1    |
| M1       | 0.84 | 0.71 | 6.7 | 42.1| 12.59| 0.615        | 2    |
| M3       | 0.79 | 0.62 | 4.8 | 46.7| 13.23| 0.402        | 3    |

### Interpretation
- Higher **TOPSIS Score** indicates a better alternative
- Rank is assigned in descending order of TOPSIS Score


## Project Structure
TOPSIS-ASSIGN/
│
├── topsis_engine/
│   ├── __init__.py        # Package initializer
│   ├── __main__.py        # Entry point for python -m execution
│   ├── cli.py             # Command-line interface logic
│   ├── engine.py          # Core TOPSIS algorithm implementation
│   └── validation.py     # Input validation (weights, impacts, CSV)
│
├── data.csv               # Sample input data
├── output.csv             # Generated output file
├── test_engine.py         # Unit tests for TOPSIS engine
├── setup.py               # Package setup configuration
├── README.md              # Project documentation
└── requirements.txt       # Project dependencies



### Description
- **topsis_engine/** contains the complete implementation of the TOPSIS package
- **cli.py** handles command-line arguments and execution
- **engine.py** performs normalization, weighting, scoring, and ranking
- **validation.py** ensures correctness of inputs before execution


## Algorithm Flow

The TOPSIS algorithm follows the steps shown below:

```mermaid
flowchart TD
    A[Start] --> B[Read CSV Input File]
    B --> C[Validate Inputs]
    C -->|Invalid| D[Throw Error & Exit]
    C -->|Valid| E[Normalize Decision Matrix]
    E --> F[Apply Weights]
    F --> G[Determine Ideal Best & Worst]
    G --> H[Calculate Separation Measures]
    H --> I[Compute TOPSIS Score]
    I --> J[Rank Alternatives]
    J --> K[Write Output CSV]
    K --> L[End]


## License

This project is licensed under the **MIT License**.

You are free to:
- Use the software for academic or commercial purposes
- Modify and distribute the code
- Include it in other projects


