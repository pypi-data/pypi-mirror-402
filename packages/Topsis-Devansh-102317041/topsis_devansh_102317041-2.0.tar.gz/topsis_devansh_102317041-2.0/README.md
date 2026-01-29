# 📊 TOPSIS-Devansh-102317041

> **A Python library for Multiple Criteria Decision Making (MCDM) using TOPSIS**

[![PyPI version](https://img.shields.io/pypi/v/TOPSIS-Devansh-102317041.svg)](https://pypi.org/project/TOPSIS-Devansh-102317041/)
[![Python Version](https://img.shields.io/pypi/pyversions/TOPSIS-Devansh-102317041.svg)](https://pypi.org/project/TOPSIS-Devansh-102317041/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Overview

**TOPSIS-Devansh-102317041** is a Python package that implements the **Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS)** method for solving Multiple Criteria Decision Making (MCDM) problems.

This package simplifies the process of ranking alternatives based on multiple criteria

---

## 🧠 What is TOPSIS?

**TOPSIS** is a multi-criteria decision analysis method that:

1. Identifies the **ideal best** and **ideal worst** alternatives
2. Calculates the **Euclidean distance** from each alternative to both ideal solutions
3. Ranks alternatives based on their **relative closeness** to the ideal solution

The alternative closest to the ideal best and farthest from the ideal worst is ranked highest.

---

## 📦 Installation

Install the package using pip:

```bash
pip install Topsis-Devansh-102317041
```

---

## 🚀 Usage

### Basic Syntax

```bash
topsis <input_file.csv> <weights> <impacts> <output_file.csv>
```

### Parameters

| Parameter | Description | Format |
|-----------|-------------|--------|
| `input_file.csv` | Input CSV file with decision matrix | `.csv` file |
| `weights` | Comma-separated weights for each criterion | `"w1,w2,w3,..."` |
| `impacts` | Comma-separated impacts (+/-) for each criterion | `"+,-,+,..."` |
| `output_file.csv` | Output CSV file with rankings | `.csv` file |

### Command Examples

**With quotes (recommended):**
```bash
topsis data.csv "1,1,1,1" "+,+,-,+" output.csv
```

> ⚠️ **Note:** Use quotes if your input contains spaces to avoid errors.

### Help Command

```bash
topsis --help
```

---

## 💡 Example

### Input File: `sample.csv`

A dataset comparing mobile phones based on different features:

| Model | Storage (GB) | Camera (MP) | Price ($) | Looks (out of 5) |
|-------|-------------|-------------|-----------|------------------|
| M1    | 16          | 12          | 250       | 5                |
| M2    | 16          | 8           | 200       | 3                |
| M3    | 32          | 16          | 300       | 4                |
| M4    | 32          | 8           | 275       | 4                |
| M5    | 16          | 16          | 225       | 2                |

### Parameters

- **Weights:** `[0.25, 0.25, 0.25, 0.25]` (Equal importance)
- **Impacts:** `[+, +, -, +]` 
  - `+` for Storage, Camera, and Looks (higher is better)
  - `-` for Price (lower is better)

### Command

```bash
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+" output.csv
```

### Output: `output.csv`

| Model | Storage (GB) | Camera (MP) | Price ($) | Looks (out of 5) | TOPSIS Score | Rank |
|-------|-------------|-------------|-----------|------------------|--------------|------|
| M1    | 16          | 12          | 250       | 5                | 0.5343       | 3    |
| M2    | 16          | 8           | 200       | 3                | 0.3084       | 5    |
| M3    | 32          | 16          | 300       | 4                | 0.6916       | 1    |
| M4    | 32          | 8           | 275       | 4                | 0.5347       | 2    |
| M5    | 16          | 16          | 225       | 2                | 0.4010       | 4    |

**Result:** Model **M3** ranks first with the highest TOPSIS score of **0.6916**.

---

## 📄 Input File Format

### Requirements

✅ CSV file format  
✅ First row contains column headers  
✅ First column contains alternative names/IDs  
✅ All criteria values must be numeric  
✅ No missing values  
✅ At least 3 alternatives and 2 criteria  

### Sample Structure

```csv
Model,Criterion1,Criterion2,Criterion3
Alt1,value1,value2,value3
Alt2,value1,value2,value3
Alt3,value1,value2,value3
```

---

## ⚠️ Important Notes

1. **Headers and Index:** The first column and first row are treated as labels and removed before processing
2. **Numeric Values Only:** Ensure all criteria values are numeric (no categorical data)
3. **Weights Format:** Weights should be positive numbers (will be normalized automatically)
4. **Impacts Format:** Use only `+` (beneficial) or `-` (non-beneficial)
5. **Dimension Matching:** Number of weights and impacts must match the number of criteria
6. **Minimum Data:** At least 3 alternatives and 2 criteria required

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

**Devansh Chhabra**  
📧 Email: [devanshchhabr@gmail.com](mailto:devanshchhabr@gmail.com)  

---
