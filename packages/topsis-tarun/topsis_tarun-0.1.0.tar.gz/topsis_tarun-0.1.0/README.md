# TOPSIS Command Line Assignment
# Submitted byt: Tarun Krishna Shastri / 102303315 / 3C23
##  Description
This project implements the **TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)** method as a **command-line Python program**, as required for the Data Science elective assignment.

---

##  Folder Structure
```
TOPSIS_Assignment/
│
├── topsis.py          # Main TOPSIS implementation
├── README.md          # Instructions to run the program
```

---

##  Requirements
- Python 3.x
- pandas
- numpy

Install dependencies using:
```
pip install pandas numpy
```

---

## ▶ How to Run (Command Line)

### General Syntax
```
python topsis.py <InputDataFile> <Weights> <Impacts> <OutputFileName>
```

### Example
```
python topsis.py data.csv "1,1,1,2" "+,+,-,+" output-result.csv
```

---

##  Input File Rules
- CSV file with **minimum 3 columns**
- First column: Alternatives (string)
- Remaining columns: Numeric criteria

---

##  Output File
- Contains all original columns
- Adds:
  - `Topsis Score`
  - `Rank` (1 = Best)

---

##  Error Handling
The program checks:
- Correct number of parameters
- File not found
- Minimum column count
- Numeric data validation
- Weight & impact consistency
- Valid impact symbols (+ / -)

---

##  Notes
- Weights and impacts **must be comma-separated**
- Impacts must be only `+` or `-`
- Ranking uses descending TOPSIS score

---

## 🎓 Author
Data Science Elective Assignment