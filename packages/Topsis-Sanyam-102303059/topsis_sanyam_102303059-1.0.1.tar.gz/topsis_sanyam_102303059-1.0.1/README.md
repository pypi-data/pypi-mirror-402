# TOPSIS Implementation in Python
# Author: Sanyam Wadhwa
# Roll Number: 102303059
# Class: 3C12

## Introduction
This project implements TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) as a Python package for multi-criteria decision analysis.

## What is TOPSIS?
TOPSIS is a multi-criteria decision analysis method that ranks alternatives by measuring their geometric distance from ideal solutions. The best alternative has the shortest distance from the ideal best and the farthest distance from the ideal worst.

## Methodology
**Algorithm Steps:**
1. **Normalize Decision Matrix**
   - r_ij = x_ij / √(Σ x_ij²)
2. **Calculate Weighted Normalized Matrix**
   - v_ij = w_j × r_ij
3. **Determine Ideal Solutions**
   - Ideal Best (A⁺): Max for beneficial (+), Min for non-beneficial (-)
   - Ideal Worst (A⁻): Min for beneficial (+), Max for non-beneficial (-)
4. **Calculate Separation Measures**
   - S_i⁺ = √(Σ (v_ij - v_j⁺)²)  [Distance from ideal best]
   - S_i⁻ = √(Σ (v_ij - v_j⁻)²)  [Distance from ideal worst]
5. **Calculate TOPSIS Score**
   - P_i = S_i⁻ / (S_i⁺ + S_i⁻)  [Range: 0 to 1]
6. **Rank Alternatives**
   - Higher score = Better rank (Rank 1 is best)

## Installation
```
pip install pandas numpy
```

## Usage
### As a Library
```python
import pandas as pd
from Topsis_Sanyam_102303059.topsis import topsis

df = pd.read_csv('data.csv')
weights = [1,1,1,2,1]
impacts = ['+','+','-','+','+']
result = topsis(df, weights, impacts)
print(result)
```

### As a Command-Line Tool
```
python topsis.py <InputFile> <Weights> <Impacts> <OutputFile>
```
**Example:**
```
python topsis.py data.csv "1,1,1,2,1" "+,+,-,+,+" result.csv
```

## Input Format
- **CSV Structure:**
  - First column: Alternative names/IDs
  - Remaining columns: Numerical criteria values

**Sample (data.csv):**
```
Model,Price,Storage,Camera,Looks,Performance
M1,250,16,12,5,5
M2,200,16,8,3,3
M3,300,32,16,4,4
M4,275,32,8,4,4
M5,225,16,16,2,2
```

## Output Format
Original columns + Topsis Score + Rank

**Sample (result.csv):**
```
Model,Price,Storage,Camera,Looks,Performance,Topsis Score,Rank
M3,300,32,16,4,4,0.6891,1
M4,275,32,8,4,4,0.6234,2
M1,250,16,12,5,5,0.5345,3
M5,225,16,16,2,2,0.4789,4
M2,200,16,8,3,3,0.4523,5
```

## Error Handling
The program validates:
- Parameter Count: Exactly 4 arguments required
- File Existence
- Column Count: Minimum 3 columns required
- Numeric Values: Columns 2+ must be numeric
- Impact Validation: Only '+' or '-' allowed
- Parameter Matching: Weights, impacts, and criteria count must match

## Example Demonstration
Test Case: Mobile Phone Selection
```
python topsis.py data.csv "1,1,1,1,1" "-,+,+,+,+" result.csv
```

## Applications
- Product selection and comparison
- Supplier evaluation
- Project prioritization
- Investment decision making
- Technology selection
- Performance evaluation

## File Structure
```
Topsis_Sanyam_102303059/
│
├── Topsis_Sanyam_102303059/
│   ├── __init__.py
│   └── topsis.py
├── README.md
├── setup.py
├── pyproject.toml
└── LICENSE
```

## Quick Start
```
# 1. Install dependencies
pip install pandas numpy

# 2. Use as a library or run as a script
```

## References
- Hwang, C.L.; Yoon, K. (1981). Multiple Attribute Decision Making
- Yoon, K. (1987). A reconciliation among discrete compromise situations

---
Developed by: Sanyam Wadhwa (102303059) - Class 3C12