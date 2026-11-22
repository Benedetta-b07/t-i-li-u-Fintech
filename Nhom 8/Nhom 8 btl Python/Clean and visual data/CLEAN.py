import pandas as pd
class WeatherDataCleaner:
    def __init__(self, raw_weather_df, numeric_cols=None):
        self.df = raw_weather_df.copy()
        self.numeric_cols = numeric_cols or [
            "TEMPERATURE",
            "HUMIDITY",
            "WIND_SPEED",
            "PRESSURE",
            "WIND_DIRECTION",
        ]
    def clean(self):
        initial_rows = len(self.df)
        print("Đang làm sạch dữ liệu WEATHER_RECORD...")
        self.df["RECORD_TIME"] = pd.to_datetime(
            self.df["RECORD_TIME"], errors="coerce"
        )
        before = len(self.df)
        self.df = self.df.dropna(subset=["RECORD_TIME", "LOCATION_ID"])
        null_rows = before - len(self.df)
    
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=["LOCATION_ID", "RECORD_TIME"])
        duplicate_rows = before - len(self.df)

        self.df[self.numeric_cols] = self.df[self.numeric_cols].apply(
            pd.to_numeric, errors="coerce"
        )
        before = len(self.df)
        self.df = self.df.dropna(subset=self.numeric_cols)
        missing_rows = before - len(self.df)

        self.df["PRECIPITATION"] = pd.to_numeric(
            self.df["PRECIPITATION"], errors="coerce"
        ).fillna(0.0)
        before = len(self.df)
        self.df = self.df[
            (self.df["WIND_SPEED"] >= 0) & (self.df["PRECIPITATION"] >= 0)
        ]
        invalid_rows = before - len(self.df)
        final_rows = len(self.df)
        dropped_rows = initial_rows - final_rows
        drop_rate = (dropped_rows / initial_rows) * 100 if initial_rows > 0 else 0
        print(
            f"Ban đầu: {initial_rows} dòng | Còn lại: {final_rows} dòng | Loại"
            f" bỏ: {dropped_rows} dòng ({drop_rate:.2f}%)"
        )
        print(f"  - Dòng null: {null_rows} dòng")
        print(f"  - Dòng trùng lặp: {duplicate_rows} dòng")
        print(f"  - Dòng thiếu/lỗi dữ liệu: {missing_rows} dòng")
        print(f"  - Dòng giá trị âm không hợp lệ: {invalid_rows} dòng")
        if drop_rate > 30:
            print(
                "CẢNH BÁO: Tỷ lệ mất mát dữ liệu thời tiết vượt quá ngưỡng 30%!"
            )
        return self.df
class AirQualityCleaner:
    def __init__(self, raw_air_df, target_cols=None):
        self.df = raw_air_df.copy()
        self.target_cols = target_cols or ["PM2_5", "PM10", "AQI"]
    def clean(self):
        initial_rows = len(self.df)
        print("\nĐang làm sạch dữ liệu AIRQUALITY_RECORD...")
        self.df["RECORD_TIME"] = pd.to_datetime(
            self.df["RECORD_TIME"], errors="coerce"
        )
        before = len(self.df)
        self.df = self.df.dropna(subset=["RECORD_TIME", "LOCATION_ID"])
        null_rows = before - len(self.df)

        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=["LOCATION_ID", "RECORD_TIME"])
        duplicate_rows = before - len(self.df)

        self.df[self.target_cols] = self.df[self.target_cols].apply(
            pd.to_numeric, errors="coerce"
        )
        before = len(self.df)
        self.df = self.df.dropna(subset=self.target_cols)
        missing_rows = before - len(self.df)

        before = len(self.df)
        for col in self.target_cols:
            self.df = self.df[self.df[col] >= 0]
        invalid_rows = before - len(self.df)
        final_rows = len(self.df)
        dropped_rows = initial_rows - final_rows
        drop_rate = (dropped_rows / initial_rows) * 100 if initial_rows > 0 else 0
        print(
            f"Ban đầu: {initial_rows} dòng | Còn lại: {final_rows} dòng | Loại"
            f" bỏ: {dropped_rows} dòng ({drop_rate:.2f}%)"
        )
        print(f"  - Dòng null: {null_rows} dòng")
        print(f"  - Dòng trùng lặp: {duplicate_rows} dòng")
        print(f"  - Dòng thiếu/lỗi dữ liệu: {missing_rows} dòng")
        print(f"  - Dòng giá trị âm không hợp lệ: {invalid_rows} dòng")
        if drop_rate > 30:
            print(
                "CẢNH BÁO: Tỷ lệ mất mát dữ liệu không khí vượt quá ngưỡng 30%!"
            )
        return self.df
if __name__ == "__main__":
    try:
        raw_weather = pd.read_csv("WEATHER_RECORD.csv")
        raw_air = pd.read_csv("AIRQUALITY_RECORD.csv")
        clean_weather = WeatherDataCleaner(raw_weather).clean()
        clean_air = AirQualityCleaner(raw_air).clean()
        clean_weather.to_csv("WEATHER_CLEAN.csv", index=False)
        clean_air.to_csv("AIRQUALITY_CLEAN.csv", index=False)
        print(
            "\nHoàn tất! Đã xuất WEATHER_CLEAN.csv và AIRQUALITY_CLEAN.csv."
        )
    except FileNotFoundError as e:
        print(f"Không tìm thấy file CSV: {e}")