# Topsis-Pratham-102303052

A Python package for performing TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution) analysis on multi-criteria decision-making problems.

**Author:** Pratham Garg  
**Roll Number:** 102303052

## What is TOPSIS?

TOPSIS is a multi-criteria decision analysis method that helps in selecting the best alternative from a set of alternatives based on multiple criteria. It works by finding the alternative that is closest to the ideal solution and farthest from the negative-ideal solution.

## Installation

```bash
pip install Topsis-Pratham-102303052
```

## Usage

### Command Line Interface

After installation, you can use the `topsis` command directly from the command line:

```bash
topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
```

### Example

```bash
topsis data.csv "1,1,1,2" "+,+,-,+" output-result.csv
```

### Parameters

- **InputDataFile**: Path to the CSV file containing the decision matrix
  - First column: Names of alternatives
  - Remaining columns: Criteria values (must be numeric)
  
- **Weights**: Comma-separated weights for each criterion
  - Example: "1,1,1,2"
  
- **Impacts**: Comma-separated impacts for each criterion
  - Use '+' for benefit criteria (higher is better)
  - Use '-' for cost criteria (lower is better)
  - Example: "+,+,-,+"
  
- **OutputResultFileName**: Path where the result file will be saved

### Input File Format

The input CSV file should have the following structure:

| Fund Name | P1   | P2   | P3  | P4   | P5    |
|-----------|------|------|-----|------|-------|
| M1        | 0.67 | 0.45 | 6.5 | 42.6 | 12.56 |
| M2        | 0.6  | 0.36 | 3.6 | 53.3 | 14.47 |
| M3        | 0.79 | 0.61 | 6.4 | 63.1 | 17.84 |

### Output File Format

The output file will contain all input columns plus two additional columns:

- **Topsis Score**: The calculated TOPSIS score for each alternative
- **Rank**: The rank of each alternative (1 = best)

## Validation

The package performs the following validations:

- Correct number of parameters
- File existence check
- Minimum 3 columns in input file
- Numeric values in all columns except the first
- Matching number of weights, impacts, and criteria columns
- Valid impact values ('+' or '-')

## Error Handling

The package provides clear error messages for:
- Missing or incorrect parameters
- File not found
- Non-numeric values in criteria columns
- Mismatch in number of weights/impacts/columns
- Invalid impact values

## Algorithm

The TOPSIS algorithm follows these steps:

1. **Normalization**: Vector normalization of the decision matrix
2. **Weighted Normalization**: Multiply normalized values by weights
3. **Ideal Solutions**: Determine ideal best and ideal worst solutions
4. **Distance Calculation**: Calculate Euclidean distances from ideal solutions
5. **TOPSIS Score**: Calculate relative closeness to ideal solution
6. **Ranking**: Rank alternatives based on TOPSIS scores

## License

MIT License

## Author

Pratham Garg  
Roll Number: 102303052  
Email: pgarg7_be23@thapar.edu

## Links

- [PyPI](https://pypi.org/project/Topsis-Pratham-102303052/)
- [GitHub](https://github.com/prathamgarg1103/Topsis-Pratham-102303052)


## Mail Service Configuration

To enable automated email delivery of TOPSIS results:

1.  Navigate to the `backend/` directory.
2.  Open the `.env` file (created from `.env.example`).
3.  Fill in your SMTP credentials:
    - `SENDER_EMAIL`: Your Gmail or SMTP email address.
    - `SENDER_PASSWORD`: Your SMTP password or [Gmail App Password](https://myaccount.google.com/apppasswords).
4.  Restart the backend server.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.
