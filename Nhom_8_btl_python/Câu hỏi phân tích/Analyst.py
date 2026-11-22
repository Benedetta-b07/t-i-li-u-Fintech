from pathlib import Path
import numpy as np
import pandas as pd

base_dir = Path("Clean & TrucQuan") if Path("Clean & TrucQuan").exists() else Path(".")


def read_csv_auto(path):
    for enc in ("utf-8-sig", "utf-16", "latin1"):
        try:
            df = pd.read_csv(path, sep=None, engine="python", encoding=enc)
            df.columns = df.columns.str.strip().str.upper()
            return df
        except Exception:
            continue
    raise ValueError(f"Không thể đọc được định dạng của tệp: {path}")


all_csv_data = {
    csv_path.stem.upper(): read_csv_auto(csv_path)
    for csv_path in sorted(base_dir.glob("*.csv"))
}

ward_df = all_csv_data["WARD"]
location_df = all_csv_data["LOCATION"]
weather_df = all_csv_data["WEATHER_CLEAN"]
air_df = all_csv_data["AIRQUALITY_CLEAN"]

for df in all_csv_data.values():
    if "RECORD_TIME" in df.columns:
        df["RECORD_TIME"] = pd.to_datetime(df["RECORD_TIME"])

weather_air_df = pd.merge(
    weather_df,
    air_df,
    on=["LOCATION_ID", "RECORD_TIME"],
    how="outer"
)


cau_1 = (
    weather_df.loc[
        weather_df["LOCATION_ID"] == "L01",
        ["RECORD_TIME", "TEMPERATURE", "HUMIDITY", "WIND_SPEED"]
    ]
    .sort_values(by="RECORD_TIME", ascending=False)
    .reset_index(drop=True)
)


cau_2 = (
    air_df.loc[
        air_df["AQI"] > 100,
        ["LOCATION_ID", "RECORD_TIME", "AQI", "PM2_5"]
    ]
    .sort_values(by=["AQI", "RECORD_TIME"], ascending=[False, False])
    .reset_index(drop=True)
)


cau_3 = (
    weather_air_df[
        ["LOCATION_ID", "RECORD_TIME", "TEMPERATURE", "WIND_SPEED", "PM2_5", "PM10"]
    ]
    .sort_values(by=["RECORD_TIME", "LOCATION_ID"], ascending=[True, True])
    .reset_index(drop=True)
)


mask_sep_oct = (
    (weather_df["RECORD_TIME"] >= "2026-09-01 00:00:00") &
    (weather_df["RECORD_TIME"] <= "2026-10-31 23:59:59")
)
df_sep_oct = weather_df.loc[mask_sep_oct].copy()
df_sep_oct["TUAN_THU"] = df_sep_oct["RECORD_TIME"].dt.isocalendar().week.astype(int)
df_sep_oct["NGAY"] = df_sep_oct["RECORD_TIME"].dt.date

weekly_rain = (
    df_sep_oct.groupby("TUAN_THU", as_index=False)
    .agg(
        TU_NGAY=("NGAY", "min"),
        DEN_NGAY=("NGAY", "max"),
        TONG_LUONG_MUA_MM=("PRECIPITATION", lambda s: round(s.sum(), 2)),
        SO_GIO_CO_MUA=("PRECIPITATION", lambda s: int((s > 0).sum()))
    )
)

avg_weekly_rain = weekly_rain["TONG_LUONG_MUA_MM"].mean()
weekly_rain["TRUNG_BINH_TUAN"] = round(avg_weekly_rain, 2)

cau_4 = (
    weekly_rain.loc[weekly_rain["TONG_LUONG_MUA_MM"] > 1.5 * avg_weekly_rain]
    .sort_values(by="TONG_LUONG_MUA_MM", ascending=False)
    .reset_index(drop=True)
)


df_q5 = pd.merge(weather_air_df, location_df, on="LOCATION_ID", how="left")

cau_5 = (
    df_q5.loc[
        (df_q5["WIND_SPEED"] < 3) &
        (df_q5["HUMIDITY"] > 85) &
        (df_q5["PM2_5"] > 75),
        ["LOCATION_NAME", "RECORD_TIME", "WIND_SPEED", "HUMIDITY", "PM2_5", "AQI"]
    ]
    .sort_values(by="PM2_5", ascending=False)
    .reset_index(drop=True)
)


df_q6 = weather_air_df.copy()

conditions = [
    (df_q6["PRECIPITATION"] == 0) & (df_q6["WIND_SPEED"] < 5),
    (df_q6["PRECIPITATION"] > 2) | (df_q6["WIND_SPEED"] > 15)
]
choices = [
    "1. Khô ráo, lặng gió (Tích tụ bụi)",
    "2. Mưa lớn hoặc gió mạnh (Rửa trôi bụi)"
]
df_q6["TRANG_THAI_THOI_TIET"] = np.select(
    conditions,
    choices,
    default="3. Thời tiết trung bình"
)

cau_6 = (
    df_q6.groupby("TRANG_THAI_THOI_TIET", as_index=False)
    .agg(
        SO_BAN_GHI_GIO=("RECORD_TIME", "count"),
        TRUNG_BINH_PM2_5=("PM2_5", lambda s: round(s.mean(), 2)),
        TRUNG_BINH_PM10=("PM10", lambda s: round(s.mean(), 2))
    )
    .sort_values(by="TRANG_THAI_THOI_TIET", ascending=True)
    .reset_index(drop=True)
)


weather_with_date = weather_df.copy()
weather_with_date["NGAY"] = weather_with_date["RECORD_TIME"].dt.date

daily_temp_amp = (
    weather_with_date.groupby(["LOCATION_ID", "NGAY"], as_index=False)
    .agg(BIEN_DO_NHIET_NGAY=("TEMPERATURE", lambda s: s.max() - s.min()))
)

df_q7 = (
    ward_df.merge(location_df, on="WARD_ID", how="left")
    .merge(weather_with_date, on="LOCATION_ID", how="left")
    .merge(air_df, on=["LOCATION_ID", "RECORD_TIME"], how="left")
    .merge(daily_temp_amp, on=["LOCATION_ID", "NGAY"], how="left")
)

cau_7 = (
    df_q7.groupby(["WARD_ID", "WARD_NAME"], as_index=False)
    .agg(
        BIEN_DO_NHIET_MAX_TRONG_NGAY=("BIEN_DO_NHIET_NGAY", lambda s: round(s.max(), 2)),
        TOC_DO_GIO_TRUNG_BINH=("WIND_SPEED", lambda s: round(s.mean(), 2)),
        TONG_SO_GIO_O_NHIEM=("AQI", lambda s: int((s > 100).sum()))
    )
    .drop(columns=["WARD_ID"])
    .sort_values(
        by=["TONG_SO_GIO_O_NHIEM", "BIEN_DO_NHIET_MAX_TRONG_NGAY"],
        ascending=[False, False]
    )
    .reset_index(drop=True)
)


if __name__ == "__main__":
    export_dir = base_dir / "output"
    export_dir.mkdir(parents=True, exist_ok=True)

    seven_files = {
        "cau_1.csv": cau_1,
        "cau_2.csv": cau_2,
        "cau_3.csv": cau_3,
        "cau_4.csv": cau_4,
        "cau_5.csv": cau_5,
        "cau_6.csv": cau_6,
        "cau_7.csv": cau_7,
    }

    for filename, df_result in seven_files.items():
        output_path = export_dir / filename
        df_result.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"Đã xuất: {output_path} ({len(df_result)} dòng)")