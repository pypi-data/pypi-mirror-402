## 1. Functional Information Decomposition (FID)

### 1.1 What is FID?

Functional Information Decomposition (FID) is a framework for decomposing the mutual information between a set of input variables and an output variable **with respect to the system’s input–output mapping**. Rather than attempting to infer informational structure solely from observed probability distributions, FID treats the function itself—deterministic or probabilistic—as the object of analysis.

FID decomposes mutual information between X (a set of inputs) and Y (the output) into:
- **Independent information(X<sub>i</sub>)** attributable to each input (X<sub>i</sub>) individually, and
- **Synergistic information** that arises only from the joint consideration of multiple inputs.

In addition FID provides a definition for:
- **Solo Synergy(X<sub>i</sub>)** the amount of synergistic information that is lost if variable X<sub>i</sub> is removed and
- **Information Loss(X<sub>i</sub>)** reduction in mutual information between X and Y if variable X<sub>i</sub> is removed.

The theoretical framework, examples, and visualizations of these completion spaces are described in detail in the accompanying paper:

- **Functional Information Decomposition: A First-Principles Approach to Analyzing Functional Relationships**
- arXiv: https://arxiv.org/abs/2509.18522

### 1.2 FID with Complete data availability

When a function is fully specified, FID provides a single unique decomposition. 

### 1.3 FID with Partial data availability

In real-world applications, data is often incomplete. Some input combinations may be unobserved, leaving the true input-output mapping underdetermined. Multiple distinct functions can be equally consistent with the finite observed dataset.

FID handles this by constructing a **space of possible functional completions** consistent with the data. Each valid completion yields a specific information decomposition. By analyzing the distribution of decompositions across this space, FID quantifies what is conclusively determined by the data versus what remains uncertain, moving beyond a single, potentially misleading point estimate.

### 1.4 FID with biased data

When the observed data has a biased input distribution (e.g., some input patterns are overrepresented), FID isolates the analysis of the functional mapping from the sampling bias. The data is internally reweighted to reflect a uniform input distribution. Duplicate input patterns are treated as a single functional entry, and conflicting outputs for the same input are interpreted as evidence of a probabilistic (non-deterministic) mapping.


---

## 2. Installation & Setup

### Installation
Install the FID package directly from PyPI:
```bash
pip install fid-tools
```

### Import the Library
```python
import pyfid
```

---

## 3. Core Concepts

### 3.1 TPM (Transition Probability Matrix)
The fundamental representation of a function in FID. A TPM captures the complete probabilistic relationship between inputs and outputs:
- **Rows**: All possible combinations of input patterns (exhaustive enumeration)
- **Columns**: Output symbols/states
- **Values**: Probabilities of each output occurring for each specific input pattern

### 3.2 FID Solution
A single, complete decomposition of the mutual information for a given function. Each FID solution represents the information structure (independent information, synergy, solo synergy, information loss) for one fully specified input-output mapping.

### 3.3 FID Cloud
When working with partial data, multiple functions are consistent with the observations. The **FID cloud** represents the set of FID solutions across this space of valid functional completions. Analyzing the cloud allows quantification of what is certain versus uncertain in the information decomposition.

---

## 4. Getting started with pyfid

### Example 1: Build and Analyze a Simple TPM
How to create a TPM for a simple AND function and compute its FID decomposition.

```python
import pyfid

# X1 AND X2 = Y
input_X1 = [0,1,0,1]
input_X2 = [0,0,1,1]
output_Y = [0,1,1,1]

# Build TPM from data
tpm = pyfid.TPM.from_data(
    data=[input_X1, input_X2, output_Y],
    input_names=['X1', 'X2'],
    output_name='Y'
)

# Display the TPM
tpm.display()

# Compute FID
fid_result = tpm.fid()

# Display results
pyfid.display_fid(fid_result)
```

### Example 2: Analyze an incomplete TPM
This example illustrates methods to visualize FID clouds.

```python
import pyfid

# Partial data could specify OR (if 1,1 = 1), XOR (if 1,1 = 0), or a probabilistic function where 1,1 specifies a distribution over Y.
input_X1 = [0,1,0]
input_X2 = [0,0,1]
output_Y = [0,1,1]

# Build TPM from data
tpm = pyfid.TPM.from_data(
    data=[input_X1, input_X2, output_Y],
    input_names=['X1', 'X2'],
    output_name='Y'
)

# Display the TPM
tpm.display()

# run fid on a neutral completion of tpm (all missing rows set to uniform distribution over output)
nc = tpm.neutral_completion_fid()

# run fid on 500 samples between deterministic solutions
edges = tpm.fid_edges(n_samples=500)

# run fid on deterministic solutions (if > 25k, sample randomly)
ends = tpm.fid_deterministic(n_samples=25000)

#generate a text report
pyfid.display_fid_with_bounds(nc,[edges,ends])

#generate a plot of total information by synergy
pyfid.plot_fid_clouds(
    base_fid= nc,
    fid_clouds= [edges,ends],
    names= ['probablistic','determinstic'],
    colors= ['red','k'],
    alphas= [.25,1],
    markers= ['.','o'],
    x_metric= 'synergy',
    y_metric= 'total_information',
    figsize= (5, 3) )
```
---
## 5. Using TPMs

The Transfer probability matrix (TPM) is a data type that is used to input, store, and manipulate data used in FID processing. For each possible input pattern (the cartesian product of the individual input domains) the TPM either stores one of the following:
- a distribution over the output space
- a list of allowed symbols
- missing, indicating that there is no data associated with this input pattern.
TPMs are initialized from existing data, but can be edited after initialization.

### 5.1 Initializing a TPM
TPMs are initialized using the TPM.from_data().
The data list can contain ints or strings, so, X1 = [1,0,2,1] and X1 = ['red','green','red','yellow'] are both valid, but X1 = ['red',1,2,'green'] is invalid.
```python
# Build TPM from data
tpm = pyfid.TPM.from_data(
    data=[input_X1, input_X2, output_Y],
    input_names=['X1', 'X2'],
    output_name='Y'
)
```
### 5.2 Inspecting a TPM
display() shows the state of a TPM
```python
tpm.display()
```
### 5.3 Manipulating existing TPMs
#### 5.3.1 set_row()
set_row() sets the output for the given input pattern. Symbols can be either a list or dict.

The list method leaves the output unspecified, but restricts it to elements in the list. If the list contains a single value then the output is deterministic.
```python
# restrict the input 0,1 so that when completions are generated, 'b' is not allowed.
tpm.set_row((0, 1), ['a','c'])
```
The dict format, sets the output to an exact distribution of the outputs. If this method is used, all output symbols must be assigned a value. 
```python
# set the input 0,1 to 'a' 4/5th of the time and 'c' 1/5th of the time, and never output 'b'.
tpm.set_row((0, 1), {'a': 4, 'b': 0, 'c': 1})
```

#### 5.3.2 clear_row()
clear_row() removes a row from a TPM, replacing any data with "MISSING"
```python
# clear output associated with input 0,1
tpm.clear_row((0,1))
```

#### 5.3.3 extend_symbols()
extend_symbols() adds symbols to the output alphabet. When completions are generated these symbols are included expect where set_row() has been used to set up restrictions. Once a symbol has been added it can be used in set_row() calls.
```python
# add the symbol 'd' to the set of possible outputs
tpm.extend_symbols(['d','e'])
```
---
## 6 generating FID solutions and clouds

### 6.1 using FID with complete data
When a TPM is fully specified (no missing rows) fid() can be used to generate an FID solution and display_fid() can be used to display a report:
```python
# generate an fid solution
result = tpm.fid()
```
### 6.2 using FID with incomplete data
When only partial data is available, fid can not be used directly. pyfid provides several tools to generate FID clouds, sets of solutions that comport with observed data.
#### 6.2.1 neutral_completion_fid()
neutral_completion_fid() does not actually generate a cloud, but a single fid solution similar to calling fid() directly). For each missing row, the highest entropy distribution is used. So if the output domain were {`A`,`B`,`C`} then missing rows would be assumed to map to 1/3 `A`,1/3 `B`,1/3 `C`, unless there as a restriction in place (see set_row()) and then, for that row only, the allowed symbols would be used.
```python
# generate a neutral fid solution
nc = tpm.neutral_completion_fid()
```

While the neutral completion is often assumed to represent a lack of assumptions, it is in fact a specific modeling choice. The neutral completion should not be interpreted as an estimate of the behavior of an underspecified function. Instead, it should be understood as a geometric reference point in the completion space, or as one distinguished member of the ensemble of admissible completions that may be useful for visualization and orientation, but not for inference.
#### 6.2.1 fid_deterministic()
fid_deterministic() samples all deterministic completions (corners of the polytope). In each completion, every missing input pattern is assigned exactly one output symbol. The n_samples parameter sets the maximum number of samples in the cloud. If the number of deterministic completions is greater than n_samples, fid_deterministic returns a randomly determined subsample.
```python
# generate a cloud of deterministic FID solutions with at most 10000 points
deterministic_cloud = tpm.fid_deterministic(n_samples = 10000)
```
#### 6.2.2 fid_edges()
fid_edges() samples completions along edges of the completion polytope, interpolating between deterministic corner solutions. These correspond to minimally non-deterministic completions: all but one previously unobserved input pattern remain deterministic, while that pattern varies probabilistically between two output symbols. The n_samples parameter sets the number of samples to be generated.
```python
# generate a cloud of edge FID solutions with 10000 points
edge_cloud = tpm.fid_edges(n_samples = 10000)
```
#### 6.2.3 fid_grid()
fid_grid() samples completions at regular intervals over the space of admissible completions. The total number of samples is capped by the n_samples parameter.

The optional steps parameter controls the granularity of the probability grid used for probabilistic completions. With steps = n, probabilities are discretized to multiples of 1/n. For example, if the output alphabet has three symbols, steps = 4 explores distributions such as [1, 0, 0], [0.25, 0.5, 0.25], and [0.75, 0.25, 0].

If steps is not provided, it is chosen automatically based on n_samples, selecting the largest grid resolution that yields no more than n_samples total completions. If steps is provided explicitly and the resulting grid exceeds n_samples, points are sampled
randomly from the grid.

```python
# generate a cloud of grid FID solutions with at most 10000 points
grid_cloud1 = tpm.fid_grid(n_samples = 10000, steps=None)
# generate a cloud of grid FID solutions with steps 10 and at most 10000 points
grid_cloud2 = tpm.fid_grid(n_samples = 10000, steps=10)
```
#### 6.2.4 fid_cloud()
fid_cloud() generates random probabilistic completions by sampling each missing row from a Dirichlet distribution. The number of samples is set of n_samples, and the alpha parameter tweaks the Dirichlet concentration.
  - alpha > 1: Samples cluster toward uniform distributions (high entropy)
  - alpha = 1: Uniform sampling over the probability simplex
  - alpha < 1: Samples favor sparse, corner-like distributions (low entropy)

For example, with three output symbols:
  - alpha=10 tends to produce distributions like [0.35, 0.32, 0.33]
  - alpha=0.1 tends to produce distributions like [0.92, 0.05, 0.03]

A method parameter is provided to allow for alternative sampling(default: 'dirichlet'). Currently only Dirichlet sampling is supported. 
```python
# generate a cloud of random FID solutions 10000 points
fid_cloud_1 = tpm.fid_cloud(n_samples = 10000, alpha=1)
# generate a cloud of random FID solutions biased towards deterministic solutions 10000 points
fid_cloud_2 = tpm.fid_cloud(n_samples = 10000, alpha=.1)
```
## 7 visualizing FID clouds
### 7.1 FID reports
Two forms of text reports are available.
#### 7.1.1 display_fid()
display_fid() provides a text report of an FID produced from complete data.
```python
# generate a text report from an FID generated from complete data.
display_fid(fid)
```
#### 7.1.2 display_fid_with_bounds()
display_fid_with_bounds() provides a text report that includes bounds. display_fid_with_bounds() takes two parameters, a base_fid (usually a neutral completion) and a list of FID clouds and generates a text report based on this data.
```python
# generate a text report with nc as the "default" and cloud_1 and cloud_2 to set bounds.
display_fid_with_bounds(nc,[cloud_1,cloud_2])
```

### 7.2 plotting FID results
#### 7.2.1 plot_fid_clouds()
plot_fid_clouds() Plots one or more FID clouds as a 2D scatter plot.
| Parameter | Description |
|-----------|-------------|
|fid_clouds|list of cloud dicts from fid_grid(), fid_edges(), etc.|
|names|list of labels for the legend|
|colors|list of colors for each cloud|
|alphas|list of transparency values (0-1)|
|x_metric|metric for x-axis (e.g., 'synergy', 'X1_independent')|
|y_metric|metric for y-axis (e.g., 'total_information')|
|base_fid=None|optional single FID result; shown as red crosshairs|
|markers=None|optional list of marker styles (default: '.')|
|figsize=(8, 6)|figure dimensions|
|filename=None|optional path to save the figure|

x_metric and y_metric can be set to "total_information", "synergy", "[var]_independent", "[var]_solo_syngery" where [var] is the name of an input variable to the TPM.

```python
nc = tpm.neutral_completion_fid()
det_cloud = tpm.fid_deterministic(n_samples=1000)
edge_cloud = tpm.fid_edges(n_samples=1000)
random_cloud = tpm.fid_cloud(n_samples = 10000, alpha=1)

pyfid.plot_fid_clouds(
    fid_clouds=[random_cloud, edge_cloud, det_cloud],
    names=['random', 'edges', 'deterministic'],
    colors=['red', 'blue', 'black'],
    alphas=[.1, .25, 1.0],
    markers=['.','o','o'],
    x_metric='synergy',
    y_metric='total_information',
    base_fid=nc
)
```
#### 7.2.2 plot_fid_clouds()
plot_fid_clouds_3d() works exactly like plot_fid_clouds(), but takes one additional argument:
- z_metric,            # metric for z-axis (e.g., 'total_information')

```python
nc = tpm.neutral_completion_fid()
det_cloud = tpm.fid_deterministic(n_samples=1000)
edge_cloud = tpm.fid_edges(n_samples=1000)
random_cloud = tpm.fid_cloud(n_samples = 10000, alpha=1)

pyfid.plot_fid_clouds_3d(
    fid_clouds=[random_cloud, edge_cloud, det_cloud],
    names=['random', 'edges', 'deterministic'],
    colors=['red', 'blue', 'black'],
    alphas=[.1, .25, 1.0],
    markers=['.','o','o'],
    x_metric='synergy',
    y_metric='total_information',
    z_metric='X1_independent',
    base_fid=nc
)
```
#### 7.2.3 plot_fid_relationships()

plot_fid_relationships() Plots a grid of scatter plots showing relationships between FID
metrics.

The top row shows global metrics (synergy and total information). Each subsequent row
corresponds to an input variable, with four columns showing:
- Independent information vs. y-axis metric
- Solo synergy vs. y-axis metric
- Loss vs. y-axis metric
- Solo synergy vs. independent (2D relationship)

| Parameter | Description |
|-----------|-------------|
| fid_clouds | list of cloud dicts from fid_grid(), fid_edges(), etc. |
| names | list of labels for the legend |
| colors | list of colors for each cloud |
| alphas | list of transparency values (0-1) |
| y_metric | metric for y-axis (e.g., 'synergy', 'X1_solo_synergy') |
| base_fid=None | optional single FID result; shown as red crosshairs |
| markers=None | optional list of marker styles (default: '.') |
| figsize=(16, 4) | figure dimensions |
| filename=None | optional path to save the figure |
| share_axis="common" | axis sharing: "none", "row", "column", "common", or "all" |

```python
nc = tpm.neutral_completion_fid()
det_cloud = tpm.fid_deterministic(n_samples=1000)
edge_cloud = tpm.fid_edges(n_samples=1000)
random_cloud = tpm.fid_cloud(n_samples = 10000, alpha=1)
print(random_cloud)

pyfid.plot_fid_relationships(
    fid_clouds=[random_cloud, edge_cloud, det_cloud],
    names=['random', 'edges', 'deterministic'],
    colors=['red', 'blue', 'black'],
    alphas=[.1, .25, 1.0],
    markers=['.','o','o'],
    y_metric='total_information',
    base_fid=nc
)
```

## 8. Accessing Cloud Data Directly

FID clouds are just Python dictionaries. You can access the underlying arrays directly for
custom analysis.
```python
cloud = tpm.fid_cloud(n_samples=1000)

cloud["synergy"]                    # np.array of synergy values
cloud["total_information"]          # np.array of total information values
cloud["independents"]["X0[0,1]"]    # np.array for a specific variable
cloud["solo_synergies"]["X0[0,1]"]  # np.array for a specific variable
```













