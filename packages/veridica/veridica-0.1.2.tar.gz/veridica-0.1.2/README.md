# Veridica

This project was made for the use of fuzzy comparison algorithmic comparisons for the use in gherkin based test automation.

We found that it was required to have full control over the system to limit dependencies. However that does not mean that others cannot use the code that I have developed and will use.

## Overview

Veridica provides a set of pure Python algorithms to compare strings reliably based on fixed math based algorithms.

It includes:

- Classic string similarity metrics Classic string to string matching based on algorithms like levenstein.

- One-to-many batch comparisons While one to one comparisons can give you a sence of what you are looking for, most usecases involve the comparion for one item to a set. Therefore an implementation was made using classic and recursive techniques that can be directly implemented.

- Timing utilities for measuring comparison performance For now limited to a wrapper function that can give back the time it took to complete for compartive data.

## Installation

You can install the package via **PyPI** or from **source**.

### Install from PyPI

```bash
pip install veridica

```

### Install from Source (GitHub)

```bash
git clone https://github.com/sebastiaanswanenberg/veridica.git
cd veridica
pip install .
```

## Usage

After installation, you can use `veridica` to compare strings one to one or compare a string to a set.

### Example: Comparing strings one-to-one.

```python
from veridica.similarity import levenshtein

```

### Example: Comparing string to a set of strings.

```python
from veridica.similarity import levenshtein
from veridica.batch import compare_many


```

### Example: Time your string to set calculations.

```python
from veridica.similarity import levenshtein
from veridica.batch import compare_many
from veridica.timing import timed

```

## Testing

This project includes a test suite. You can run tests using `pytest`:

```bash
pip install pytest
pytest tests
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues if you have any suggestions or find bugs.
