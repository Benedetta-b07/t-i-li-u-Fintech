import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.makedirs("output", exist_ok=True)
weather = pd.read_csv("WEATHER_CLEAN.csv")
air = pd.read_csv("AIRQUALITY_CLEAN.csv")
locations = pd.read_csv("LOCATION.csv")

weather["RECORD_TIME"] = pd.to_datetime(weather["RECORD_TIME"])
air["RECORD_TIME"] = pd.to_datetime(air["RECORD_TIME"])

w_start = weather["RECORD_TIME"].min().strftime("%d/%m")
w_end = weather["RECORD_TIME"].max().strftime("%d/%m/%Y")
a_start = air["RECORD_TIME"].min().strftime("%d/%m")
a_end = air["RECORD_TIME"].max().strftime("%d/%m/%Y")
hours_per_loc = int(weather.groupby("LOCATION_ID").size().mean())

#1. Line chart
weather["DATE"] = weather["RECORD_TIME"].dt.date
daily_temp = weather.groupby("DATE")["TEMPERATURE"].agg(["mean", "min", "max"])

fig, ax = plt.subplots(figsize=(9, 4))
ax.plot(
    daily_temp.index,
    daily_temp["mean"],
    marker="o",
    markersize=4,
    color="#2369a0",
    label="Nhiệt độ trung bình",
)
ax.fill_between(
    daily_temp.index,
    daily_temp["min"],
    daily_temp["max"],
    color="#2369a0",
    alpha=0.15,
    label="Biên độ Min - Max trong ngày",
)
ax.set_title(
    f"Nhiệt độ trung bình theo ngày - Hà Đông ({w_start} - {w_end})"
)
ax.set_xlabel("Ngày quan sát")
ax.set_ylabel("Nhiệt độ (°C)")
ax.set_ylim(daily_temp["min"].min() - 1.5, daily_temp["max"].max() + 3.5)
ax.legend(frameon=False, loc="upper right")
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.autofmt_xdate()
fig.text(
    0.01,
    -0.05,
    f"Nguồn: WEATHER_CLEAN.csv ({len(locations)} trạm Hà Đông, {w_start}-{w_end}, N = {len(weather)} giờ).",
    fontsize=8.5,
    color="gray",
)
fig.savefig("output/Biểu đồ 1 - Line chart.png", dpi=160, bbox_inches="tight")
plt.close(fig)

#2. Horizontal bar chart
rain_loc = weather.groupby("LOCATION_ID", as_index=False)["PRECIPITATION"].sum()
rain_loc = pd.merge(
    rain_loc, locations[["LOCATION_ID", "LOCATION_NAME"]], on="LOCATION_ID"
)
rain_loc = rain_loc.sort_values("PRECIPITATION")

fig, ax = plt.subplots(figsize=(9, 4))
bars = ax.barh(rain_loc["LOCATION_NAME"], rain_loc["PRECIPITATION"], color="#2b8b78")
ax.bar_label(bars, fmt="%.1f mm", padding=4, fontsize=9)
ax.set_title(
    f"Tổng lượng mưa tích lũy theo địa điểm ({w_start} - {w_end})"
)
ax.set_xlabel("Tổng lượng mưa (mm)")
ax.set_ylabel("Địa điểm quan trắc")
ax.set_xlim(0, rain_loc["PRECIPITATION"].max() * 1.15)
ax.grid(axis="x", linestyle="--", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.text(
    0.01,
    -0.05,
    f"Nguồn: WEATHER_CLEAN.csv & LOCATION.csv ({w_start}-{w_end}, {hours_per_loc} giờ/trạm).",
    fontsize=8.5,
    color="gray",
)
fig.savefig(
    "output/Biểu đồ 2 - Horizontal bar chart.png", dpi=160, bbox_inches="tight"
)
plt.close(fig)

#3. Histogram
pm25 = air["PM2_5"]
max_bin = max(160, np.ceil(pm25.max() / 10) * 10)
bins = np.arange(0, max_bin + 10, 10)

fig, ax = plt.subplots(figsize=(9, 4))
ax.hist(pm25, bins=bins, color="#7298c6", edgecolor="white")
ax.axvline(
    50,
    color="#2b8b78",
    linestyle="-.",
    label="QCVN 24h: 50 µg/m³",
)
ax.axvline(
    pm25.median(),
    color="red",
    linestyle="--",
    label=f"Trung vị: {pm25.median():.2f} µg/m³",
)
ax.axvline(
    pm25.quantile(0.95),
    color="orange",
    linestyle=":",
    label=f"P95: {pm25.quantile(0.95):.2f} µg/m³",
)
ax.set_title(
    f"Phân bố nồng độ bụi mịn PM2.5 theo giờ - Hà Đông ({a_start} - {a_end})"
)
ax.set_xlabel("Nồng độ PM2.5 (µg/m³)")
ax.set_ylabel("Số giờ quan sát")
ax.legend(frameon=False)
ax.grid(axis="y", linestyle="--", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.text(
    0.01,
    -0.05,
    f"Nguồn: AIRQUALITY_CLEAN.csv ({a_start}-{a_end}, N = {len(pm25)} bản ghi).",
    fontsize=8.5,
    color="gray",
)
fig.savefig("output/Biểu đồ 3 - Histogram.png", dpi=160, bbox_inches="tight")
plt.close(fig)

#4. Scatter plot
r_val = weather["TEMPERATURE"].corr(weather["HUMIDITY"])
m, b = np.polyfit(weather["TEMPERATURE"], weather["HUMIDITY"], 1)
x_line = np.linspace(weather["TEMPERATURE"].min(), weather["TEMPERATURE"].max(), 100)

fig, ax = plt.subplots(figsize=(8, 4.5))
ax.scatter(
    weather["TEMPERATURE"],
    weather["HUMIDITY"],
    alpha=0.25,
    s=14,
    color="#4a7ea8",
    label="Quan sát theo giờ",
)
ax.plot(
    x_line,
    m * x_line + b,
    color="#d9534f",
    linewidth=1.8,
    linestyle="--",
    label="Đường xu hướng tuyến tính",
)
ax.set_title(
    f"Tương quan giữa nhiệt độ và độ ẩm theo giờ ({w_start} - {w_end})\nHệ số tương quan r = {r_val:.2f}"
)
ax.set_xlabel("Nhiệt độ (°C)")
ax.set_ylabel("Độ ẩm (%)")
ax.legend(frameon=False)
ax.grid(True, linestyle="--", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.text(
    0.01,
    -0.05,
    f"Nguồn: WEATHER_CLEAN.csv ({w_start}-{w_end}, N = {len(weather)} bản ghi).",
    fontsize=8.5,
    color="gray",
)
fig.savefig("output/Biểu đồ 4 - Scatter plot.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("WEATHER")
print(weather[["TEMPERATURE", "HUMIDITY", "PRECIPITATION"]].describe().round(2))
print("\nAIRQUALITY")
print(air[["AQI", "PM2_5", "PM10"]].describe().round(2))
print("P95 PM2.5:", round(pm25.quantile(0.95), 2))
print("Hệ số tương quan Nhiệt độ - Độ ẩm (r):", round(r_val, 4))