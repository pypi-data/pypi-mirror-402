# TOPSIS Python Package

This package implements the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** method.

## Installation

```bash
pip install topsis-ishwin-101303644
```

## Usage

```bash
topsis data.xlsx "1,1,1,2,1" "+,+,-,+,+" output.xlsx
```

## Input Format

* First column: Alternatives
* Remaining columns: Numeric criteria

## Output

* Adds **Topsis Score**
* Adds **Rank**

## Example

```bash
topsis sample.xlsx "1,1,1,2,1" "+,+,-,+,+" result.xlsx
```

## Author

Ishwin
