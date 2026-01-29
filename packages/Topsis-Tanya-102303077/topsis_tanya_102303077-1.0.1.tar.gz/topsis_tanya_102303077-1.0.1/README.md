````md
# Topsis-Tanya-102303077

## Project Description

**For:** Project-1 (UCS654 – Predictive Analytics)  
**Submitted by:** Tanya Mediratta
**Roll Number:** 102303077  

**Topsis-Tanya-102303077** is a Python package developed to solve **Multiple Criteria Decision Making (MCDM)** problems using the **Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS)** method.

The package ranks multiple alternatives based on their relative closeness to the ideal best and ideal worst solutions. It is implemented as a **command-line tool**, making it easy to use for practical and academic decision-making problems.

---

## Installation

Install the package using `pip`:

```bash
pip install Topsis-Tanya-102303077
````

---

## Usage

Run the package from the command line by providing:

* Input CSV file
* Weights vector
* Impacts vector
* Output file name

```bash
topsis data.csv "1,1,1,2" "+,-,-,+" result.csv
```

If weights or impacts contain spaces, they must be enclosed within double quotes (`" "`).

---

## Input Format

* Input file must be in **CSV format**
* First column contains the **names of alternatives**
* Remaining columns contain **numeric criteria values**
* Minimum of **three columns** is required
* Categorical values are not allowed in criteria columns

---

## Example

### Sample Input File (`data.csv`)

```csv
Fund Name,P1,P2,P3,P4
M1,0.67,0.45,6.5,42.6
M2,0.60,0.36,3.6,53.3
M3,0.82,0.67,3.8,63.1
M4,0.60,0.36,3.5,69.2
M5,0.76,0.58,4.8,43.0
```

### Command

```bash
topsis data.csv "1,1,1,2" "+,-,-,+" result.csv
```

---

## Output

The output CSV file contains:

* Original input data
* **TOPSIS Score** for each alternative
* **Rank** of each alternative based on the TOPSIS score
  (Higher score indicates a better rank)

---

## Features

* Command-line based execution
* Supports user-defined weights and impacts
* Input validation with clear error messages
* Ranks alternatives using TOPSIS methodology
* Outputs results in CSV format

---

## Notes

* Number of weights must match the number of criteria
* Number of impacts must match the number of criteria
* Impacts must be either `+` or `-`
* Criteria columns must contain numeric values only

---

## License

MIT License



