# Functional Information Decomposition (FID) Library - User Manual

## Table of Contents
1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Core Concepts](#core-concepts)
4. [Quick Start](#quick-start)
5. [Working with TPMs](#working-with-tpms)
6. [FID Analysis](#fid-analysis)
7. [Handling Missing Data](#handling-missing-data)
8. [Visualization](#visualization)
9. [API Reference](#api-reference)
10. [Examples](#examples)
11. [Limitations & Warnings](#limitations--warnings)

---

## Overview

**FID** (Functional Information Decomposition) is a library for analyzing how multiple input variables contribute to predicting an output, using information-theoretic concepts.

### What It Does
- **Quantifies independent information**: How much each input alone predicts the output
- **Measures synergy**: Information only available from joint inputs
- **Computes solo synergy**: How much each input contributes when combined with all others
- **Handles incomplete data**: Intelligently manages missing input patterns through probabilistic sampling

### Key Features
- Build TPMs (Transition Probability Matrices) from raw data
- Compute FID decompositions on complete or incomplete data
- Sample completions using multiple strategies (Dirichlet, grid, deterministic, edges)
- Visualize results with scatter plots, clouds, and uncertainty bounds
- Flexible handling of categorical/discrete variables with arbitrary names and symbols

---

## Installation & Setup

### Install from PyPI
```bash
pip install fid-tools
```

### Import the Library
```python
from pyfid import TPM, display_fid, plot_fid_clouds
```

---

## Core Concepts

### TPM (Transition Probability Matrix)
A matrix representing the relationship between inputs and an output:
- **Rows**: All possible combinations of input patterns (exhaustive enumeration)
- **Columns**: Output symbols/states
- **Values**: Probabilities P(Y|X) for conditional, or P(X,Y) for joint

### RN_TPM (Row-Normalized TPM)
Each row sums to 1.0, representing **conditional probability P(Y|X_i)**
- Answers: "Given this input pattern, what's the probability of each output?"

### MN_TPM (Matrix-Normalized TPM)
The entire matrix sums to 1.0, representing **joint probability P(X,Y)**
- Answers: "What's the probability of seeing this input-output pair?"
- Computed as: `MN_TPM = RN_TPM / n_rows` (assuming uniform input distribution)

### Information-Theoretic Metrics

**Entropy H(Y)**
- Measure of output uncertainty
- Higher entropy = more uniform output distribution

**Conditional Entropy H(Y|X)**
- Average uncertainty in output given the inputs
- Lower is better (inputs explain more)

**Mutual Information I(X;Y)**
- How much knowing X reduces uncertainty about Y
- Equals: `H(Y) - H(Y|X)`

**Independent Information**
- How much a single input X_i predicts Y by itself

**Synergy**
- Information only available from the joint state of all inputs
- Equals: `Total MI - Sum of Independents`

**Solo Synergy**
- How much input X_i contributes when combined with all other inputs
- Accounts for interactions and non-linear effects

---

## Quick Start

### Example 1: Build and Analyze a Simple TPM

```python
import numpy as np
from pyfid import TPM, display_fid

# Create data: one input perfectly predicts output, the other doesn't
input_A = ['a', 'a', 'b', 'b', 'a', 'b']
input_B = [0, 1, 0, 1, 0, 1]
output = ['X', 'Y', 'X', 'Y', 'X', 'Y']

# Build TPM from data
tpm = TPM.from_data(
    data=[input_A, input_B, output],
    input_names=['A', 'B'],
    output_name='Z'
)

# Display the TPM
tpm.display()

# Compute FID
fid_result = tpm.fid()

# Display results
display_fid(fid_result)
```

**What to expect:**
- Input B perfectly predicts output (B=0 always → X, B=1 always → Y)
- Input A does not predict output
- So: B has high independent information (~1.0 bits), A has none
- Synergy should be ~0.0 (no joint effects needed)

### Example 2: Handle Incomplete Data

```python
# Data with a missing input pattern (a,a)
input_1 = ['a', 'a', 'b', 'b']
input_2 = [0, 1, 0, 1]
output = ['X', 'Y', 'X', 'Y']

tpm = TPM.from_data(
    data=[input_1, input_2, output],
    input_names=['A', 'B'],
    output_name='Z'
)

# Check missing rows
print(f"Missing patterns: {len(tpm.missing_rows)}")

# Set a prior for missing pattern (a,0)
tpm.set_row(('a', 0), {'X': 0.8, 'Y': 0.2})

# Now compute FID on neutral (uniform) completion
result = tpm.neutral_completion_fid()
display_fid(result)
```

---

## Working with TPMs

### Creating a TPM

```python
tpm = TPM.from_data(
    data=[input_1_seq, input_2_seq, output_seq],
    input_names=['Input1', 'Input2'],
    output_name='Output'
)
```
- Automatically builds all possible patterns
- Counts observed transitions to compute P(Y|X)
- Marks patterns never seen as "missing"

### Inspecting a TPM

```python
# Display the full TPM
tpm.display()

# Get input names
inputs = tpm.get_input_names()
print(inputs)  # ['A', 'B']

# Get symbols for each input
input_symbols = tpm.get_input_symbols()
print(input_symbols)  # {'A': ['a', 'b'], 'B': [0, 1]}

# Get output symbols
output_symbols = tpm.get_output_symbols()
print(output_symbols)  # ['X', 'Y']

# Check for missing rows
print(f"Missing: {len(tpm.missing_rows)} / {tpm.n_rows}")
```

### Modifying a TPM

#### Add/Extend Output Symbols
```python
# Add new output symbol
tpm.extend_symbols(['Z'])
tpm.display()  # New column automatically filled with 0.0 for complete rows
```

#### Set a Row (Prior)
Set a specific input pattern to a known probability distribution:

```python
# Set pattern (a, 0) to probability {'X': 0.8, 'Y': 0.2}
tpm.set_row(('a', 0), {'X': 0.8, 'Y': 0.2})

# Internally, probabilities are normalized
# After refresh, RN_TPM[pattern_idx] = [0.8, 0.2]
```

#### Set a Row (Restriction)
Restrict which outputs are allowed for a pattern, but keep it incomplete:

```python
# Pattern (a, 0) can only produce 'X' (but exact probability unknown)
tpm.set_row(('a', 0), ['X'])

# Row stays in missing_rows; FID requires all rows complete
# Useful for constraints in completion sampling
```

#### Clear a Row
```python
# Reset pattern (a, 0) to unknown (all NaN)
tpm.clear_row(('a', 0))
```

#### Refresh After Changes
```python
# Automatically called by set_row(), clear_row(), extend_symbols()
# But can be called manually:
tpm.refresh_TPMs()

# This recomputes:
# - RN_TPM normalization (each row sums to 1)
# - MN_TPM from RN_TPM (joint distribution)
```

---

## FID Analysis

### Single-Point FID

For a **complete TPM** (no missing rows), compute exact FID:

```python
result = tpm.fid()

# Result keys:
# - 'total_information' (float): I(X;Y)
# - 'independents' (dict): {label -> float} for each input
# - 'synergy' (float): residual joint information
# - 'solo_synergies' (dict): {label -> float} for each input
# - 'output_entropy' (float): H(Y)
# - 'conditional_entropy' (float): H(Y|X)
# - 'input_labels' (list): formatted variable names

print(f"Total Info: {result['total_information']:.4f} bits")
print(f"Synergy: {result['synergy']:.4f} bits")
for label, val in result['independents'].items():
    print(f"  {label}: {val:.4f} bits")
```

### Neutral Completion FID

For **incomplete TPMs**, fill missing rows uniformly and compute FID:

```python
result = tpm.neutral_completion_fid()

# Returns same structure as fid()
# Missing rows filled with P(Y) = uniform over allowed outputs
```

---

## Handling Missing Data

The library provides multiple strategies for sampling **completions** of missing rows.

### Motivation
When data is sparse, not all input patterns are observed. FID requires a complete TPM. Different completion strategies yield different (but related) FID results. Sampling many completions gives uncertainty bounds.

### Strategy 1: Dirichlet Cloud (Recommended)

Sample missing rows from a **Dirichlet distribution** (soft, probabilistic):

```python
cloud = tpm.fid_cloud(
    method='dirichlet',
    n_samples=10000,
    alpha=1.0
)

# cloud keys:
# - 'total_information' (array of shape (n_samples,))
# - 'independents' (dict of arrays)
# - 'synergy' (array)
# - 'solo_synergies' (dict of arrays)
# - 'output_entropy', 'conditional_entropy' (arrays)
# - 'n_completions' (int): 10000

# Get summary statistics
import numpy as np
mean_synergy = np.mean(cloud['synergy'])
std_synergy = np.std(cloud['synergy'])
print(f"Synergy: {mean_synergy:.4f} ± {std_synergy:.4f}")
```

**Alpha parameter:**
- `alpha = 1.0`: Uniform (neutral, default)
- `alpha < 1.0`: Sparse distributions (peaked)
- `alpha > 1.0`: Uniform distributions

### Strategy 2: Deterministic Cloud

Sample missing rows from **discrete delta distributions** (hard one-hot):

```python
cloud = tpm.fid_deterministic(n_samples=5000)

# Each missing row is assigned to a single output with 100% probability
# Result: all outputs represented equally
```

**Use when:**
- You want extreme/boundary cases
- Grid is computationally feasible

### Strategy 3: Grid-Based Cloud

Sample missing rows from a **structured grid** (balanced, parametric):

```python
cloud = tpm.fid_grid(
    steps=5,      # discretization level
    n_samples=10000
)

# Automatically subsamples if grid is larger than n_samples
# Deterministic and reproducible
```

**Use when:**
- You want systematic coverage
- Comparability across runs

### Strategy 4: Edges Cloud

Sample missing rows along **interpolated paths** between deterministic completions:

```python
cloud = tpm.fid_edges(n_samples=5000)

# Samples midpoints between pairs of deterministic completions
# Explores the "surface" of the completion space
```

**Use when:**
- You want smooth transitions
- Interested in boundaries

### Comparing Completions

```python
# Compute multiple clouds
cloud_dirichlet = tpm.fid_cloud(n_samples=5000, alpha=1.0)
cloud_deterministic = tpm.fid_deterministic(n_samples=5000)

# Display with bounds
from pyfid import display_fid_with_bounds
neutral = tpm.neutral_completion_fid()
display_fid_with_bounds(neutral, [cloud_dirichlet, cloud_deterministic])
```

---

## Visualization

### Simple Scatter Plot

```python
from pyfid import plot_fid_clouds

neutral = tpm.neutral_completion_fid()
cloud = tpm.fid_cloud(n_samples=10000)

plot_fid_clouds(
    base_fid=neutral,
    fid_clouds=[cloud],
    names=['Dirichlet'],
    colors=['blue'],
    alphas=[0.3],
    x_metric='synergy',
    y_metric='total_information',
    filename='plot1.png'
)
```

### 3D Scatter Plot

```python
from pyfid import plot_fid_clouds_3d

plot_fid_clouds_3d(
    base_fid=neutral,
    fid_clouds=[cloud],
    names=['Dirichlet'],
    colors=['blue'],
    alphas=[0.3],
    x_metric='synergy',
    y_metric='total_information',
    z_metric='output_entropy',
    filename='plot_3d.png'
)
```

### Relationship Grid (Advanced)

```python
from pyfid import plot_fid_relationships

plot_fid_relationships(
    base_fid=neutral,
    fid_clouds=[cloud],
    names=['Dirichlet'],
    colors=['blue'],
    alphas=[0.3],
    y_axis='total_information',
    share_axis='common',  # all plots share axes
    filename='relationships.png'
)
```

This creates a matrix of scatter plots showing:
- **Top row**: Synergy and Total Information vs. y-axis
- **Remaining rows** (one per input):
  - Independent vs. y-axis
  - Solo Synergy vs. y-axis
  - Loss (Independent + Solo Synergy) vs. y-axis
  - Solo Synergy vs. Independent (2D relationship)

### Retrieving Metrics from Clouds

```python
from pyfid import get_metric

# Get a specific metric from a cloud
synergy_values = get_metric(cloud, 'synergy')
x0_independent = get_metric(cloud, 'X0_independent')
x1_solo_synergy = get_metric(cloud, 'X1_solo_synergy')
```

---

## API Reference

### TPM Class

#### Constructors

**`TPM.from_data(data, input_names=None, output_name='Y')`**
- Build TPM from sequences
- **Args:**
  - `data` (list): [input_1_seq, input_2_seq, ..., output_seq]
  - `input_names` (list, optional): Names for inputs
  - `output_name` (str): Name for output
- **Returns:** TPM instance

#### Display Methods

**`tpm.display()`**
- Print formatted TPM with all patterns and probabilities

**`tpm.get_input_names()`**
- **Returns:** List of input variable names

**`tpm.get_input_symbols()`**
- **Returns:** Dict mapping input names to symbol lists

**`tpm.get_output_symbols()`**
- **Returns:** List of output symbols

#### Modification Methods

**`tpm.set_row(pattern, symbols)`**
- Set prior or restriction for a row
- **Args:**
  - `pattern` (tuple): Input pattern using visible symbols
  - `symbols` (list or dict):
    - List: restriction to allowed outputs
    - Dict: prior probabilities {symbol -> weight}

**`tpm.clear_row(pattern)`**
- Reset row to missing (all NaN)

**`tpm.extend_symbols(new_symbols)`**
- Add new output symbols to TPM

**`tpm.refresh_TPMs()`**
- Recompute RN_TPM and MN_TPM after manual changes

#### Analysis Methods

**`tpm.fid()`**
- Compute FID for complete TPM
- **Returns:** FID result dict
- **Raises:** ValueError if missing rows exist

**`tpm.neutral_completion_fid()`**
- Compute FID with uniform completion of missing rows
- **Returns:** FID result dict

**`tpm.fid_cloud(method='dirichlet', n_samples=50000, alpha=1.0)`**
- Sample completions from Dirichlet distribution
- **Returns:** Cloud dict with arrays

**`tpm.fid_deterministic(n_samples)`**
- Sample deterministic completions
- **Returns:** Cloud dict with arrays

**`tpm.fid_grid(steps=None, n_samples=...)`**
- Sample from grid of probability compositions
- **Returns:** Cloud dict with arrays

**`tpm.fid_edges(n_samples)`**
- Sample interpolations between deterministic completions
- **Returns:** Cloud dict with arrays

#### Utility Methods

**`tpm.output_entropy()`**
- **Returns:** H(Y) as float

**`tpm.conditional_entropy()`**
- **Returns:** H(Y|X) as float

**`tpm.mutual_information()`**
- **Returns:** I(X;Y) as float

---

### Module-Level Functions

**`entropy(probs)`**
- Compute entropy of probability distribution (vectorized)
- **Args:** NumPy array of shape (..., n)
- **Returns:** Array of shape (...)

**`display_fid(fid_result)`**
- Print formatted FID report

**`display_fid_with_bounds(base_fid, clouds)`**
- Print FID with uncertainty bounds from multiple completions

**`plot_fid_clouds(base_fid, fid_clouds, names, colors, alphas, x_metric, y_metric, ...)`**
- 2D scatter plot with base assumption overlay

**`plot_fid_clouds_3d(base_fid, fid_clouds, names, colors, alphas, x_metric, y_metric, z_metric, ...)`**
- 3D scatter plot

**`plot_fid_relationships(base_fid, fid_clouds, names, colors, alphas, y_axis, ...)`**
- Relationship grid (matrix of scatter plots)

**`get_metric(cloud, metric_name)`**
- Extract a metric from a cloud dict
- Handles special naming: `X0_independent`, `X1_solo_synergy`, etc.

---

## Examples

### Example 1: Basic FID Analysis

```python
from pyfid import TPM, display_fid

# Your data: inputs as lists, output as last list
input_1 = ['a', 'a', 'b', 'b']
input_2 = [0, 1, 0, 1]
output =  ['X', 'X', 'Y', 'Y']

# Build TPM and compute FID
tpm = TPM.from_data(
    data=[input_1, input_2, output],
    input_names=['Category', 'Flag'],
    output_name='Result'
)

# Display the TPM
tpm.display()

# Compute and display FID
result = tpm.fid()
display_fid(result)
```

---

### Example 2: Handling Missing Data with Priors

```python
from pyfid import TPM, display_fid

# Data where not all input combinations are observed
input_1 = ['a', 'b', 'b']
input_2 = [1, 0, 1]
output =  ['Y', 'X', 'Y']

tpm = TPM.from_data(
    data=[input_1, input_2, output],
    input_names=['A', 'B'],
    output_name='Z'
)

# Check what's missing
print(f"Missing patterns: {tpm.missing_rows}")
tpm.display()

# Set a prior for the missing pattern (a, 0)
tpm.set_row(('a', 0), {'X': 0.8, 'Y': 0.2})

# Compute FID with neutral completion for any remaining missing rows
result = tpm.neutral_completion_fid()
display_fid(result)
```

---

### Example 3: Uncertainty Analysis with Completion Sampling

```python
from pyfid import TPM, display_fid_with_bounds
import numpy as np

# Sparse data
input_1 = [0, 0, 1]
input_2 = [0, 1, 0]
output =  [0, 1, 1]

tpm = TPM.from_data([input_1, input_2, output])

# Get baseline (neutral/uniform completion)
neutral = tpm.neutral_completion_fid()

# Sample different completion strategies
cloud_soft = tpm.fid_cloud(n_samples=10000, alpha=1.0)      # Probabilistic
cloud_hard = tpm.fid_deterministic(n_samples=10000)         # Deterministic

# Display results with uncertainty bounds
display_fid_with_bounds(neutral, [cloud_soft, cloud_hard])

# Access raw values for custom analysis
print(f"\nSynergy range: {np.min(cloud_soft['synergy']):.3f} - {np.max(cloud_soft['synergy']):.3f}")
```

---

### Example 4: Visualization

```python
from pyfid import TPM, plot_fid_clouds

# Build TPM from data
input_1 = [0, 0, 1, 1, 0]
input_2 = [0, 1, 0, 1, 0]
output =  [0, 1, 1, 0, 0]

tpm = TPM.from_data([input_1, input_2, output], input_names=['X1', 'X2'])

# Generate baseline and clouds
neutral = tpm.neutral_completion_fid()
cloud1 = tpm.fid_cloud(n_samples=5000, alpha=0.1)   # Sparse completions
cloud2 = tpm.fid_cloud(n_samples=5000, alpha=1.0)   # Uniform completions
cloud3 = tpm.fid_deterministic(n_samples=5000)      # Hard completions

# Plot synergy vs total information
plot_fid_clouds(
    base_fid=neutral,
    fid_clouds=[cloud1, cloud2, cloud3],
    names=['Sparse (a=0.1)', 'Uniform (a=1)', 'Deterministic'],
    colors=['red', 'blue', 'green'],
    alphas=[0.3, 0.3, 0.3],
    x_metric='synergy',
    y_metric='total_information',
    filename='fid_cloud_plot.png'
)
```

---

### Example 5: Comparing Completion Strategies

```python
from pyfid import TPM
import numpy as np

# Data with missing patterns
input_1 = ['a', 'a', 'b']
input_2 = ['x', 'y', 'x']
output =  [1, 2, 1]

tpm = TPM.from_data([input_1, input_2, output])

print(f"Complete patterns: {tpm.n_rows - len(tpm.missing_rows)}/{tpm.n_rows}")

# Run different strategies
strategies = {
    'Neutral': tpm.neutral_completion_fid(),
    'Dirichlet (a=0.1)': tpm.fid_cloud(n_samples=5000, alpha=0.1),
    'Dirichlet (a=1.0)': tpm.fid_cloud(n_samples=5000, alpha=1.0),
    'Deterministic': tpm.fid_deterministic(n_samples=5000),
    'Grid': tpm.fid_grid(n_samples=5000),
}

# Compare synergy across strategies
print("\nSynergy by strategy:")
print("-" * 50)
for name, result in strategies.items():
    syn = result['synergy']
    if isinstance(syn, np.ndarray):
        print(f"{name:20} {np.mean(syn):8.4f} (range: {np.min(syn):.4f} - {np.max(syn):.4f})")
    else:
        print(f"{name:20} {syn:8.4f}")
```

---

### Example 6: Working with Categorical Data

```python
from pyfid import TPM, display_fid

# Mixed categorical data
weather = ['sunny', 'sunny', 'rainy', 'rainy', 'cloudy', 'cloudy']
weekend = [True, False, True, False, True, False]
activity = ['beach', 'work', 'movies', 'work', 'hiking', 'work']

tpm = TPM.from_data(
    data=[weather, weekend, activity],
    input_names=['Weather', 'Weekend'],
    output_name='Activity'
)

tpm.display()

# Check coverage
print(f"\nObserved {tpm.n_rows - len(tpm.missing_rows)} of {tpm.n_rows} possible patterns")

# Compute FID (using neutral completion for missing)
result = tpm.neutral_completion_fid()
display_fid(result)
```

---

### Example 7: Full Analysis Pipeline

```python
from pyfid import TPM, display_fid, display_fid_with_bounds, plot_fid_clouds
import numpy as np

# 1. Load/prepare your data
gene_A = [0, 0, 1, 1, 0, 1, 0, 1]
gene_B = [0, 1, 0, 1, 1, 0, 1, 0]
phenotype = ['healthy', 'sick', 'sick', 'healthy', 'healthy', 'sick', 'sick', 'healthy']

# 2. Build TPM
tpm = TPM.from_data(
    data=[gene_A, gene_B, phenotype],
    input_names=['GeneA', 'GeneB'],
    output_name='Phenotype'
)

# 3. Inspect
print("=== TPM Summary ===")
tpm.display()
print(f"Missing patterns: {len(tpm.missing_rows)}")

# 4. Compute baseline FID
print("\n=== Baseline FID ===")
if len(tpm.missing_rows) == 0:
    baseline = tpm.fid()
else:
    baseline = tpm.neutral_completion_fid()
display_fid(baseline)

# 5. If incomplete, quantify uncertainty
if len(tpm.missing_rows) > 0:
    print("\n=== Uncertainty Analysis ===")
    cloud = tpm.fid_cloud(n_samples=10000, alpha=1.0)
    display_fid_with_bounds(baseline, [cloud])

    # 6. Visualize
    plot_fid_clouds(
        base_fid=baseline,
        fid_clouds=[cloud],
        names=['Completions'],
        colors=['steelblue'],
        alphas=[0.2],
        x_metric='synergy',
        y_metric='total_information'
    )
```

---

## Limitations & Warnings

### Combinatorial Explosion

⚠️ **Critical Limitation:** The library enumerates ALL possible input patterns upfront.

- 3 inputs × 3 values each = 27 patterns
- 5 inputs × 3 values each = 243 patterns
- 10 inputs × 3 values each = 59,049 patterns
- 20 inputs × 3 values each = 3.5 billion patterns ❌

**Recommendation:** For sparse data (>10 inputs or high cardinality), this library will struggle. Consider:
- Reducing dimensionality beforehand
- Using a sparse-friendly alternative for very high dimensions
- Accepting that dense enumeration is necessary for exact FID calculations

### Missing Rows and Completeness

⚠️ **FID requires all rows to be complete.** Options:
1. `fid()` - Works only if no missing rows
2. `neutral_completion_fid()` - Fills missing rows uniformly
3. `fid_cloud()` etc. - Samples many completions and returns distributions

**Choose based on your problem:**
- All data observed? → Use `fid()`
- Sparse data with no prior? → Use `fid_cloud()` + `neutral_completion_fid()`
- Domain knowledge about missing patterns? → Use `set_row()` + `neutral_completion_fid()`

### Normalization Assumptions

The library assumes **uniform input distribution** P(X) = 1/n_rows when computing MN_TPM.

If your observed data has non-uniform pattern frequencies, consider:
- Resampling or weighting your data upfront
- Using `from_data()` which properly counts observed patterns

### Numerical Precision

- Small probabilities (< 1e-12) are clipped to avoid log(0)
- Very sparse distributions may have numerical issues
- Use `np.clip()` if you see NaN/inf in results

### Reproducibility

- Sampling methods (`fid_cloud`, etc.) use random number generation
- Set `np.random.seed()` before calls if reproducibility is needed

```python
np.random.seed(42)
cloud = tpm.fid_cloud(n_samples=5000)
```

### Performance Considerations

- **Bottleneck:** Computing marginalizations for each FID sample
- **For large n_samples (>100k):** Memory usage grows ~10GB+
- **Recommendation:** Batch clouds or reduce n_samples if memory-constrained

---

## FAQ

**Q: What's the difference between `fid()` and `neutral_completion_fid()`?**

A: `fid()` requires a complete TPM (raises error if missing rows). `neutral_completion_fid()` fills missing rows with uniform distributions and returns a single FID result.

**Q: Can I compare FID results across different datasets?**

A: Partially. FID values are relative to the datasets' entropies. Comparing synergy or independents directly is only valid if output entropies are similar.

**Q: How do I know if my completion is "good"?**

A: Sample many completions and check the bounds. Wide bounds = uncertain. Narrow bounds = robust. Compare across strategies (Dirichlet, deterministic, grid, edges) for consistency.

**Q: What if I have ordered/continuous variables?**

A: Discretize them first (bin into categories), then use the library.

**Q: Can I export the TPM to CSV?**

A: Use `tpm.RN_TPM`, `tpm.input_info`, and `tpm.output_info` to extract the data for export.

**Q: How do I interpret "synergy" intuitively?**

A: Synergy is the "magic" that only happens when inputs are jointly considered. Example: XOR (each input alone is useless; together they perfectly predict output).

---

## Version & Author Notes

- **Package:** `fid-tools` (import as `pyfid`)
- **Version:** 0.1.0
- **License:** MIT
- **Author:** Clifford Bohm

For issues or contributions, refer to the repository documentation.
