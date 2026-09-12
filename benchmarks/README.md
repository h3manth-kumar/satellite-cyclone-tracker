# CycloneAI: Datasets & Statistical Benchmarks

This directory contains benchmark datasets, statistical analysis notebooks, evaluation scripts, and performance artifacts for the CycloneAI project.

---

## Directory Contents

| File | Description |
|---|---|
| `cyclone_dataset_5000.csv` | Dataset containing 5,000 synthetic & historical cyclone observation records (latitude, longitude, wind speed, central pressure, pressure drop, forward motion speed, severity class). |
| `benchmark_eval.py` | Standalone Python evaluation script for linear regression pressure modeling, severity classification metrics (Accuracy, Precision, F1), and correlation matrix visualization. |
| `cycloneai_benchmark_colab.ipynb` | Google Colab Jupyter Notebook for interactive exploratory data analysis (EDA), regression benchmarks, and visual explainability. |
| `cycloneai_colab_benchmark.py` | Python script optimized for executing benchmark pipelines in headless/cloud environments. |
| `cyclone_statistical_results.json` | JSON output containing regression coefficients, MAE, MSE, RMSE, and F1 metrics. |
| `cycloneai_benchmark_metrics.json` | Summary performance benchmarks across multi-lead forecasting horizons. |
| `cycloneai_benchmark_predictions.csv` | Model validation predictions vs ground truth. |
| `cyclone_5000_correlation_heatmap.png` | Feature correlation matrix heatmap. |
| `cycloneai_benchmark_charts.png` | Benchmark metric comparative charts. |
| `correlation_heatmap.png` | Baseline correlation heatmap. |

---

## Running the Benchmark

```bash
python benchmarks/benchmark_eval.py
```

### Evaluated Metrics
* **Regression**: Mean Absolute Error (MAE), Mean Squared Error (MSE), Root Mean Squared Error (RMSE) for Central Pressure estimation.
* **Classification**: Accuracy, Precision, F1 Score for Severe Cyclone categorization ($P \le 983\text{ hPa}$).
* **Explainability**: Pearson correlation heatmaps between spatial, kinematic, and barometric variables.
