"""
main.py - Chương trình chính thu thập dữ liệu thời tiết và chất lượng không khí Quận Hà Đông từ Open-Meteo.
Phục vụ bài tập lớn môn Lập trình Python.

Cách chạy:
- Chạy thử nghiệm 1 ngày: python main.py --test
- Chạy đầy đủ 61 ngày:    python main.py
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from loguru import logger
from collector import OpenMeteoCollector


def parse_arguments():
    """
    Xử lý tham số dòng lệnh:
    --test: Chỉ lấy dữ liệu 1 ngày (2026-09-01) để chạy thử nhanh, ghi ra thư mục test_output/
    """
    parser = argparse.ArgumentParser(
        description="Thu thập dữ liệu thời tiết và chất lượng không khí cho 5 phường Quận Hà Đông từ Open-Meteo."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Chế độ thử nghiệm: Chỉ lấy 1 ngày (2026-09-01) và ghi ra thư mục test_output/"
    )
    return parser.parse_args()


def main():
    # 1. Tải cấu hình từ file .env
    load_dotenv()

    data_dir = os.getenv("DATA_DIR", "./file_CSV")
    start_date = os.getenv("START_DATE", "2026-09-01")
    end_date = os.getenv("END_DATE", "2026-10-31")
    timezone = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")
    cache_expire_seconds = int(os.getenv("CACHE_EXPIRE_SECONDS", "3600"))

    # 2. Xử lý tham số dòng lệnh
    args = parse_arguments()
    is_test = args.test

    if is_test:
        logger.info("=== CHẾ ĐỘ THỬ NGHIỆM (--test) ===")
        start_date = "2026-09-01"
        end_date = "2026-09-01"
        output_dir = "./test_output"
        logger.info(f"Thời gian: {start_date} (1 ngày, 24 mốc giờ)")
        logger.info(f"Thư mục xuất kết quả thử nghiệm: {output_dir}")
    else:
        logger.info("=== CHẾ ĐỘ CHẠY ĐẦY ĐỦ (FULL RUN) ===")
        output_dir = data_dir
        logger.info(f"Thời gian: {start_date} đến {end_date} (61 ngày, 1464 mốc giờ)")
        logger.info(f"Thư mục ghi kết quả: {output_dir}")

    logger.info(f"Múi giờ: {timezone} | Thời gian cache: {cache_expire_seconds}s")

    # 3. Khởi tạo đối tượng thu thập dữ liệu
    try:
        collector = OpenMeteoCollector(
            data_dir=data_dir,
            start_date=start_date,
            end_date=end_date,
            timezone=timezone,
            cache_expire_seconds=cache_expire_seconds,
        )
    except Exception as e:
        logger.error(f"Lỗi khởi tạo OpenMeteoCollector: {e}")
        sys.exit(1)

    # 4. Bước 1: Đọc và kiểm tra tọa độ từ LOCATION.csv
    try:
        df_locations = collector.load_locations()
    except Exception as e:
        logger.error(f"Kiểm tra tọa độ thất bại: {e}")
        logger.error("Dừng chương trình và KHÔNG gọi API!")
        sys.exit(1)

    # 5. Bước 2: Gọi API Thời tiết (1 lượt cho cả 5 điểm)
    try:
        updated_locations, df_weather = collector.fetch_weather(df_locations)
    except Exception as e:
        logger.error(f"Lỗi khi thu thập dữ liệu thời tiết: {e}")
        logger.error("Dừng chương trình và KHÔNG ghi file CSV dở dang!")
        sys.exit(1)

    # 6. Bước 3: Gọi API Chất lượng không khí (1 lượt cho cả 5 điểm)
    try:
        df_aq = collector.fetch_air_quality(df_locations)
    except Exception as e:
        logger.error(f"Lỗi khi thu thập dữ liệu chất lượng không khí: {e}")
        logger.error("Dừng chương trình và KHÔNG ghi file CSV dở dang!")
        sys.exit(1)

    # 7. Bước 4: Ghi dữ liệu ra CSV (chỉ ghi khi cả hai lượt gọi API đều thành công)
    try:
        collector.save_csv(updated_locations, df_weather, df_aq, output_dir=output_dir)
        logger.success(f"Đã lưu thành công toàn bộ dữ liệu vào '{output_dir}'.")
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu vào CSV: {e}")
        sys.exit(1)

    # 8. Bước 5: Kiểm tra và in báo cáo dữ liệu thu thập
    try:
        collector.validate_and_report(df_weather, df_aq, is_test=is_test)
    except Exception as e:
        logger.warning(f"Lỗi trong quá trình kiểm tra và in báo cáo: {e}")

    logger.success("Chương trình hoàn thành xuất sắc!")


if __name__ == "__main__":
    main()
