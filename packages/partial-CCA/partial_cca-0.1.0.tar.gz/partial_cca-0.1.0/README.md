Partial Canonical Correlation Analysis (pCCA)

A Python implementation of Partial Canonical Correlation Analysis (pCCA) designed for neuronal population recordings. pCCA identifies linear combinations of neurons that maximized interregional correlations, while statistically removing the influence of other recorded populations.

This code has been utilized in the following research:
Subspace communication in the hippocampal-retrosplenial axis. Gonzalez and Vöröslakos, et al. (doi:10.64898/2025.12.31.697203)

Installation
```
pip install partial_CCA
```
Quick Start
The PartialCCA class follows the standard scikit-learn API (fit, transform, score).

Usage in Python:
```
import numpy as np
from partial_CCA import PartialCCA

# Generate dummy data: 100 samples, 20 neurons in X, 15 in Y, 5 in Z
X = np.random.randn(100, 20)
Y = np.random.randn(100, 15)
Z = np.random.randn(100, 5)

# Initialize and fit the model
model = PartialCCA()
model.fit(X, Y, Z)

# Transform data into canonical components
proj_x, proj_y = model.transform(X, Y)

# Get canonical correlations
print(model.canonical_correlations_)

```
Features:
If no variable Z is provided, the model automatically defaults to standard Canonical Correlation Analysis (CCA).
Statistical Validation: Includes a surrogate\_test method that uses circular shifting to calculate p-values for the observed correlations.


Examples \& Tutorials:
Examples on how to use these functions can be found here: https://github.com/joaqgonzar/pCCA-Hippocampus/


About the Author:
Developed by Joaquin Gonzalez, Postdoc at the Buzsaki Lab and Chen Lab (NYU).

Google Scholar Profile:
https://scholar.google.com/citations?user=rcGEkDgAAAAJ&hl=en


