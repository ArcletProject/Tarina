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



## Build from source

```bash
git clone https://github.com/ArcletProject/Tarina.git
cd Tarina
pip install setuptools wheel cibuildwheel==2.12.1
pip install -r requirements/cython.txt
make cythonize
python -m cibuildwheel --output-dir wheelhouse
```