# topsis-harshleen-102303220

A Python command-line package implementing the **TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)** method for **multi-criteria decision making (MCDM)**.

This package allows users to rank multiple alternatives based on several criteria by specifying weights and impacts, following standard TOPSIS methodology.

---

## Table of Contents

- [Introduction](#introduction)
- [What is TOPSIS?](#what-is-topsis)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Input File Format](#input-file-format)
- [Weights and Impacts](#weights-and-impacts)
- [Algorithm Steps](#algorithm-steps)
- [Output Format](#output-format)
- [Validation and Error Handling](#validation-and-error-handling)
- [Example](#example)
- [Author](#author)
- [License](#license)

---

## Introduction

Decision making often involves evaluating multiple alternatives against several criteria.  
**TOPSIS** is a well-known technique that helps identify the best alternative by comparing how close each option is to an ideal solution.

This package provides a **command-line implementation** of TOPSIS using Python and supports real-world datasets through CSV input files.

---

## What is TOPSIS?

**TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)** ranks alternatives based on:

- Minimum distance from the **Ideal Best** solution
- Maximum distance from the **Ideal Worst** solution

The alternative with the highest TOPSIS score is considered the best.

---

## Features

- Command-line based TOPSIS implementation
- Supports any number of alternatives and criteria
- User-defined weights and impacts
- Automatic ranking of alternatives
- Input validation and error handling
- Outputs results in CSV format
- Compatible with large datasets

---

## Installation

Install the package directly from **PyPI**:

```bash
pip install topsis-harshleen-102303220
Usage
Run the package using Python module execution:

bash
Copy code
python -m topsis_harshleen_102303220.topsis <InputDataFile> <Weights> <Impacts> <OutputFile>
Arguments
Argument	Description
InputDataFile	CSV file containing decision matrix
Weights	Comma-separated numeric weights
Impacts	Comma-separated + or -
OutputFile	Name of output CSV file

Input File Format
The first column must contain alternative names

Remaining columns must contain numeric values

At least 3 columns are required

Example Input (data.csv)
csv
Copy code
Mobile,Price,Storage,Camera,Looks
Mobile 1,250,16,12,5
Mobile 2,200,16,8,3
Mobile 3,300,32,16,4
Mobile 4,275,32,8,4
Mobile 5,225,16,16,2
Weights and Impacts
Weights
Represent the importance of each criterion

Must be numeric

Provided as comma-separated values

Example:

text
Copy code
1,1,1,1
Impacts
+ indicates benefit criterion

- indicates cost criterion

Example:

text
Copy code
-,+,+,+
Algorithm Steps
Read and validate input data

Normalize decision matrix using vector normalization

Apply weights to normalized matrix

Determine ideal best and ideal worst solutions

Compute Euclidean distance from ideal solutions

Calculate TOPSIS performance score

Rank alternatives based on scores

Output Format
The output file is a CSV containing:

Original data

Topsis Score

Rank (Rank 1 = Best alternative)

Example Output
cs
Copy code
Mobile,Price,Storage,Camera,Looks,Topsis Score,Rank
Mobile 3,300,32,16,4,0.6916,1
Mobile 4,275,32,8,4,0.5348,2
Mobile 1,250,16,12,5,0.5343,3
Mobile 5,225,16,16,2,0.4010,4
Mobile 2,200,16,8,3,0.3083,5
Validation and Error Handling
The package performs the following checks:

Correct number of command-line arguments

Input file existence

Minimum number of columns

Numeric values in criteria columns

Matching count of weights, impacts, and criteria

Valid impact symbols (+ or -)

Meaningful error messages are displayed for incorrect inputs.

Example
bash
Copy code
python -m topsis_harshleen_102303220.topsis data.csv "1,1,1,1" "-,+,+,+" output.csv
Author
Harshleen
Roll Number: 102303220
B.Tech Computer Engineering
Thapar Institute of Engineering and Technology