# TOPSIS-Harnoor-102303260

This package is a **Python-based command-line utility** that implements the **Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS)**. It helps users evaluate and rank multiple alternatives by comparing them across several quantitative criteria. By incorporating **user-specified weights and preference directions**, the tool calculates a **performance score** and assigns a **final rank** to each alternative.

---

## Installation

The package can be installed easily using `pip`:

```bash
pip install topsis-harnoor-102303260
```

---

## Usage Overview

The application is designed to be executed directly from the terminal. To run the analysis, you must provide:

- an input dataset (CSV or Excel),
- a list of weights,
- a list of impacts, and
- an output filename to store the results.

---

### Command Syntax

```bash
topsis <InputFile> <Weights> <Impacts> <OutputFile>
```

---

### Argument Explanation

1. **InputFile**
   - Location of the dataset file (`.csv` or `.xlsx`).
   - The file must contain **at least three columns**.
   - The **first column** represents the alternatives (such as Product IDs or Names) and is not included in calculations.
   - All subsequent columns should contain **numeric criterion values**.

2. **Weights**
   - A comma-separated sequence of numbers defining the importance of each criterion.
   - Example: `"3,2,1,4"`

3. **Impacts**
   - A comma-separated list of symbols (`+` or `-`) indicating preference direction:
     - `+` means higher values are better
     - `-` means lower values are better

4. **OutputFile**
   - The name of the CSV file where the computed scores and rankings will be saved.

---

## Example Walkthrough

Suppose we want to evaluate **five smartphones** based on **four criteria**: **Price**, **Camera Quality**, **Battery Capacity**, and **Storage**.

---

### 1. Input Dataset (`phones.csv`)

| Phone | Price | Camera | Battery | Storage |
| ----- | ----- | ------ | ------- | ------- |
| P1    | 500   | 8      | 4500    | 128     |
| P2    | 600   | 9      | 4800    | 256     |
| P3    | 450   | 7      | 4200    | 64      |
| P4    | 700   | 9      | 5000    | 256     |
| P5    | 550   | 8      | 4700    | 128     |

**Evaluation Criteria**:

- **Price** → Lower is better (`-`)
- **Camera Quality** → Higher is better (`+`)
- **Battery Capacity** → Higher is better (`+`)
- **Storage** → Higher is better (`+`)

---

### 2. Running the Analysis

Execute the following command:

```bash
topsis phones.csv "2,3,2,1" "-,+,+,+" results.csv
```

- Camera quality is given the highest priority.
- Price is treated as a cost criterion.

---

### 3. Output File (`results.csv`)

The output contains the original data along with two additional columns: **TOPSIS Score** and **Rank**.

| Phone | Price | Camera | Battery | Storage | TOPSIS Score | Rank |
| ----- | ----- | ------ | ------- | ------- | ------------ | ---- |
| P1    | 500   | 8      | 4500    | 128     | 0.548        | 3    |
| P2    | 600   | 9      | 4800    | 256     | 0.682        | 2    |
| P3    | 450   | 7      | 4200    | 64      | 0.401        | 5    |
| P4    | 700   | 9      | 5000    | 256     | 0.755        | 1    |
| P5    | 550   | 8      | 4700    | 128     | 0.612        | 4    |
