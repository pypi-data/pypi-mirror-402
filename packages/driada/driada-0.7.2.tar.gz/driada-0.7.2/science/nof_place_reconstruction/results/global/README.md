# Global Analysis Results

This folder contains aggregated results across all recording sessions.

## Data Files

### all_sessions_results.csv
Aggregated dataset combining all 64 sessions (16 animals × 4 days).

**Columns:**
- `animal`: Animal ID (H01, H02, ..., H39)
- `day`: Recording day (1D, 2D, 3D, 4D)
- **Spatial coding metrics (real):**
  - `real_r2`: Position decoding R²
  - `real_spearman_dist`: Spearman distance correlation
  - `real_procrustes_norm`: Procrustes disparity (normalized)
- **Spatial coding metrics (shuffled baseline):**
  - `shuffled_mean`: Mean R² from shuffled controls
  - `shuffled_std`: Std of R² from shuffled controls
  - `shuffled_spearman_mean`: Mean Spearman distance from shuffled
  - `shuffled_spearman_std`: Std of Spearman distance from shuffled
  - `shuffled_procrustes_mean`: Mean Procrustes disparity from shuffled
  - `shuffled_procrustes_std`: Std of Procrustes disparity from shuffled
- **Statistical comparisons:**
  - `p_value`: Permutation test p-value (real vs shuffled)
  - `effect_size`: Cohen's d effect size
- **Recording properties:**
  - `n_neurons`: Number of neurons recorded
  - `n_timepoints`: Number of timepoints (after downsampling)
- **Behavioral metrics:**
  - `pct_near_objects`: % time near objects
  - `pct_locomotion`: % time in locomotion
  - `pct_walk`: % time walking
  - `pct_corners`: % time in corners

## Figures

### combined_metrics.png
**Multi-panel figure (2×2 layout)** showing progression of key metrics across days:
- **Panel A:** R² (position decoding accuracy)
- **Panel B:** Spearman Distance Correlation (distance preservation)
- **Panel C:** Procrustes Disparity (manifold alignment quality)
- **Panel D:** Behavioral Metrics (locomotion, walk, corners, near objects)

Each spatial coding panel shows both real data and shuffled baseline for comparison.

### Individual Progression Plots

**Spatial coding metrics:**
- `progression_real_r2.png`: R² progression
- `progression_real_spearman_dist.png`: Spearman distance progression
- `progression_real_procrustes_norm.png`: Procrustes disparity progression

**Real vs Shuffled comparisons:**
- `progression_real_r2_vs_shuffled.png`
- `progression_real_spearman_dist_vs_shuffled.png`
- `progression_real_procrustes_norm_vs_shuffled.png`

**Behavioral metrics:**
- `progression_pct_locomotion.png`
- `progression_pct_walk.png`
- `progression_pct_corners.png`
- `progression_pct_near_objects.png`

**Recording properties:**
- `progression_n_neurons.png`

## How to Regenerate

1. **Aggregate results from all sessions:**
   ```bash
   python aggregate_results.py
   ```

2. **Generate individual progression plots:**
   ```bash
   python plot_metric_progression.py
   ```

3. **Generate combined multi-panel figure:**
   ```bash
   python plot_combined_metrics.py
   ```

4. **With individual animal trajectories overlaid:**
   ```bash
   python plot_combined_metrics.py --show_individuals
   ```

## Analysis Notes

- All analyses use downsampling factor of 5 (DEFAULT_DOWNSAMPLING)
- UMAP parameters: n_neighbors=100, min_dist=0.8
- Position decoding uses ordinary least squares regression
- Shuffled controls: 10 iterations with randomized cell identities
- Procrustes alignment includes scaling and reflection
- All plots use 300 DPI for publication quality
