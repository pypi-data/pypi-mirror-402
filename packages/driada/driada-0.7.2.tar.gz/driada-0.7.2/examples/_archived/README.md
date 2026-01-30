# Archived Examples

This folder contains examples that have been archived during the validation process.

## Why Examples Are Archived

Examples are moved here when they are:
1. **Redundant** - Functionality already covered by other examples
2. **Outdated** - Superseded by better approaches or APIs
3. **Confusing** - May mislead users away from recommended practices

Archived examples are kept for historical reference but are not maintained or recommended for use.

---

## Archived Examples

### `recursive_embedding/` (Archived: 2026-01-12)

**Reason**: Redundant - functionality already covered by other examples

**What it demonstrated**:
- Manual DR chaining using `Embedding.to_mvdata()` method
- 3-stage pipeline: AE → PCA → t-SNE

**Why archived**:
- `dr_sequence_neural_example.py` shows the recommended `dr_sequence()` API
- `dr_simplified_api_demo.py` already demonstrates BOTH manual chaining AND the recommended API
- Having multiple examples for the same concept confuses users about which approach to use

**What to use instead**:
- For sequential DR: Use `dr_sequence()` API (see `examples/dr_sequence/`)
- For API demonstration: See `examples/dr_simplified_api/`

### `spatial_map/` (Archived: 2026-01-12)

**Reason**: Redundant + uses legacy sklearn API instead of DRIADA's MVData

**What it demonstrated**:
- Extracting 2D spatial maps from place cell populations
- Comparing PCA, Isomap, UMAP for spatial representation
- Testing robustness to noise

**Why archived**:
- Uses sklearn/umap directly (`from sklearn.decomposition import PCA`) instead of DRIADA's unified MVData API
- All other examples use `mvdata.get_embedding(method='pca', dim=2)` pattern
- `compare_dr_methods.py` already provides systematic DR comparison using proper DRIADA API
- Would require ~100 line rewrite to modernize
- Had 5 bugs that were fixed during validation

**What to use instead**:
- For DR method comparison: Use `compare_dr_methods.py` (compares PCA/Isomap/UMAP/t-SNE/MDS with MVData API)
- For spatial data visualization: Use `examples/spatial_analysis/spatial_visualization.py`

---

## Using Archived Examples

These examples are **not validated** and may not work with the current DRIADA version. If you need similar functionality, please refer to the recommended examples listed above.
