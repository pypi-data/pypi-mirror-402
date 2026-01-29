# Topsis-Naman-102303352

**For:** UCS654 (Predictive Analytics)  
**Submitted by:** Naman Singh  
**Roll Number:** 102303352  

---

## Overview
This is a Python package that implements the **Technique for Order of Preference by Similarity to Ideal Solution (TOPSIS)**. It is a multi-criteria decision-making (MCDM) method used to rank alternatives based on their distance from the "Ideal Best" and "Ideal Worst" solutions.



## Installation

You can install the package directly from PyPI using the following command:

```bash
pip install Topsis-Naman-102303352


## Usage

The package is designed to be executed via the command line. Use the following format:

```bash
topsis <InputDataFile> <Weights> <Impacts> <ResultFileName>

## Example Input

The input file must be a CSV where the first column contains the names of the alternatives and the subsequent columns contain numeric data.

Model,Storage,Camera,Price,Looks
M1,16,12,250,5
M2,16,8,200,3
M3,32,16,300,4
M4,32,8,275,4

## Example Command

```bash
topsis data.csv "1,1,1,2,1" "+,+,-,+,+" result.csv

## Example Output

After running the command, the package performs Vector Normalization and calculates the Euclidean Distance from the Ideal Best and Ideal Worst solutions to generate the final scores and rankings.

The resulting file will contain your original columns plus the calculated Topsis Score and Rank:

Model,Storage,Camera,Price,Looks,TopsisScore,Rank
M1,16,12,250,5,0.5342,3
M2,16,8,200,3,0.3891,4
M3,32,16,300,4,0.7215,1
M4,32,8,275,4,0.6128,2

## License

https://choosealicense.com/licenses/mit/