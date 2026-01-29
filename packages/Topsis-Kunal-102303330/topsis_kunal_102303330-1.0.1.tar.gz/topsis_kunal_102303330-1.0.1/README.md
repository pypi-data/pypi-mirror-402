# Topsis-Kunal-102303330

This project is a **Python Command Line Implementation of TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)**.

It allows you to rank alternatives based on multiple criteria using **weights and impacts** provided by the user.

---

### Installation:

```bash
pip install topsis-102303330
```

---

## 🚀 Features

- Works with both `.csv` and `.xlsx` files
- Command-line based (as required)
- Performs all validation checks
- Handles file errors and invalid input
- Implements full TOPSIS mathematical procedure
- Outputs ranked result file with **Topsis Score** and **Rank**

---

## What is TOPSIS?

TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) is a **multi-criteria decision-making (MCDM)** method.

> The best alternative is the one that is:

- Closest to the **ideal best solution**
- Farthest from the **ideal worst solution**

---

## 📂 Input File Format

Your input file must be either:

- `.csv` OR
- `.xlsx`

### Format:

| Alternative | C1   | C2   | C3  | C4   | C5    |
| ----------- | ---- | ---- | --- | ---- | ----- |
| A1          | 0.67 | 0.45 | 6.5 | 42.6 | 12.56 |
| A2          | 0.60 | 0.36 | 3.6 | 53.3 | 14.47 |
| A3          | 0.82 | 0.67 | 3.8 | 63.1 | 17.1  |

⚠️ First column = Name/ID  
⚠️ From second column onwards = Only numeric values

---

## 🖥️ How to Run

### 🔹 Syntax:

```bash
python topsis.py <InputFile> <Weights> <Impacts> <OutputFile>
```

Output File Structure:
| Alternative | C1 | C2 | C3 | C4 | C5 | Topsis Score | Rank |
| ----------- | --- | --- | --- | --- | --- | ------------ | ---- |
| A1 | ... | ... | ... | ... | ... | 0.645 | 2 |
| A2 | ... | ... | ... | ... | ... | 0.782 | 1 |
| A3 | ... | ... | ... | ... | ... | 0.432 | 3 |

## 👨‍💻 Author

### Kunal Sharma

B.Tech Student | Machine Learning & Full Stack Developer
