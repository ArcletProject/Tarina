# Tarina
A collection of common utils for Arclet Projects


## Installation

```bash
pip install tarina
```

## Usage

```python
from tarina import generic_isinstance
from typing import List

assert generic_isinstance([1, 2, 3], List[int])
```