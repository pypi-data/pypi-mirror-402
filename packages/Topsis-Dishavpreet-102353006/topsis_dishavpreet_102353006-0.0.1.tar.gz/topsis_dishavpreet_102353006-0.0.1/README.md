# Topsis-Dishavpreet-102353006

This package implements the TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) method in Python.

This project was developed as part of an academic assignment.

---

## Installation

Install the package using pip:

pip install Topsis-Dishavpreet-102353006

---

## Usage

After installation, run the following command from the command line:

topsis input.csv "1,1,1,1,1" "+,+,+,+,+" output.csv

---

## Parameters

input.csv  
Input CSV file containing alternatives and criteria.  
The first column should be non-numeric.

weights  
Comma-separated numerical weights.  
Example:  
"1,1,1,1,1"

impacts  
Comma-separated impacts.  
Use + for benefit and - for cost criteria.  
Example:  
"+,+,-,+,+"

output.csv  
Output CSV file containing TOPSIS score and rank.

---

## Example

topsis data.csv "1,1,1" "+,+,+" result.csv

---

## Requirements

Python 3.x  
numpy  
pandas
