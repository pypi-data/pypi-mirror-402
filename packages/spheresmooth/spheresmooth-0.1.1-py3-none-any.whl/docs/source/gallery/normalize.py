"""
Row-wise Matrix Normalization Example
=====================================

Normalize each row of a matrix by dividing by its L2 norm.
"""

import numpy as np
from spheresmooth import normalize

# Example matrix (2 × 3)
x = np.array([
    [1, 2, 3],
    [4, 5, 6]
])

print("Input matrix:")
print(x)

# Row-wise normalization
x_norm = normalize(x)

print("\nRow-wise normalized matrix normalize(x):")
print(x_norm)
