# chronically-needs-csv

> *For Kostas, the analyst blessed with mass amounts of Chronos (time), yet mysteriously none to spare for learning `json.load()`.*

A JSON to CSV converter for people who **chronically** can't be bothered to parse JSON themselves.

## Installation

```bash
pip install chronically-needs-csv
```

Or if you somehow mess that up too:

```bash
pip install git+https://github.com/JellevanE/chronically-needs-csv.git
```

## Usage

### Command Line

```bash
# The tool you'll chronically need
chronically-needs-csv data.json

# Or use the shorthand (named after you-know-who)
chronis data.json

# Specify output file
chronis data.json output.csv

# Use pipe delimiter for arrays (good for BigQuery, Konstantinos)
chronis data.json -d "|"

# Silent mode (if you can't handle the truth)
chronis data.json --silent
```

### Python

```python
from chronically_needs_csv import convert, json_to_csv_string

# Convert file to file
convert("data.json", "output.csv")

# Convert data directly
data = [{"name": "Chronis", "skill": "SQL", "json_knowledge": None}]
csv_string = json_to_csv_string(data)
```

## Features

- **Nested objects** → flattened with dot notation (`user.address.city`)
- **Arrays** → joined with delimiter (default: `, `)
- **Missing fields** → empty cells (like your JSON knowledge)
- **Any JSON shape** → handled automatically

## Example

Input (`analysts.json`):
```json
[
  {
    "name": "Konstantinos",
    "tools": {"primary": "BigQuery", "avoided": "Python"},
    "skills": ["SQL", "asking friends for help"]
  }
]
```

Output (`analysts.csv`):
```csv
name,tools.primary,tools.avoided,skills
Kostas,BigQuery,Python,"SQL, asking friends for help"
```

## BigQuery Import

After converting, Kostas can finally do what he does best:

```sql
LOAD DATA INTO my_dataset.my_table
FROM FILES (
  format = 'CSV',
  uris = ['gs://bucket/data.csv']
);
```

## FAQ

**Q: Why is this package called "chronically-needs-csv"?**
A: Because someone *chronically* needs CSV files and his name happens to sound like Chronos. Coincidence? We think not.

**Q: Can I use this even if my name isn't Konstantinos?**
A: Yes, but you'll still see messages about him. Consider it a feature.

**Q: Why not just use pandas?**
A: Because then we couldn't make this joke.

---

*Made with mild exasperation and mass amounts of love.*
