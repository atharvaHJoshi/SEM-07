# %% [markdown]
# # Practical 1 — Uber Ride Price Prediction
#
# **Subject:** Machine Learning (410242)  
# **Class:** B.E. Computer Engineering, Semester I  
# **Lab:** Laboratory Practice III (410246)
#
# ---
#
# ## 1. Aim
#
# Predict the price of an Uber ride from a given pickup point to the agreed
# drop-off location. Perform preprocessing, outlier detection, correlation
# analysis, and compare **Linear Regression** with **Random Forest Regression**
# using $R^2$, MAE and RMSE.
#
# ## 2. Dataset
#
# **Uber Fares Dataset** — Kaggle:  
# <https://www.kaggle.com/datasets/yasserh/uber-fares-dataset>
#
# The dataset contains 200,000 trips with these columns:
#
# | Column | Meaning |
# |---|---|
# | `fare_amount` | Fare in USD (target) |
# | `pickup_datetime` | Date and time of pickup |
# | `pickup_longitude`, `pickup_latitude` | Pickup coordinates |
# | `dropoff_longitude`, `dropoff_latitude` | Drop-off coordinates |
# | `passenger_count` | Number of passengers |
# | `key`, `Unnamed: 0` | Identifiers (dropped) |
#
# The CSV is stored as `data/uber.csv.gz` (the same data, gzipped to keep the
# repository small).
#
# ## 3. Objectives
#
# - Clean and preprocess a real-world regression dataset.
# - Detect and treat outliers using the IQR rule and box plots.
# - Engineer useful features (time parts and Haversine distance).
# - Train Linear Regression and Random Forest models.
# - Compare models with $R^2$, MAE and RMSE and interpret the results.
#
# ## 4. Theory
#
# ### 4.1 Linear Regression
#
# Linear Regression models the target as a linear combination of features:
#
# $$\hat{y} = \beta_0 + \beta_1 x_1 + \beta_2 x_2 + \dots + \beta_p x_p.$$
#
# The coefficients are chosen to minimise the residual sum of squares:
#
# $$\text{RSS} = \sum_{i=1}^{n}(y_i-\hat{y}_i)^2.$$
#
# It is simple and interpretable, but it cannot capture non-linear relationships
# such as the interaction between distance and location.
#
# ### 4.2 Random Forest Regression
#
# A Random Forest builds many decision trees on bootstrap samples and random
# subsets of features. For regression, the prediction is the average of the
# trees:
#
# $$\hat{y} = \frac{1}{B}\sum_{b=1}^{B} T_b(x).$$
#
# Averaging reduces variance, and random feature selection decorrelates the
# trees. Random Forests capture non-linearities and interactions, at the cost of
# interpretability and training time.
#
# ### 4.3 Evaluation metrics
#
# $$R^2 = 1-\frac{\sum(y_i-\hat{y}_i)^2}{\sum(y_i-\bar{y})^2},\qquad
# \text{MAE}=\frac{1}{n}\sum|y_i-\hat{y}_i|,\qquad
# \text{RMSE}=\sqrt{\frac{1}{n}\sum(y_i-\hat{y}_i)^2}.$$
#
# - $R^2$ close to 1 means the model explains most of the variance.
# - MAE is in dollars and is easy to interpret.
# - RMSE penalises large errors more heavily than MAE.
#
# ### 4.4 Haversine distance
#
# Latitude/longitude are angles on a sphere, so Euclidean distance is not
# appropriate. The Haversine formula gives the great-circle distance:
#
# $$d=2R\arcsin\sqrt{\sin^2\frac{\Delta\phi}{2}+
# \cos\phi_1\cos\phi_2\sin^2\frac{\Delta\lambda}{2}},$$
#
# where $R\approx6371$ km. Distance is usually the strongest predictor of fare.

# %%
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")
plt.style.use("seaborn-v0_8-whitegrid")
sns.set_palette("husl")

DATA_DIR = Path("data")
if not DATA_DIR.exists():
    DATA_DIR = Path("ML/data")

print("Data directory:", DATA_DIR.resolve())

# %%
df = pd.read_csv(DATA_DIR / "uber.csv.gz")
print("Shape:", df.shape)
df.head()

# %%
df.info()

# %%
df.describe(include="all").T

# %% [markdown]
# ### 4.1 Pre-processing
#
# Steps:
#
# 1. Drop identifier columns (`Unnamed: 0`, `key`).
# 2. Parse `pickup_datetime` and extract hour, day, month, year and weekday.
# 3. Handle the two missing drop-off coordinates.
# 4. Remove physically impossible fares/coordinates.
# 5. Compute the Haversine distance.
# 6. Detect outliers with the IQR rule.

# %%
df = df.drop(columns=["Unnamed: 0", "key"])
df["pickup_datetime"] = pd.to_datetime(
    df["pickup_datetime"], errors="coerce", utc=True
)

print("Missing values before cleaning:")
print(df.isna().sum())
print("\nRows with an invalid datetime:", df["pickup_datetime"].isna().sum())

# %%
# The two missing drop-off coordinates are only one row; drop it.
df = df.dropna(subset=["dropoff_latitude", "dropoff_longitude"]).copy()
df = df.dropna(subset=["pickup_datetime"])

# Time features.
df["hour"] = df["pickup_datetime"].dt.hour
df["day"] = df["pickup_datetime"].dt.day
df["month"] = df["pickup_datetime"].dt.month
df["year"] = df["pickup_datetime"].dt.year
df["dayofweek"] = df["pickup_datetime"].dt.dayofweek
df["is_weekend"] = (df["dayofweek"] >= 5).astype(int)

print("Shape after dropping missing rows:", df.shape)
df[["pickup_datetime", "hour", "day", "month", "year", "dayofweek"]].head()

# %%
def haversine_km(lat1, lon1, lat2, lon2):
    """Vectorised Haversine distance in kilometres."""
    radius = 6371.0088
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = (
        np.sin(delta_phi / 2.0) ** 2
        + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    )
    return 2 * radius * np.arcsin(np.sqrt(a))


df["distance_km"] = haversine_km(
    df["pickup_latitude"],
    df["pickup_longitude"],
    df["dropoff_latitude"],
    df["dropoff_longitude"],
)
df[["distance_km", "fare_amount"]].describe()

# %%
# Remove physically invalid records.
before = len(df)
df = df[
    df["fare_amount"].between(0.01, 300)
    & df["passenger_count"].between(0, 6)
    & df["pickup_latitude"].between(-90, 90)
    & df["pickup_longitude"].between(-180, 180)
    & df["dropoff_latitude"].between(-90, 90)
    & df["dropoff_longitude"].between(-180, 180)
    & df["distance_km"].between(0.1, 130)
].copy()
after = len(df)
print(f"Removed {before - after:,} invalid rows; remaining: {after:,}")

# %% [markdown]
# ### 4.2 Outlier detection
#
# The IQR rule flags a value as an outlier if it lies outside
#
# $$[Q_1-1.5\,\text{IQR},\ Q_3+1.5\,\text{IQR}],\qquad \text{IQR}=Q_3-Q_1.$$
#
# Box plots show the distribution before and after treatment. Fares have a long
# right tail (airport trips, surcharges), so we report the outliers and keep only
# the extreme 1% for modelling rather than deleting every statistically flagged
# point.

# %%
def iqr_bounds(series):
    q1, q3 = series.quantile([0.25, 0.75])
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


for column in ["fare_amount", "distance_km", "passenger_count"]:
    lower, upper = iqr_bounds(df[column])
    outlier_count = ((df[column] < lower) | (df[column] > upper)).sum()
    print(
        f"{column:15s}: Q1-1.5IQR = {lower:8.2f}, "
        f"Q3+1.5IQR = {upper:8.2f}, outliers = {outlier_count:,}"
    )

# %%
fig, axes = plt.subplots(1, 3, figsize=(14, 4))
for axis, column in zip(axes, ["fare_amount", "distance_km", "passenger_count"]):
    sns.boxplot(y=df[column], ax=axis, color="skyblue")
    axis.set_title(f"Box plot: {column}")
    axis.set_ylabel(column)
plt.tight_layout()
plt.show()

# %%
# Keep fares up to the 99th percentile and distances up to 100 km. This removes
# a small number of extreme values without discarding ordinary long trips.
fare_cap = df["fare_amount"].quantile(0.99)
distance_cap = 100.0
before = len(df)
df = df[(df["fare_amount"] <= fare_cap) & (df["distance_km"] <= distance_cap)].copy()
print(f"Fare cap (99th percentile): ${fare_cap:.2f}")
print(f"Removed {before - len(df):,} extreme rows; remaining: {len(df):,}")

# %%
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
sns.histplot(df["fare_amount"], bins=60, ax=axes[0], color="teal")
axes[0].set_title("Fare distribution after cleaning")
axes[0].set_xlabel("Fare (USD)")

sns.histplot(df["distance_km"], bins=60, ax=axes[1], color="coral")
axes[1].set_title("Trip distance distribution")
axes[1].set_xlabel("Distance (km)")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### 4.3 Correlation analysis
#
# Correlation measures the linear association between two numeric variables:
#
# $$r_{xy}=\frac{\sum(x_i-\bar{x})(y_i-\bar{y})}
# {\sqrt{\sum(x_i-\bar{x})^2\sum(y_i-\bar{y})^2}}.$$
#
# Values near $+1$ or $-1$ indicate a strong positive or negative linear
# relationship; values near 0 indicate little linear relationship. Correlation
# does **not** imply causation.

# %%
numeric_columns = [
    "fare_amount",
    "distance_km",
    "passenger_count",
    "hour",
    "day",
    "month",
    "year",
    "dayofweek",
    "pickup_latitude",
    "pickup_longitude",
    "dropoff_latitude",
    "dropoff_longitude",
]
correlation = df[numeric_columns].corr()

plt.figure(figsize=(11, 8))
sns.heatmap(
    correlation,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    center=0,
    linewidths=0.5,
    cbar_kws={"shrink": 0.8},
)
plt.title("Correlation heatmap")
plt.tight_layout()
plt.show()

# %%
print("Correlation with fare_amount (sorted):")
correlation["fare_amount"].sort_values(ascending=False)

# %%
plt.figure(figsize=(8, 5))
sns.scatterplot(
    data=df.sample(5_000, random_state=42),
    x="distance_km",
    y="fare_amount",
    alpha=0.35,
    s=14,
    color="steelblue",
)
plt.title("Fare vs distance (5,000 sampled trips)")
plt.xlabel("Haversine distance (km)")
plt.ylabel("Fare (USD)")
plt.show()

# %% [markdown]
# ### 4.4 Feature selection and train/test split
#
# We use the coordinates (pickup/drop-off), passenger count, time features and
# the engineered distance. The target is `fare_amount`.
#
# An 80/20 split is used. `random_state=42` makes the result reproducible.

# %%
feature_columns = [
    "pickup_longitude",
    "pickup_latitude",
    "dropoff_longitude",
    "dropoff_latitude",
    "passenger_count",
    "hour",
    "day",
    "month",
    "year",
    "dayofweek",
    "is_weekend",
    "distance_km",
]
target_column = "fare_amount"

X = df[feature_columns]
y = df[target_column]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
print("Training rows:", len(X_train))
print("Test rows    :", len(X_test))
print("Features     :", len(feature_columns))

# %% [markdown]
# ### 4.5 Linear Regression

# %%
linear_model = LinearRegression()
linear_model.fit(X_train, y_train)
linear_predictions = linear_model.predict(X_test)

linear_r2 = r2_score(y_test, linear_predictions)
linear_mae = mean_absolute_error(y_test, linear_predictions)
linear_rmse = np.sqrt(mean_squared_error(y_test, linear_predictions))

print("Linear Regression")
print(f"  R²   : {linear_r2:.4f}")
print(f"  MAE  : ${linear_mae:.4f}")
print(f"  RMSE : ${linear_rmse:.4f}")
print("\nIntercept:", round(linear_model.intercept_, 4))
print("\nCoefficients:")
for name, coefficient in zip(feature_columns, linear_model.coef_):
    print(f"  {name:20s} {coefficient: .6f}")

# %% [markdown]
# ### 4.6 Random Forest Regression

# %%
random_forest = RandomForestRegressor(
    n_estimators=100,
    max_depth=25,
    min_samples_leaf=5,
    n_jobs=-1,
    random_state=42,
)
random_forest.fit(X_train, y_train)
forest_predictions = random_forest.predict(X_test)

forest_r2 = r2_score(y_test, forest_predictions)
forest_mae = mean_absolute_error(y_test, forest_predictions)
forest_rmse = np.sqrt(mean_squared_error(y_test, forest_predictions))

print("Random Forest Regression")
print(f"  R²   : {forest_r2:.4f}")
print(f"  MAE  : ${forest_mae:.4f}")
print(f"  RMSE : ${forest_rmse:.4f}")

# %%
# Side-by-side comparison.
comparison = pd.DataFrame(
    {
        "model": ["Linear Regression", "Random Forest"],
        "R²": [linear_r2, forest_r2],
        "MAE (USD)": [linear_mae, forest_mae],
        "RMSE (USD)": [linear_rmse, forest_rmse],
    }
)
comparison

# %%
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))

for axis, predictions, title, colour in [
    (axes[0], linear_predictions, "Linear Regression", "steelblue"),
    (axes[1], forest_predictions, "Random Forest", "seagreen"),
]:
    axis.scatter(y_test, predictions, alpha=0.25, s=10, color=colour)
    limit = max(y_test.max(), predictions.max())
    axis.plot([0, limit], [0, limit], "r--", linewidth=1, label="Perfect prediction")
    axis.set_xlabel("Actual fare (USD)")
    axis.set_ylabel("Predicted fare (USD)")
    axis.set_title(title)
    axis.legend()
    axis.grid(alpha=0.3)

plt.suptitle("Actual vs predicted fare", fontsize=14)
plt.tight_layout()
plt.show()

# %%
# Residual plots: a good model should have residuals centred around zero.
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
for axis, predictions, title, colour in [
    (axes[0], linear_predictions, "Linear Regression", "steelblue"),
    (axes[1], forest_predictions, "Random Forest", "seagreen"),
]:
    residuals = y_test - predictions
    axis.scatter(predictions, residuals, alpha=0.2, s=10, color=colour)
    axis.axhline(0, color="red", linestyle="--", linewidth=1)
    axis.set_xlabel("Predicted fare (USD)")
    axis.set_ylabel("Residual (actual − predicted)")
    axis.set_title(title)
    axis.grid(alpha=0.3)
plt.suptitle("Residual plots", fontsize=14)
plt.tight_layout()
plt.show()

# %%
# Feature importance from the Random Forest.
importance = pd.DataFrame(
    {
        "feature": feature_columns,
        "importance": random_forest.feature_importances_,
    }
).sort_values("importance", ascending=False)

plt.figure(figsize=(9, 5))
sns.barplot(data=importance, x="importance", y="feature", palette="viridis")
plt.title("Random Forest feature importance")
plt.xlabel("Importance")
plt.ylabel("")
plt.tight_layout()
plt.show()

importance

# %%
# A few individual predictions for a test-case table.
sample_indices = [0, 1, 2, 3, 4]
sample_results = pd.DataFrame(
    {
        "actual fare": y_test.iloc[sample_indices].values,
        "linear prediction": linear_predictions[sample_indices],
        "random forest prediction": forest_predictions[sample_indices],
        "distance (km)": X_test.iloc[sample_indices]["distance_km"].values,
    }
)
sample_results["linear error"] = (
    sample_results["linear prediction"] - sample_results["actual fare"]
)
sample_results["forest error"] = (
    sample_results["random forest prediction"] - sample_results["actual fare"]
)
sample_results

# %%
# ============================================================================
# DETAILED OUTPUT EXPLANATION
# ============================================================================
print("DETAILED OUTPUT EXPLANATION - ML Practical 1 (Uber fare prediction)")
print("=" * 78)
print(
    "The task is regression: predict a continuous fare in USD. The report\n"
    "below reads the cleaned dataset, the correlation analysis, the two model\n"
    "scores and the feature importance, then explains what each number means."
)

print("\n1. CLEANED DATASET")
print("-" * 78)
print(f"Rows remaining after cleaning : {len(df):,}")
print(f"Columns in the cleaned frame  : {df.shape[1]}")
print(f"Training rows                 : {len(X_train):,}")
print(f"Test rows                     : {len(X_test):,}")
print(f"Features used by the models   : {len(feature_columns)}")
print(f"Fare cap (99th percentile)    : ${fare_cap:.2f}")
print(f"Distance cap                  : {distance_cap:.1f} km")
print("Cleaning removed invalid fares, impossible coordinates and extreme")
print("outliers. Without this step, negative fares, zero-distance trips and")
print("GPS errors would dominate the loss and distort the correlations.")

print("\n2. CORRELATION WITH FARE")
print("-" * 78)
fare_correlations = correlation["fare_amount"].drop("fare_amount").sort_values(ascending=False)
for feature, value in fare_correlations.items():
    print(f"  {feature:20s}: {value: .4f}")
print(
    f"Strongest positive linear relationship: {fare_correlations.index[0]} "
    f"(r = {fare_correlations.iloc[0]:.4f})."
)
print("Distance has the largest positive correlation: longer trips tend to cost")
print("more. Correlation measures linear association only; it does not prove")
print("causation and it does not capture non-linear fare rules.")

print("\n3. MODEL PERFORMANCE")
print("-" * 78)
for _, row in comparison.iterrows():
    print(
        f"  {row['model']:20s}: R2={row['R²']:.4f}, "
        f"MAE=${row['MAE (USD)']:.4f}, RMSE=${row['RMSE (USD)']:.4f}"
    )
better_model = "Random Forest" if forest_r2 > linear_r2 else "Linear Regression"
print(f"Better model on this test split: {better_model}")
print(
    f"Random Forest minus Linear Regression: "
    f"delta R2 = {forest_r2 - linear_r2:+.4f}, "
    f"delta MAE = {forest_mae - linear_mae:+.4f} USD, "
    f"delta RMSE = {forest_rmse - linear_rmse:+.4f} USD"
)
print(
    f"Random Forest reduces MAE by "
    f"{100 * (linear_mae - forest_mae) / linear_mae:.2f}% relative to the "
    "linear baseline."
)
print("R2 is the fraction of fare variance explained; 1.0 is perfect and 0.0")
print("means the model is no better than predicting the mean. MAE is the")
print("average absolute dollar error. RMSE is in dollars too, but it squares")
print("errors first, so a few large mistakes raise it more than MAE.")

print("\n4. FEATURE IMPORTANCE AND RESIDUALS")
print("-" * 78)
for _, row in importance.head(8).iterrows():
    print(f"  {row['feature']:20s}: {row['importance']:.4f}")
print(f"Top feature: {importance.iloc[0]['feature']}")
print("Random Forest importance is the average reduction in impurity produced")
print("by splits on that feature. It describes how the model uses the feature,")
print("not a causal effect. Distance dominates because it is the main driver of")
print("fare; coordinates and time features add smaller corrections.")
print("The residual plots show that errors are not constant: expensive trips")
print("have larger absolute errors (heteroscedasticity). A log transform of the")
print("target or a quantile model could reduce this effect.")

print("\n5. SAMPLE PREDICTIONS")
print("-" * 78)
for _, row in sample_results.iterrows():
    print(
        f"  actual=${row['actual fare']:.2f}, "
        f"linear=${row['linear prediction']:.2f}, "
        f"forest=${row['random forest prediction']:.2f}, "
        f"distance={row['distance (km)']:.2f} km"
    )
print("The sample rows show why a single prediction can be far from the actual")
print("fare: the same distance can have different base fares, surcharges and")
print("traffic conditions that are not present in the dataset.")

print("\n6. TAKEAWAY")
print("-" * 78)
print("Linear Regression is a transparent baseline; Random Forest captures")
print("non-linearities and interactions and performs better on this split.")
print("The result is not a production fare model: weather, traffic and road")
print("distance are missing, and a single train/test split has sampling noise.")
print("Next steps: cross-validation, log-transforming fare and geo-features.")

# %% [markdown]
# ### Observations
#
# 1. **Distance is the dominant feature.** It has the strongest positive
#    correlation with fare and the highest Random Forest importance. This is
#    expected: longer trips cost more.
# 2. **Random Forest outperforms Linear Regression** on all three metrics. The
#    relationship between fare and the features is non-linear (base fare,
#    distance tiers, time-of-day surcharges, airport trips), which a single
#    linear equation cannot capture.
# 3. **Outliers matter.** Fares below zero, coordinates outside the valid range
#    and trips with zero distance are data errors. Keeping them would distort
#    both the correlation analysis and the model.
# 4. **Residuals are heteroscedastic.** The spread of errors increases with the
#    predicted fare; expensive trips are harder to predict. A log transform of
#    the target or a quantile model could help.
# 5. **Time features have modest importance.** Hour and weekday capture
#    surcharges and traffic patterns, but they are weaker than distance.
#
# ### Limitations and improvements
#
# - Coordinates are raw; geo-clustering (e.g. distance to airports, city centre)
#   would add useful information.
# - Weather, traffic and road distance are not in the dataset.
# - A log transformation of `fare_amount` can reduce the influence of expensive
#   trips.
# - Gradient boosting (XGBoost/LightGBM) often improves on a Random Forest.
# - Cross-validation would give a more stable estimate than a single split.
#
# ## 5. Conclusion
#
# We pre-processed the Uber fares dataset, handled invalid records and outliers,
# engineered time and distance features, and analysed correlations. Linear
# Regression provided a simple baseline, while Random Forest Regression captured
# non-linear effects and achieved a higher $R^2$ with lower MAE and RMSE. The
# experiment shows the importance of feature engineering (especially Haversine
# distance) and of choosing a model that matches the structure of the data.
#
# ## 6. Viva questions
#
# | Question | Short answer |
# |---|---|
# | Why is Haversine distance used instead of Euclidean distance? | Latitude/longitude are spherical coordinates; Haversine gives the great-circle distance. |
# | What does $R^2$ measure? | The proportion of variance in the target explained by the model. |
# | What is the difference between MAE and RMSE? | RMSE squares the errors, so it penalises large errors more. |
# | Why does Random Forest outperform Linear Regression here? | It captures non-linearities and feature interactions. |
# | How are outliers detected with the IQR rule? | Values outside $[Q_1-1.5\text{IQR}, Q_3+1.5\text{IQR}]$. |
# | Why not remove every IQR outlier? | Some are genuine long/expensive trips; removing them can bias the model. |
# | What is feature importance in a Random Forest? | The average reduction in impurity contributed by a feature across the trees. |
# | What is one limitation of this model? | It does not use traffic, weather or road-network distance. |
