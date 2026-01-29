**Topsis-Trishti-102313056**

**For:** Project-1 (UCS654)
**Submitted by:** Trishti
**Roll No:** 102313056
**Group:** 3C33

**Topsis-Trishti-10155792** is a Python library designed to solve **Multiple Criteria Decision Making (MCDM)** problems using the **Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS)** method.

The package helps users rank alternatives based on multiple quantitative criteria by calculating their closeness to the ideal best and ideal worst solutions. It is implemented as a **command-line tool**, making it easy to use for academic and real-world decision-making problems.

## Installation

The package can be installed using the Python package manager **pip**.

```bash
pip install Topsis-Trishti-10155792
```

## Usage

Provide the input CSV file name, followed by the **weights vector** and the **impacts vector**.

```bash
topsis input.csv "1,1,1,1" "+,+,-,+"
```

Alternatively, vectors can be passed without quotes:

```bash
topsis input.csv 1,1,1,1 +,+,-,+
```

**Note:**
If the vectors contain spaces, they **must** be enclosed within double quotes `" "`.

To view help instructions, use:

```bash
topsis /h
```

## Example

### Input File: `sample.csv`

A CSV file containing data for different mobile handsets with multiple attributes.

| Model | Storage (GB) | Camera (MP) | Price ($) | Looks (out of 5) |
| ----- | ------------ | ----------- | --------- | ---------------- |
| M1    | 16           | 12          | 250       | 5                |
| M2    | 16           | 8           | 200       | 3                |
| M3    | 32           | 16          | 300       | 4                |
| M4    | 32           | 8           | 275       | 4                |
| M5    | 16           | 16          | 225       | 2                |

**Weights Vector:**

```
[0.25, 0.25, 0.25, 0.25]
```

**Impacts Vector:**

```
[+, +, -, +]
```

### Command

```bash
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+"
```


## Output

```
        TOPSIS RESULTS
-----------------------------
   Topsis Score   Rank
1     0.534277      3
2     0.308368      5
3     0.691632      1
4     0.534737      2
5     0.401046      4
```

The output file contains the **TOPSIS score** and **rank** for each alternative.

---

## Important Notes

* The first column (identifiers) and the header row are ignored during computation.
* The CSV file must contain **only numerical values** (no categorical data).
* The number of weights and impacts must match the number of criteria.
* Impacts must be either `+` (benefit) or `-` (cost).

---

