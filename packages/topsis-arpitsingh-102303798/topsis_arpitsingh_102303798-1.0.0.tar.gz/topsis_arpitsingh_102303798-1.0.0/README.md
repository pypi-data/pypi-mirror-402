# TOPSIS-ArpitSingh-102303798

This package provides a command-line implementation of the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** method for multi-criteria decision making.

## Installation
```bash
pip install Topsis-ArpitSingh-102303798
````

## Usage

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

### Example

```bash
topsis data.csv "1,1,1,1,1" "+,+,-,+,-" output.csv
```

## Input File Format

* First column: Alternative / Object name
* Remaining columns: Numeric criteria values
* Minimum 3 columns required

## Weights

* Numeric
* Comma separated
* Count must match number of criteria

## Impacts

* `+` for benefit criteria
* `-` for cost criteria
* Comma separated
* Count must match number of criteria

## Output

* Adds two columns:

  * Topsis Score
  * Rank

## Dependencies

* pandas
* numpy