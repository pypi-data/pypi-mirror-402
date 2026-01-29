# simple-recommender-rg

## Description
simple-recommender-rg is a Python package that implements a simple 
content-based recommender system.
It recommends items based on feature similarity using machine learning 
techniques.

This project is mainly intended for academic learning and mini-projects.



## Installation
Use the package manager pip to install simple-recommender-rg.
```bash
pip install simple-recommender-rg
```


## Usage
Enter the CSV filename followed by the `.csv` extension.

```bash
recommend sample.csv
```

To view usage help, use:

```bash
recommend -h
```


## Example

A CSV file containing numeric feature values for different items.

```bash
| Item | Feature1 | Feature2 | Feature3 |
|------|----------|----------|----------|
| A    | 10       | 7        | 9        |
| B    | 8        | 6        | 5        |
| C    | 9        | 9        | 8        |
```

## Working
1. The CSV file is read using the pandas library.
2. The first column (item names) and first row (headers) are removed 
before processing.
3. Feature values are normalized using Min-Max scaling.
4. Cosine similarity is calculated between items.
5. Items are ranked based on similarity scores.

### Output Table

```bash
| Item | Similarity Score | Rank |
|------|------------------|------|
| A    | 1.000000         | 1    |
| C    | 0.976532         | 2    |
| B    | 0.845210         | 3    |
```

## Other Notes
- The CSV file should not contain categorical (string) values.
- There should be no missing values in the dataset.
- This package is designed for educational purposes.
- The first column and first row are removed automatically before 
processing.

## License
MIT 
