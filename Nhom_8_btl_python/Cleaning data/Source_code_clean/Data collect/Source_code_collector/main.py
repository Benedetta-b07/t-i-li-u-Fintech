
import os
from dotenv import load_dotenv
from loguru import logger
from collector import OpenMeteoCollector


def select_mode():
    """
    Chọn chế độ chạy trực tiếp bằng input():
    - 1 (hoặc 'test'): Chỉ lấy dữ liệu 1 ngày (2026-09-01), ghi ra thư mục ./test_output
    - 2 (hoặc Enter):  Chạy đầy đủ theo khoảng thời gian trong .env
    """
    print("Chọn chế độ chạy chương trình:")
    print("  1. Chế độ thử nghiệm (1 ngày: 2026-09-01, ghi ra ./test_output)")
    print("  2. Chế độ chạy đầy đủ (61 ngày)")

    while True:
        choice = input("Nhập lựa chọn (1 hoặc 2, mặc định 2): ").strip().lower()
        if choice in ("1", "test", "--test"):
            return True
        if choice in ("2", "full", ""):
            return False
        print("Lựa chọn không hợp lệ. Vui lòng nhập 1 hoặc 2.")


def main():
    # 1. Tải cấu hình từ file .env
    load_dotenv()

    data_dir = os.getenv("DATA_DIR", "./DATA_raw")
    start_date = os.getenv("START_DATE", "2026-09-01")
    end_date = os.getenv("END_DATE", "2026-10-31")
    timezone = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")
    cache_expire_seconds = int(os.getenv("CACHE_EXPIRE_SECONDS", "3600"))

    # 2. Chọn chế độ
    is_test = select_mode()

    if is_test:
        logger.info("=== CHẾ ĐỘ THỬ NGHIỆM (TEST) ===")
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
        return

    # 4. Bước 1: Đọc và kiểm tra tọa độ từ LOCATION.csv
    try:
        df_locations = collector.load_locations()
    except Exception as e:
        logger.error(f"Kiểm tra tọa độ thất bại: {e}")
        logger.error("Dừng chương trình và KHÔNG gọi API!")
        return

    # 5. Bước 2: Gọi API Thời tiết (1 lượt cho cả 5 điểm)
    try:
        updated_locations, df_weather = collector.fetch_weather(df_locations)
    except Exception as e:
        logger.error(f"Lỗi khi thu thập dữ liệu thời tiết: {e}")
        logger.error("Dừng chương trình và KHÔNG ghi file CSV dở dang!")
        return

    # 6. Bước 3: Gọi API Chất lượng không khí (1 lượt cho cả 5 điểm)
    try:
        df_aq = collector.fetch_air_quality(df_locations)
    except Exception as e:
        logger.error(f"Lỗi khi thu thập dữ liệu chất lượng không khí: {e}")
        logger.error("Dừng chương trình và KHÔNG ghi file CSV dở dang!")
        return

    # 7. Bước 4: Ghi dữ liệu ra CSV (chỉ ghi khi cả hai lượt gọi API đều thành công)
    try:
        collector.save_csv(updated_locations, df_weather, df_aq, output_dir=output_dir)
        logger.success(f"Đã lưu thành công toàn bộ dữ liệu vào '{output_dir}'.")
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu vào CSV: {e}")
        return

    # 8. Bước 5: Kiểm tra và in báo cáo dữ liệu thu thập
    try:
        collector.validate_and_report(df_weather, df_aq, is_test=is_test)
    except Exception as e:
        logger.warning(f"Lỗi trong quá trình kiểm tra và in báo cáo: {e}")

    logger.success("Chương trình hoàn thành xuất sắc!")


if __name__ == "__main__":
    main()