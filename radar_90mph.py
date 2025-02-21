import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sqlalchemy

# Connect to the database
engine_hp_data = sqlalchemy.create_engine(classified)

# Define the SQL query
query = """
SELECT  
    `body_weight_[lbs]`,
    `peak_power_[w]_mean_cmj`,
    `peak_power_[w]_mean_sj`,
    `best_rsi_(flight/contact_time)_mean_ht`,
    `peak_takeoff_force_[n]_mean_pp`,
    `net_peak_vertical_force_[n]_max_imtp`,
    pitching_max_hss,
    pitch_speed_mph
FROM 
    `hp_data`.`hp_tests`
WHERE 
    pitch_speed_mph >= 90;
"""

# Execute the query and load data into a DataFrame
df_hp_tests = pd.read_sql(query, con=engine_hp_data)

# Compute statistics for 90+ mph throwers
averages_90 = df_hp_tests.drop(columns=["pitch_speed_mph"]).mean(skipna=True)

# Compute statistics for 95+ mph throwers
df_hp_95 = df_hp_tests[df_hp_tests["pitch_speed_mph"] >= 95]
averages_95 = df_hp_95.drop(columns=["pitch_speed_mph"]).mean(skipna=True)

# Compute minimum values excluding 0 and NA
mins = df_hp_tests.replace(0, np.nan).drop(columns=["pitch_speed_mph"]).min(skipna=True)

# Define categories (7 points)
categories = [
    "Body Weight",
    "CMJ Peak Power",
    "SJ Peak Power",
    "Reactive Strength - RSI",
    "Peak Takeoff Force",
    "Net Peak Vertical Force",
    "Pitching Max HSS"
]

# Normalize data for visualization (scale to 0-100)
# mins = mins.fillna(0)  # Replace any remaining NaN values with 0
range_values = averages_90 - mins
range_values[range_values == 0] = 1  # Prevent division by zero in normalization

normalized_avg_90 = ((averages_90 - mins) / range_values) * 100
normalized_avg_95 = ((averages_95 - mins) / range_values) * 100
# normalized_min = np.zeros(len(categories))  # Ensures min values are at 0
normalized_min = ((mins - mins) / range_values) * 100  # Properly normalized min values

# Create angles for radar chart
angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
angles += angles[:1]  # Close the loop

# Convert normalized data into lists for plotting
avg_90_values = np.append(normalized_avg_90.values, normalized_avg_90.values[0])
avg_95_values = np.append(normalized_avg_95.values, normalized_avg_95.values[0])
min_values = np.append(normalized_min.values, normalized_min.values[0])  # Ensure it's correctly formatted

# Create Radar Chart
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

# Plot Min, Avg (90+ mph), and Avg (95+ mph) Data
ax.plot(angles, min_values, linestyle="solid", color="red", linewidth=1, label="MIN")
ax.fill(angles, min_values, color="red", alpha=0.2)

ax.plot(angles, avg_90_values, linestyle="-", color="orange", linewidth=2, label="AVG 90+ MPH")
ax.fill(angles, avg_90_values, color="orange", alpha=0.3)

ax.plot(angles, avg_95_values, linestyle="--", color="blue", linewidth=2, label="AVG 95+ MPH")
ax.fill(angles, avg_95_values, color="blue", alpha=0.3)

# Add labels for each metric at their respective positions
for i, (angle, avg_90, avg_95, min_v) in enumerate(zip(angles[:-1], averages_90, averages_95, mins)):
    ax.text(angle, 105, f"{avg_95:.1f}", color="blue", fontsize=9, ha="center", va="bottom")  # 95+ mph Avg labels
    ax.text(angle, 50, f"{avg_90:.1f}", color="orange", fontsize=9, ha="center", va="bottom")  # 90+ mph Avg labels
    ax.text(angle, -5, f"{min_v:.1f}", color="red", fontsize=9, ha="center", va="top")  # Min labels

# Add labels and title
ax.set_yticklabels([])
ax.set_xticks(angles[:-1])
ax.set_xticklabels(categories, fontsize=10)

plt.title("Average High Performance Metrics of 90+mph Throwers", fontsize=14, fontweight="bold", y=1.1)
plt.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

# Display the radar chart
plt.show()
