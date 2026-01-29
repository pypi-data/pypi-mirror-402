
# TOPSIS Implementation in Python

**Course:** UCS654 - Predictive Analytics using Statistics  
**Assignment:** Assignment-1 (TOPSIS)  
**Author:** Ishika
**Roll Number:** 102303460  

---

## About the Project

This repository contains a Python implementation of the  
**TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)** method.

TOPSIS is a **multi-criteria decision-making (MCDM)** technique used to rank multiple
alternatives based on their distance from the ideal best and ideal worst solutions.

---

## Installation - USER MANUAL
1. topsis-ishika-102303460 requires Python3 to run.
2. Other dependencies that come installed with this package are :-
    - pandas
    - numpy
3. Package listed on PyPI:- https://pypi.org/project/Topsis-Ishika-102303460/1.0.0/
4. Use the following command to install this package:-
    ```bash
    pip install Topsis-Ishika-102303460==1.0.0

---

## Usage
Run the following command in command prompt:
```bash
topsis <inputFile> <weights> <impacts> <outputFile>

```


Example:
```bash
topsis sample.csv "1,1,1,1" "+,+,-,+" result.csv
```
## Help

To view usage instructions:
```bash
topsis /h
```
## Example

### Input File: `sample.csv`

The input file contains data for different mobile handsets with multiple criteria.

| Model | Storage (GB) | Camera (MP) | Price ($) | Looks (out of 5) |
|------|--------------|-------------|-----------|------------------|
| M1   | 16           | 12          | 250       | 5                |
| M2   | 16           | 8           | 200       | 3                |
| M3   | 32           | 16          | 300       | 4                |
| M4   | 32           | 8           | 275       | 4                |
| M5   | 16           | 16          | 225       | 2                |

## Weights
```csharp
[0.25, 0.25, 0.25, 0.25]
```

## Impacts
```csharp
[+, +, -, +]
```

## Input Command
```bash
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+"
```
### Output

| Model | Topsis Score | Rank |
|------|-------------|------|
| M1   | 0.534277    | 3    |
| M2   | 0.308368    | 5    |
| M3   | 0.691632    | 1    |
| M4   | 0.534737    | 2    |
| M5   | 0.401046    | 4    |

