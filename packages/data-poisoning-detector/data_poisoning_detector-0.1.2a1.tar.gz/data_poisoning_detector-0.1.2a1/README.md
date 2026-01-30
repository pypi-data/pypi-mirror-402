**Status: Alpha**
APIs may change and detection thresholds are still being refined.
Results should not be considered production-stable.

This is the python library that can be used for the api requests so that users can call to check for poisons in their own datasets.

---

## Quick Start

```python
from poison_detector import api

#UCI dataset
report = api.analyze('uci', 73)
print(report)
clean_uci_df = api.clean('uci', 73)

#CSV file
report = api.analyze('csv', 'path/to/file/dataset.csv')
print(report)
clean_csv_df = api.clean('csv', 'path/to/file/dataset.csv')

#URL
report = api.analyze('url', 'https://webpath/to/file/dataset')
print(report)
clean_url_csv_df = api.clean('url', 'https://webpath/to/file/dataset')
```

---

```markdown
## Supported Sources

- "uci" - UCI Machine Learning repository (by dataset ID).
- "csv" - Local CSV files.
- "url" - URL where an csv file is set for the dataset.

for url's in google drive you can use the following format

- https://drive.google.com/uc?id=FILE_ID&export=download
```
