# TOPSIS

This is a project developed in Python using Numpy to calculate best possible candidate in a dataset using the Technique for Order Preference by Similarity to Ideal Solution (TOPSIS) in Data Science.
The program calculates during runtime using the built-in sys module in Python.


## INSTALLATION

pip install topsis-ritwik-102303905==0.0.1

## USAGE

To run program, run a prompt in command prompt of the format:
```bash 
python topsis.py <InputFileName> <Weights> <Impacts> <OutputFileName>
```

For example:
```bash 
    python topsis.py data.csv "2,1,0.5,1,1" "+,-,+,+,-" output.csv
```
