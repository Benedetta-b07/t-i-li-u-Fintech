"""
collector.py - Mô-đun thu thập dữ liệu thời tiết và chất lượng không khí từ Open-Meteo API.
Thiết kế đơn giản, dễ hiểu phục vụ bài tập lớn môn Lập trình Python.
"""

import os
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry
from loguru import logger

# Bảng ánh xạ biến API thời tiết -> Tên cột trong WEATHER_RECORD.csv
# Định nghĩa duy nhất 1 từ điển để đảm bảo thứ tự gọi và thứ tự đọc luôn khớp nhau
WEATHER_VARIABLES = {
    "temperature_2m": "TEMPERATURE",
    "relative_humidity_2m": "HUMIDITY",
    "wind_speed_10m": "WIND_SPEED",
    "wind_direction_10m": "WIND_DIRECTION",
    "precipitation": "PRECIPITATION",
    "pressure_msl": "PRESSURE",
}

# Bảng ánh xạ biến API chất lượng không khí -> Tên cột trong AIRQUALITY_RECORD.csv
AIRQUALITY_VARIABLES = {
    "us_aqi": "AQI",
    "pm2_5": "PM2_5",
    "pm10": "PM10",
    "carbon_monoxide": "CO",
    "nitrogen_dioxide": "NO2",
    "sulphur_dioxide": "SO2",
    "ozone": "O3",
}

# Giới hạn tọa độ hợp lý của Quận Hà Đông (Hà Nội)
LAT_MIN, LAT_MAX = 20.85, 21.10
LON_MIN, LON_MAX = 105.60, 105.90


class OpenMeteoCollector:
    """
    Lớp OpenMeteoCollector chịu trách nhiệm:
    1. Đọc và kiểm tra tọa độ các điểm từ LOCATION.csv
    2. Gọi Open-Meteo API (2 lượt: 1 thời tiết, 1 chất lượng không khí)
    3. Tạo DataFrame và định dạng thời gian giờ địa phương UTC+7
    4. Ghi dữ liệu gốc ra CSV khi cả 2 lượt gọi thành công
    5. Kiểm tra chất lượng dữ liệu và in báo cáo chi tiết
    """

    def __init__(self, data_dir="./file_CSV", start_date="2026-09-01", 
                 end_date="2026-10-31", timezone="Asia/Ho_Chi_Minh", 
                 cache_expire_seconds=3600):
        self.data_dir = data_dir
        self.start_date = start_date
        self.end_date = end_date
        self.timezone = timezone
        self.cache_expire_seconds = cache_expire_seconds

        # Thiết lập Open-Meteo client có cơ chế cache và tự động thử lại khi lỗi (retry)
        # theo đúng hướng dẫn trong usage_meteoAPI.txt
        cache_session = requests_cache.CachedSession(".cache", expire_after=self.cache_expire_seconds)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)

    def load_locations(self):
        """
        Đọc tọa độ 5 điểm từ LOCATION.csv và kiểm tra hợp lệ:
        - Kiểm tra có thiếu giá trị tọa độ không.
        - Kiểm tra tọa độ có nằm trong phạm vi Quận Hà Đông không (vĩ độ 20.85-21.10, kinh độ 105.60-105.90).
        Nếu sai/thiếu, in thông báo rõ ràng bằng tiếng Việt và dừng chương trình.
        """
        location_file = os.path.join(self.data_dir, "LOCATION.csv")
        logger.info(f"Đang đọc danh sách điểm đo từ: {location_file}")

        if not os.path.exists(location_file):
            raise FileNotFoundError(f"Không tìm thấy file tọa độ: {location_file}")

        df_locations = pd.read_csv(location_file, encoding="utf-8-sig")

        # Kiểm tra xem file có dòng dữ liệu nào không
        if df_locations.empty:
            raise ValueError(f"File {location_file} trống, chưa có dữ liệu điểm đo!")

        # Kiểm tra từng điểm đo
        for idx, row in df_locations.iterrows():
            loc_id = row.get("LOCATION_ID", f"Dòng {idx+1}")
            loc_name = row.get("LOCATION_NAME", "Chưa đặt tên")
            lat = row.get("LATITUDE")
            lon = row.get("LONGITUDE")

            # 1. Kiểm tra thiếu tọa độ (NaN hoặc rỗng)
            if pd.isna(lat) or pd.isna(lon):
                msg = f"LỖI: Điểm đo '{loc_name}' (ID: {loc_id}) bị THIẾU tọa độ vĩ độ hoặc kinh độ!"
                logger.error(msg)
                raise ValueError(msg)

            # Chuyển đổi sang float
            try:
                lat = float(lat)
                lon = float(lon)
            except ValueError:
                msg = f"LỖI: Điểm đo '{loc_name}' (ID: {loc_id}) có tọa độ không phải dạng số: lat={lat}, lon={lon}"
                logger.error(msg)
                raise ValueError(msg)

            # 2. Kiểm tra tọa độ có nằm trong khoảng hợp lý của Hà Đông không
            if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
                msg = (f"LỖI: Điểm đo '{loc_name}' (ID: {loc_id}) có tọa độ ({lat}, {lon}) "
                       f"nằm ngoài phạm vi Hà Đông (Vĩ độ: {LAT_MIN}-{LAT_MAX}, Kinh độ: {LON_MIN}-{LON_MAX})!")
                logger.error(msg)
                raise ValueError(msg)

        logger.info(f"Đã kiểm tra thành công {len(df_locations)} điểm đo tại Quận Hà Đông.")
        return df_locations

    def _call_api_with_fallback_tz(self, url, params):
        """
        Gọi API Open-Meteo, nếu lỗi múi giờ Asia/Ho_Chi_Minh thì chuyển sang Asia/Bangkok (cùng UTC+7).
        """
        try:
            return self.openmeteo.weather_api(url, params=params)
        except Exception as e:
            if "timezone" in str(e).lower() and params.get("timezone") == "Asia/Ho_Chi_Minh":
                logger.warning("API không nhận múi giờ Asia/Ho_Chi_Minh, tự động chuyển sang Asia/Bangkok (UTC+7)...")
                params["timezone"] = "Asia/Bangkok"
                return self.openmeteo.weather_api(url, params=params)
            raise e

    def fetch_weather(self, df_locations):
        """
        Gọi API thời tiết 1 lần duy nhất cho toàn bộ các điểm đo.
        Cập nhật độ cao ELEVATION vào DataFrame điểm đo và trả về DataFrame thời tiết.
        """
        logger.info("--- BẮT ĐẦU GỌI API THỜI TIẾT (LƯỢT 1/2) ---")
        url = "https://api.open-meteo.com/v1/forecast"
        
        latitudes = df_locations["LATITUDE"].astype(float).tolist()
        longitudes = df_locations["LONGITUDE"].astype(float).tolist()

        params = {
            "latitude": latitudes,
            "longitude": longitudes,
            "hourly": list(WEATHER_VARIABLES.keys()),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "timezone": self.timezone,
        }

        # Gọi API thời tiết (1 lượt cho cả 5 điểm)
        responses = self._call_api_with_fallback_tz(url, params)
        logger.info(f"Đã nhận phản hồi thời tiết cho {len(responses)} điểm đo.")

        weather_rows = []
        updated_locations = df_locations.copy()

        # Ánh xạ kết quả trả về theo đúng thứ tự tọa độ gửi lên
        for i, response in enumerate(responses):
            loc_id = updated_locations.iloc[i]["LOCATION_ID"]
            
            # Cập nhật ELEVATION từ API thời tiết
            elevation = response.Elevation()
            updated_locations.loc[updated_locations["LOCATION_ID"] == loc_id, "ELEVATION"] = elevation

            hourly = response.Hourly()
            time_start = hourly.Time() + response.UtcOffsetSeconds()
            time_end = hourly.TimeEnd() + response.UtcOffsetSeconds()
            interval = hourly.Interval()

            # Tạo danh sách RECORD_TIME (giờ địa phương UTC+7, không có múi giờ: YYYY-MM-DD HH:MM:SS)
            record_times = pd.date_range(
                start=pd.to_datetime(time_start, unit="s"),
                end=pd.to_datetime(time_end, unit="s"),
                freq=pd.Timedelta(seconds=interval),
                inclusive="left"
            ).strftime("%Y-%m-%d %H:%M:%S")

            # Đọc các biến thời tiết theo đúng thứ tự trong WEATHER_VARIABLES
            point_data = {
                "LOCATION_ID": loc_id,
                "RECORD_TIME": record_times,
            }

            for var_idx, (api_var, col_name) in enumerate(WEATHER_VARIABLES.items()):
                values = hourly.Variables(var_idx).ValuesAsNumpy()
                point_data[col_name] = values

            df_point = pd.DataFrame(point_data)
            weather_rows.append(df_point)

        df_weather = pd.concat(weather_rows, ignore_index=True)
        # Giữ đúng thứ tự các cột theo đặc tả yêu cầu
        cols_order = ["LOCATION_ID", "RECORD_TIME", "TEMPERATURE", "HUMIDITY", 
                      "WIND_SPEED", "WIND_DIRECTION", "PRECIPITATION", "PRESSURE"]
        df_weather = df_weather[cols_order]

        logger.info(f"Thu thập thành công dữ liệu thời tiết: {len(df_weather)} dòng.")
        return updated_locations, df_weather

    def fetch_air_quality(self, df_locations):
        """
        Gọi API chất lượng không khí 1 lần duy nhất cho toàn bộ các điểm đo.
        Trả về DataFrame chất lượng không khí.
        """
        logger.info("--- BẮT ĐẦU GỌI API CHẤT LƯỢNG KHÔNG KHÍ (LƯỢT 2/2) ---")
        url = "https://air-quality-api.open-meteo.com/v1/air-quality"

        latitudes = df_locations["LATITUDE"].astype(float).tolist()
        longitudes = df_locations["LONGITUDE"].astype(float).tolist()

        params = {
            "latitude": latitudes,
            "longitude": longitudes,
            "hourly": list(AIRQUALITY_VARIABLES.keys()),
            "start_date": self.start_date,
            "end_date": self.end_date,
            "timezone": self.timezone,
        }

        # Gọi API chất lượng không khí (1 lượt cho cả 5 điểm)
        responses = self._call_api_with_fallback_tz(url, params)
        logger.info(f"Đã nhận phản hồi chất lượng không khí cho {len(responses)} điểm đo.")

        aq_rows = []

        # Ánh xạ kết quả trả về theo đúng thứ tự tọa độ gửi lên
        for i, response in enumerate(responses):
            loc_id = df_locations.iloc[i]["LOCATION_ID"]

            hourly = response.Hourly()
            time_start = hourly.Time() + response.UtcOffsetSeconds()
            time_end = hourly.TimeEnd() + response.UtcOffsetSeconds()
            interval = hourly.Interval()

            record_times = pd.date_range(
                start=pd.to_datetime(time_start, unit="s"),
                end=pd.to_datetime(time_end, unit="s"),
                freq=pd.Timedelta(seconds=interval),
                inclusive="left"
            ).strftime("%Y-%m-%d %H:%M:%S")

            point_data = {
                "LOCATION_ID": loc_id,
                "RECORD_TIME": record_times,
            }

            for var_idx, (api_var, col_name) in enumerate(AIRQUALITY_VARIABLES.items()):
                values = hourly.Variables(var_idx).ValuesAsNumpy()
                point_data[col_name] = values

            df_point = pd.DataFrame(point_data)
            aq_rows.append(df_point)

        df_aq = pd.concat(aq_rows, ignore_index=True)
        # Giữ đúng thứ tự các cột theo đặc tả yêu cầu
        cols_order = ["LOCATION_ID", "RECORD_TIME", "AQI", "PM2_5", "PM10", "CO", "NO2", "SO2", "O3"]
        df_aq = df_aq[cols_order]

        logger.info(f"Thu thập thành công dữ liệu chất lượng không khí: {len(df_aq)} dòng.")
        return df_aq

    def save_csv(self, df_locations, df_weather, df_aq, output_dir=None):
        """
        Ghi dữ liệu ra CSV:
        - Chỉ ghi sau khi cả hai API đã thu thập thành công.
        - Sắp xếp theo LOCATION_ID rồi RECORD_TIME.
        - Không làm sạch dữ liệu (giữ nguyên gốc, giá trị thiếu để ô trống).
        - Định dạng utf-8-sig, index=False.
        """
        save_dir = output_dir or self.data_dir
        os.makedirs(save_dir, exist_ok=True)

        logger.info(f"Đang ghi kết quả vào thư mục: {save_dir}")

        # Sắp xếp dữ liệu theo yêu cầu
        df_weather_sorted = df_weather.sort_values(by=["LOCATION_ID", "RECORD_TIME"])
        df_aq_sorted = df_aq.sort_values(by=["LOCATION_ID", "RECORD_TIME"])

        # Đường dẫn các file
        loc_path = os.path.join(save_dir, "LOCATION.csv")
        weather_path = os.path.join(save_dir, "WEATHER_RECORD.csv")
        aq_path = os.path.join(save_dir, "AIRQUALITY_RECORD.csv")

        # Ghi các file CSV
        df_locations.to_csv(loc_path, index=False, encoding="utf-8-sig", na_rep="")
        logger.info(f"Đã lưu: {loc_path} (đã cập nhật ELEVATION)")

        df_weather_sorted.to_csv(weather_path, index=False, encoding="utf-8-sig", na_rep="")
        logger.info(f"Đã lưu: {weather_path} ({len(df_weather_sorted)} dòng)")

        df_aq_sorted.to_csv(aq_path, index=False, encoding="utf-8-sig", na_rep="")
        logger.info(f"Đã lưu: {aq_path} ({len(df_aq_sorted)} dòng)")

    def validate_and_report(self, df_weather, df_aq, is_test=False):
        """
        Thực hiện kiểm tra sau khi lấy dữ liệu và in báo cáo theo đúng Mục 8:
        1. Số dòng mỗi điểm và tổng số dòng mỗi file.
        2. Khoảng thời gian nhỏ nhất và lớn nhất của từng điểm.
        3. Số lượng giá trị thiếu (NaN) của từng cột.
        4. Kiểm tra trùng lặp cặp (LOCATION_ID, RECORD_TIME).
        5. Kiểm tra miền giá trị bất thường (HUMIDITY, WIND_DIRECTION, PM2_5, PM10).
        6. So sánh tỷ lệ phần trăm thời điểm trùng giá trị giữa 5 điểm đo.
        """
        print("\n" + "=" * 80)
        print("               BÁO CÁO KIỂM TRA DỮ LIỆU THU THẬP TỪ OPEN-METEO")
        print("=" * 80)

        expected_rows_per_point = 24 if is_test else 1464
        expected_total_rows = expected_rows_per_point * 5

        # ---------------- 1. KIỂM TRA SỐ DÒNG ----------------
        print("\n[1] KIỂM TRA SỐ DÒNG (EXPECTED ROWS):")
        print(f"  - Kỳ vọng mỗi điểm: {expected_rows_per_point} dòng (Tổng 5 điểm: {expected_total_rows} dòng)")
        
        for name, df in [("WEATHER_RECORD", df_weather), ("AIRQUALITY_RECORD", df_aq)]:
            total = len(df)
            status = "ĐẠT" if total == expected_total_rows else f"CHÚ Ý (Kỳ vọng {expected_total_rows})"
            print(f"  * {name}: Tổng {total} dòng -> {status}")
            for loc_id, group in df.groupby("LOCATION_ID"):
                cnt = len(group)
                loc_status = "ĐẠT" if cnt == expected_rows_per_point else "CHƯA KHỚP"
                print(f"      + Điểm {loc_id}: {cnt} dòng [{loc_status}]")

        # ---------------- 2. KHOẢNG THỜI GIAN NHỎ NHẤT VÀ LỚN NHẤT ----------------
        print("\n[2] KHOẢNG THỜI GIAN CỦA TỪNG ĐIỂM (MIN / MAX RECORD_TIME):")
        for loc_id, group in df_weather.groupby("LOCATION_ID"):
            min_t = group["RECORD_TIME"].min()
            max_t = group["RECORD_TIME"].max()
            print(f"  * Điểm {loc_id}: Từ '{min_t}' đến '{max_t}'")

        # ---------------- 3. SỐ GIÁ TRỊ THIẾU (NaN) ----------------
        print("\n[3] SỐ LƯỢNG GIÁ TRỊ THIẾU (NaN) TỪNG CỘT:")
        print("  * File WEATHER_RECORD.csv:")
        for col in df_weather.columns:
            nan_cnt = df_weather[col].isna().sum()
            print(f"      + Cột {col:15s}: {nan_cnt:5d} giá trị NaN ({nan_cnt/len(df_weather)*100:.2f}%)")
        print("  * File AIRQUALITY_RECORD.csv:")
        for col in df_aq.columns:
            nan_cnt = df_aq[col].isna().sum()
            print(f"      + Cột {col:15s}: {nan_cnt:5d} giá trị NaN ({nan_cnt/len(df_aq)*100:.2f}%)")

        # ---------------- 4. KIỂM TRA TRÙNG CẶP (LOCATION_ID, RECORD_TIME) ----------------
        print("\n[4] KIỂM TRA TRÙNG LẶP KHÓA CHÍNH (LOCATION_ID, RECORD_TIME):")
        dup_weather = df_weather.duplicated(subset=["LOCATION_ID", "RECORD_TIME"]).sum()
        dup_aq = df_aq.duplicated(subset=["LOCATION_ID", "RECORD_TIME"]).sum()
        print(f"  * Trùng lặp trong WEATHER_RECORD: {dup_weather} cặp -> " + ("KHÔNG TRÙNG (ĐẠT)" if dup_weather == 0 else "CÓ TRÙNG"))
        print(f"  * Trùng lặp trong AIRQUALITY_RECORD: {dup_aq} cặp -> " + ("KHÔNG TRÙNG (ĐẠT)" if dup_aq == 0 else "CÓ TRÙNG"))

        # ---------------- 5. MIỀN GIÁ TRỊ BẤT THƯỜNG ----------------
        print("\n[5] KIỂM TRA MIỀN GIÁ TRỊ BẤT THƯỜNG:")
        # HUMIDITY ngoài 0 - 100
        invalid_hum = df_weather[(df_weather["HUMIDITY"] < 0) | (df_weather["HUMIDITY"] > 100)]
        print(f"  * HUMIDITY ngoài khoảng 0-100%: {len(invalid_hum)} dòng -> " + ("BÌNH THƯỜNG" if len(invalid_hum) == 0 else "BẤT THƯỜNG"))
        
        # WIND_DIRECTION ngoài 0 - 360
        invalid_wind_dir = df_weather[(df_weather["WIND_DIRECTION"] < 0) | (df_weather["WIND_DIRECTION"] > 360)]
        print(f"  * WIND_DIRECTION ngoài khoảng 0-360 độ: {len(invalid_wind_dir)} dòng -> " + ("BÌNH THƯỜNG" if len(invalid_wind_dir) == 0 else "BẤT THƯỜNG"))
        
        # PM2_5 hoặc PM10 âm
        invalid_pm25 = df_aq[df_aq["PM2_5"] < 0]
        invalid_pm10 = df_aq[df_aq["PM10"] < 0]
        print(f"  * PM2_5 âm (< 0): {len(invalid_pm25)} dòng -> " + ("BÌNH THƯỜNG" if len(invalid_pm25) == 0 else "BẤT THƯỜNG"))
        print(f"  * PM10 âm (< 0): {len(invalid_pm10)} dòng -> " + ("BÌNH THƯỜNG" if len(invalid_pm10) == 0 else "BẤT THƯỜNG"))

        # ---------------- 6. SO SÁNH GIỮA 5 ĐIỂM (TỶ LỆ TRÙNG GIÁ TRỊ) ----------------
        print("\n[6] SO SÁNH TỶ LỆ TRÙNG GIÁ TRỊ GIỮA 5 ĐIỂM ĐO (GRID RESOLUTION CHECK):")
        self._compare_points_similarity(df_weather, "WEATHER_RECORD", 
                                        ["TEMPERATURE", "HUMIDITY", "WIND_SPEED", "WIND_DIRECTION", "PRECIPITATION", "PRESSURE"])
        self._compare_points_similarity(df_aq, "AIRQUALITY_RECORD", 
                                        ["AQI", "PM2_5", "PM10", "CO", "NO2", "SO2", "O3"])
        print("=" * 80 + "\n")

    def _compare_points_similarity(self, df, dataset_name, columns):
        """
        Tính toán tỷ lệ phần trăm các mốc thời gian mà cả 5 điểm có giá trị giống hệt nhau.
        """
        print(f"  * Bảng {dataset_name}:")
        timestamps = df["RECORD_TIME"].unique()
        total_times = len(timestamps)

        for col in columns:
            # Tạo bảng pivot với index là RECORD_TIME, các cột là LOCATION_ID
            pivoted = df.pivot(index="RECORD_TIME", columns="LOCATION_ID", values=col)
            
            # Đếm số hàng mà giá trị min bằng giá trị max (tức cả 5 điểm bằng nhau)
            # Dùng np.isclose hoặc hiệu min-max cực nhỏ để tránh sai số số thực
            identical_rows = (pivoted.max(axis=1) - pivoted.min(axis=1)).abs() < 1e-5
            identical_count = identical_rows.sum()
            ratio = (identical_count / total_times) * 100

            warn = ""
            if ratio >= 90.0:
                warn = " [CẢNH BÁO: Gần như 100% giống nhau do lưới mô hình lớn hơn khoảng cách các phường]"
            print(f"      + Cột {col:15s}: {identical_count:5d}/{total_times} mốc giờ giống hệt ({ratio:6.2f}%){warn}")
