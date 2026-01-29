# TOPSIS Implementation in Python

**Course:** UCS654 – Predictive Analytics using Statistics  
**Assignment:** Assignment-1 (TOPSIS)  
**Author:** Pritish Dutta  
**Roll Number:** 102303473

---

##  About the Project

This project provides a Python implementation of the  
**TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)** method.

TOPSIS is a multi-criteria decision-making (MCDM) technique used to rank alternatives based on their distance from the ideal best and ideal worst solutions.


---

##  Installation (User Manual)

This package requires **Python 3.7 or higher**.

### Dependencies
- pandas  
- numpy  

Package listed on PyPI:- https://pypi.org/project/Topsis-pritish-102303473/

Install the package using pip:

```bash
pip install Topsis-pritish-102303473
```
---

## Usage

Run the following command in the Command Prompt / Terminal:

```bash
topsis <inputFile> <weights> <impacts> <outputFile>
```
 Example

 ```bash 
 topsis sample.csv "1,1,1,1" "+,+,-,+" result.csv

```







