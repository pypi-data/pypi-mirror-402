# Topsis_Arjun_Angirus_102303596

A simple Python package implementing TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) for multi-criteria decision-making.

## Install

```bash
pip install .
```

## CLI Usage

```bash
# After installation
topsis-aaa-102303596 <InputDataFile> <Weights> <Impacts> <OutputResultFile>

# Example
topsis-aaa-102303596 example.csv "0.5,0.3,0.2" "+,+,-" output.csv
```

- `InputDataFile`: CSV with first column as identifier, remaining columns numeric criteria.
- `Weights`: Comma-separated numeric weights (same count as criteria).
- `Impacts`: Comma-separated `+` or `-` for each criterion.
- `OutputResultFile`: Path to save results.

## Python API

```python
from Topsis_Arjun_Angirus_102303596.topsis import main
# main() reads args from sys.argv
```

## Project Structure

```
.
├── LICENSE.txt
├── README.md
├── setup.cfg
├── setup.py
├── Topsis_Arjun_Angirus_102303596/
│   ├── __init__.py
│   └── topsis.py
└── .gitignore
```

## Requirements

- Python >= 3.8
- numpy, pandas

## License

MIT
