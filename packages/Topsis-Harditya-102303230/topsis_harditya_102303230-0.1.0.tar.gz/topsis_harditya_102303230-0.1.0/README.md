# TOPSIS CLI

Python command-line implementation of the TOPSIS method.

## Install
```bash
pip install .
```

## Run
```bash
topsis <input.csv> "<weights>" "<impacts>" <output.csv>
```

### Example
```bash
topsis data.csv "1,1,1" "+,+,+" result.csv
```

## Input
- CSV file
- First column: alternatives
- Remaining columns: numeric criteria

## Output
- Adds `Topsis Score` and `Rank`

## Web App (Streamlit)

A simple Streamlit based web interface is also included.

### Features
- Upload CSV file
- Enter weights and impacts
- Compute TOPSIS using the same package logic
- Result CSV is emailed to the provided address

### Run locally
```bash
streamlit run app.py

## Author
Harditya Vir Singh Ghuman