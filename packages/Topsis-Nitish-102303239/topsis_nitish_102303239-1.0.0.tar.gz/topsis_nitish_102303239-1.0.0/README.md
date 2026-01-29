# Topsis-Nitish-102303239

This package implements the TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) method for multi-criteria decision making.

---

## Installation

After uploading to PyPI, install using:

pip install Topsis-Nitish-102303239

---

## Usage

Run from command line as:

topsis-nitish <InputDataFile> <Weights> <Impacts> <OutputFile>

Example:

topsis-nitish data.csv "1,1,1,1" "+,+,+,+" output-result.csv

---

## Input Format

- First column → Alternative names  
- Remaining columns → Numeric criteria values  

Example:

Model,Price,Storage,Camera,Battery  
A,250,64,12,3000  
B,200,32,8,2500  
C,300,128,16,3500  
D,275,64,12,3300  

---

## Output

The output CSV file will contain:
- Original data  
- Topsis Score  
- Rank  

---

## Error Handling

The program checks for:
- File not found errors  
- Non-numeric values  
- Incorrect number of weights or impacts  
- Invalid impacts (+ or - only)  

---

## Author

Name: Nitish  
Roll Number: 102303239  
