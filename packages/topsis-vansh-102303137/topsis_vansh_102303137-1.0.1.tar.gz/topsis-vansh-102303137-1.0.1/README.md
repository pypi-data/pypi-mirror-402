TOPSIS Python Package

Project-1 (UCS654)

Submitted by: Vansh Garg
Roll No: 102303137
Group: 3C15

Project Description:

topsis-vansh-102303137 is a Python package for solving Multiple Criteria Decision Making (MCDM) problems using the Technique for Order Preference by Similarity to Ideal Solution (TOPSIS) method.

This package helps in ranking alternatives based on their distance from the ideal best and ideal worst solutions.

Installation

Install the package using pip:
pip install topsis-vansh-102303137

Usage

Run the package directly from the command line:
topsis <input_file.csv> <weights> <impacts>


Example:
topsis sample.csv "0.25,0.25,0.25,0.25" "+,+,-,+"

Weights and impacts can also be passed without quotes:
topsis sample.csv 0.25,0.25,0.25,0.25 +,+,-,+

⚠️ Important:
If your input contains spaces, always enclose it in double quotes " ".

Input File Format:
1. Input file must be a CSV file
2. First column → Alternative name (identifier)
3. Remaining columns → Numeric criteria only
4. No missing or categorical values allowed

Sample CSV (sample.csv):
Model,Storage,Camera,Price,Looks
M1,16,12,250,5
M2,16,8,200,3
M3,32,16,300,4
M4,32,8,275,4
M5,16,16,225,2

Parameters
Weights Vector
    Must be numeric
    Length = number of criteria

Example:
0.25,0.25,0.25,0.25


Impacts Vector
    Use + for benefit criteria
    Use - for cost criteria

Example:
+,+,-,+

Output
The program generates a CSV file with:
Topsis Score → Relative closeness to ideal solution
Rank → Higher score gets better rank

Sample Output:
      Topsis Score   Rank
1     0.534277        3
2     0.308368        5
3     0.691632        1
4     0.534737        2
5     0.401046        4

Notes
Higher Topsis Score indicates a better alternative
Rank 1 represents the best option
Input validation is performed for:

Missing values
Incorrect weights/impacts length
Invalid impact symbols

