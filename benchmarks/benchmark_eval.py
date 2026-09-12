import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (
    accuracy_score, precision_score, f1_score,
    mean_absolute_error, mean_squared_error
)

# ---------------------------------------------------------
# 1. Read CSV from Benchmark Directory Path
# ---------------------------------------------------------
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "cyclone_dataset_5000.csv")
df = pd.read_csv(csv_file_path)

print(f"[OK] Successfully loaded dataset from:")
print(f"    {csv_file_path}")
print(f"    Total Rows: {len(df):,} | Total Columns: {len(df.columns)}")

# ---------------------------------------------------------
# 2. Linear Regression (Pressure as Dependent, Wind as Independent)
# ---------------------------------------------------------
X = df[["wind_speed"]]     # INDEPENDENT VARIABLE (Input Feature)
y = df["pressure"]         # DEPENDENT VARIABLE (Prediction Target)

model = LinearRegression()
model.fit(X, y)
y_pred_reg = model.predict(X)

# ---------------------------------------------------------
# 3. Calculate Regression Metrics (MAE, MSE, RMSE)
# ---------------------------------------------------------
mae  = mean_absolute_error(y, y_pred_reg)
mse  = mean_squared_error(y, y_pred_reg)
rmse = np.sqrt(mse)

# ---------------------------------------------------------
# 4. Calculate Classification Metrics (Accuracy, Precision, F1)
# ---------------------------------------------------------
y_pred_cls = (y_pred_reg <= 983).astype(int)

acc  = accuracy_score(df["is_severe"], y_pred_cls) * 100
prec = precision_score(df["is_severe"], y_pred_cls, zero_division=0) * 100
f1   = f1_score(df["is_severe"], y_pred_cls, zero_division=0) * 100

# ---------------------------------------------------------
# 5. Display All Numerical Results
# ---------------------------------------------------------
print("=" * 65)
print("                  METRICS EVALUATION RESULTS")
print("=" * 65)
print(f"File Path:                {csv_file_path}")
print(f"Total Rows:               {len(df):,} samples")
print(f"Independent Variable (X): wind_speed (knots)")
print(f"Dependent Variable (y):   pressure (hPa)")
print("-" * 65)
print(f"Accuracy:   {acc:.2f}%")
print(f"Precision:  {prec:.2f}%")
print(f"F1 Score:   {f1:.2f}%")
print(f"MAE:        {mae:.2f} hPa")
print(f"MSE:        {mse:.2f} hPa^2")
print(f"RMSE:       {rmse:.2f} hPa")
print(f"Linear Reg: Pressure = ({model.coef_[0]:.2f} * wind_speed) + {model.intercept_:.2f}")
print("=" * 65)

# ---------------------------------------------------------
# 6. Correlation Matrix & Heat Map Visualization
# ---------------------------------------------------------
numeric_cols = ["latitude", "longitude", "wind_speed", "pressure", "pressure_drop", "forward_speed_kmh", "is_severe"]
correlation_matrix = df[numeric_cols].corr()

print("\nCorrelation Matrix:")
print(correlation_matrix.round(2))

plt.figure(figsize=(9, 7))
sns.heatmap(
    correlation_matrix, 
    annot=True, 
    cmap="coolwarm", 
    fmt=".2f", 
    linewidths=0.5,
    cbar=True
)
plt.title(f"Correlation Heat Map ({len(df):,} Rows)", fontsize=12, fontweight="bold")
plt.tight_layout()

output_chart_path = os.path.join(script_dir, "cyclone_5000_correlation_heatmap.png")
plt.savefig(output_chart_path, dpi=300)
plt.close()
print(f"\n[OK] Heat map saved to: {output_chart_path}")