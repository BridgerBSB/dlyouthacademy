###############################################################################
# 1. Install/Import Required Packages
###############################################################################
# Make sure to install the following if you haven't:
#   pip install sqlalchemy pymysql pandas numpy matplotlib seaborn

import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import seaborn as sns

###############################################################################
# 2. Create a SQLAlchemy Engine and Fetch Data
###############################################################################
# Replace placeholders with your actual credentials
host = classified
port = classified
user = classified
password = classified
database = classified

# This string uses the 'mysql+mysqlconnector' or 'mysql+pymysql' dialect;
# either will work, provided the appropriate driver is installed (pymysql or mysql-connector).
engine_str = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
# Alternatively: engine_str = f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"

engine = create_engine(engine_str)

# Write your query
hp_query = "SELECT * FROM `hp_data`.`hp_tests`;"

# Fetch data into a pandas DataFrame using SQLAlchemy only
df_raw = pd.read_sql(hp_query, con=engine)

###############################################################################
# 3. Data Wrangling (Replicate Your R Logic)
###############################################################################
# -- Step 1: Remove rows where peak_takeoff_force_[n]_mean_pp is NA --
df = df_raw.dropna(subset=["peak_takeoff_force_[n]_mean_pp"])

# -- Step 2: Keep only rows where the athlete_name appears more than once --
df["name_count"] = df.groupby("athlete_name")["athlete_name"].transform("size")
df = df[df["name_count"] > 1].copy()

# -- Focus columns --
df = df[["athlete", "athlete_name", "test_date", "peak_takeoff_force_[n]_mean_pp"]]

# -- Convert test_date to datetime --
df["test_date"] = pd.to_datetime(df["test_date"], format="%Y-%m-%d", errors="coerce")

# -- Sort by athlete_name and test_date --
df.sort_values(by=["athlete_name", "test_date"], inplace=True)

# -- Step 3: Remove selected athlete names --
names_to_remove = [
    "Zack Jones", "Dylan Gargas", "Logan Kniss", "Alexander Combs",
    "Dan Swain", "Shio Enomoto", "Jackson Sigman", "Cade Johnson", "Brice Crider",
    "Connor White", "Brett Cook", "Abigayle Darula", 
    "Conner Watson", "Tyler Kozlowski"
]
df = df[~df["athlete_name"].isin(names_to_remove)].copy()

# Drop the helper column
df.drop(columns=["name_count"], inplace=True, errors="ignore")

###############################################################################
# 4. Identify 1st, 2nd, 3rd, 4th Tests per Athlete & Calculate Differences
###############################################################################
def nth_peak_force(group, n):
    """
    Return the nth peak_takeoff_force_[n]_mean_pp for the group 
    if the n-th test exists, else NaN.
    """
    if len(group) >= n:
        return group.iloc[n-1]["peak_takeoff_force_[n]_mean_pp"]
    else:
        return np.nan

# Apply this function to each athlete group
df_grouped = (
    df.groupby("athlete_name")
    .apply(lambda g: pd.Series({
        "Test1": nth_peak_force(g, 1),
        "Test2": nth_peak_force(g, 2),
        "Test3": nth_peak_force(g, 3),
        "Test4": nth_peak_force(g, 4)
    }))
    .reset_index()
)

# Calculate differences
df_grouped["diff_1_2"] = df_grouped["Test2"] - df_grouped["Test1"]
df_grouped["diff_1_3"] = df_grouped["Test3"] - df_grouped["Test1"]
df_grouped["diff_1_4"] = df_grouped["Test4"] - df_grouped["Test1"]

avg_1_2 = df_grouped["diff_1_2"].mean(skipna=True)
avg_1_3 = df_grouped["diff_1_3"].mean(skipna=True)
avg_1_4 = df_grouped["diff_1_4"].mean(skipna=True)

print("Average Increase from Test1 to Test2:", avg_1_2)
print("Average Increase from Test1 to Test3:", avg_1_3)
print("Average Increase from Test1 to Test4:", avg_1_4)

###############################################################################
# 4A. Remove Outliers from the Differences (±3 std dev)
###############################################################################
# We do this for each difference column individually.
# Any row that is outside ±3 std dev for a given difference is dropped.

for diff_col in ["diff_1_2", "diff_1_3", "diff_1_4"]:
    mean_val = df_grouped[diff_col].mean(skipna=True)
    std_val  = df_grouped[diff_col].std(skipna=True)
    lower_bound = mean_val - 3 * std_val
    upper_bound = mean_val + 3 * std_val
    
    # Keep only rows whose diff_col is within [lower_bound, upper_bound]
    df_grouped = df_grouped[
        (df_grouped[diff_col] >= lower_bound) &
        (df_grouped[diff_col] <= upper_bound)
    ].copy()

# After removing outliers, recalculate averages
avg_1_2 = df_grouped["diff_1_2"].mean(skipna=True)
avg_1_3 = df_grouped["diff_1_3"].mean(skipna=True)
avg_1_4 = df_grouped["diff_1_4"].mean(skipna=True)

print("Average Increase from Test1 to Test2 (post-outlier-removal):", avg_1_2)
print("Average Increase from Test1 to Test3 (post-outlier-removal):", avg_1_3)
print("Average Increase from Test1 to Test4 (post-outlier-removal):", avg_1_4)

# ###############################################################################
# # 4B. Print How Many Rows Went Into Each Bar
# ###############################################################################
# print(f"\nNumber of data points for diff_1_2 (Test1→Test2): {count_1_2}")
# print(f"Number of data points for diff_1_3 (Test1→Test3): {count_1_3}")
# print(f"Number of data points for diff_1_4 (Test1→Test4): {count_1_4}\n")

# print(f"Average Increase (Test1→Test2): {avg_1_2}")
# print(f"Average Increase (Test1→Test3): {avg_1_3}")
# print(f"Average Increase (Test1→Test4): {avg_1_4}")

###############################################################################
# 5. Create the Bar + Line Chart
###############################################################################
x_labels = ["1st Retest", "2nd Retest", "3rd Retest"]
y_values = [avg_1_2, avg_1_3, avg_1_4]

plt.figure(figsize=(8, 6))

# Bar plot
sns.barplot(x=x_labels, y=y_values, color="skyblue")

# Line plot on top
sns.lineplot(x=x_labels, y=y_values, color="red", marker="o")

plt.title("Avg Increase in Plyo Push Up Peak Takeoff Force Over Multiple Assessments")
plt.xlabel("Assessment Number")
plt.ylabel("Average Increase in Peak Takeoff Force (N)")
plt.ylim(bottom=0)  # Start y-axis at 0 for clarity (optional)

plt.tight_layout()
plt.show()
