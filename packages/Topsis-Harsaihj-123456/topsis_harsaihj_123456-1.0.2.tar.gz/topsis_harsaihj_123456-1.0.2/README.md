
# Topsis-Harsaihaj-123456

A Python package for solving **Multiple Criteria Decision Making (MCDM)** problems
using **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)**.

This package is developed as part of UCS654 coursework.

---

## Installation
```bash
pip install Topsis-Harsaihaj-123456
```

---

## Usage

```bash
topsis sample.csv "1,1,1,1" "+,-,+,+" output.csv
```

- Weights and impacts must be comma-separated
- Impacts must be `+` or `-`

---

## Input File Format

| Model | C1 | C2 | C3 | C4 |
|------|----|----|----|----|
| A1   | 250 | 16 | 12 | 5 |
| A2   | 200 | 16 | 8  | 3 |

- First column: identifier
- Remaining columns: numeric

---

## Output

Adds:
- **Topsis Score**
- **Rank**

---

## Example

```bash
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+" result.csv
```

---

## Author
Harsaihaj Singh

## License
MIT
