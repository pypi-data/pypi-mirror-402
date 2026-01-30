# EleMi

Elastic net regularized multi-regression (https://link.springer.com/chapter/10.1007/978-3-031-57515-0_13)

EleMi is used to infer soil ecological networks using abundance data.

## Usage
EleMi takes as input an abundance matrix shaped like n × p where n is the number of samples and p is the number of taxa. You can find an example dataset in [example_data/otu.csv](https://github.com/nan-v-chen/EleMi/tree/master/example_data).
```python
from EleMi import EleMi, row_clr, col_normalize
import pandas as pd

data = pd.read_csv("example_data/otu.csv", index_col=0)
data = data.astype(float).values

data = row_clr(data)
data = col_normalize(data)

A = EleMi(data, 0.1, 0.01)
A = (A + A.T) / 2
```