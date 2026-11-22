# Bài Tập Lớn Python - Nhóm 8: Thu thập, Xử lý và Phân tích Dữ liệu Thời tiết & Chất lượng Không khí

Dự án xây dựng quy trình khép kín từ thu thập, làm sạch, trực quan hóa đến phân tích dữ liệu thời tiết và chất lượng không khí (AQI) theo giờ tại 5 phường thuộc **Quận Hà Đông, Thành phố Hà Nội** trong giai đoạn chuyển mùa từ **01/09/2026 đến 31/10/2026** (61 ngày) sử dụng nguồn dữ liệu **Open-Meteo API**.

## 1. Mô tả chức năng chính

Dự án được tổ chức thành 3 module độc lập theo đúng trình tự xử lý dữ liệu:

1. **Thu thập dữ liệu (`Collect data/`)**:

   * Khai thác Open-Meteo API qua hai endpoint độc lập (thời tiết và chất lượng không khí) bằng `collector.py` và `main.py`.

   * Kiểm tra tính hợp lệ của tọa độ 5 điểm quan trắc (`L01`–`L05`) từ `DATA_raw/LOCATION.csv`, hỗ trợ lưu bộ nhớ đệm (`.cache.sqlite`), tự động thử lại khi lỗi mạng (`retry-requests`) và dự phòng múi giờ UTC+7.

   * Hỗ trợ 2 chế độ chạy: **Chế độ thử nghiệm** (1 ngày, lưu vào `test_output/`) và **Chế độ chạy đầy đủ** (61 ngày, lưu vào `DATA_raw/`), đồng thời tự động chạy 6 tiêu chí kiểm thử dữ liệu sau khi tải.

2. **Làm sạch và trực quan hóa dữ liệu (`Clean and visual data/`)**:

   * **Làm sạch (`CLEAN.py`)**: Chuẩn hóa kiểu dữ liệu thời gian và số thực, loại bỏ trùng lặp khóa `(LOCATION_ID, RECORD_TIME)`, lọc các dòng khuyết thiếu liên tiếp ở giai đoạn đầu bảng thời tiết (giữ lại 6.560/7.320 bản ghi) và bảo toàn 100% (7.320 bản ghi) bảng chất lượng không khí; xuất ra `WEATHER_CLEAN.csv` và `AIRQUALITY_CLEAN.csv`.

   * **Trực quan hóa (`TrucQuan.py`)**: Tạo 4 biểu đồ phân tích và lưu vào `Clean and visual data/output/`:

     * **Biểu đồ 1 (`Line chart`)**: Diễn biến nhiệt độ trung bình và biên độ nhiệt theo ngày.

     * **Biểu đồ 2 (`Horizontal bar chart`)**: Tổng lượng mưa tích lũy theo 5 địa điểm quan trắc.

     * **Biểu đồ 3 (`Histogram`)**: Phân bố tần suất nồng độ bụi mịn $PM_{2.5}$ theo giờ kèm ngưỡng QCVN.

     * **Biểu đồ 4 (`Scatter plot`)**: Tương quan nghịch giữa nhiệt độ và độ ẩm theo giờ.

3. **Phân tích chuyên sâu (`Câu hỏi phân tích/`)**:

   * Tập lệnh `Analyst.py` trả lời 7 câu hỏi nghiên cứu và xuất kết quả ra thư mục `Câu hỏi phân tích/output/` (`cau_1.csv` đến `cau_7.csv`):

     * `cau_1.csv`: Lịch sử biến đổi nhiệt độ, độ ẩm, tốc độ gió tại trạm `L01` (Hà Đông).

     * `cau_2.csv`: Danh sách các thời điểm và điểm đo có chất lượng không khí kém/xấu ($AQI > 100$).

     * `cau_3.csv`: Đối chiếu đa chiều giữa thời tiết và nồng độ bụi mịn ($PM_{2.5}$, $PM_{10}$).

     * `cau_4.csv`: Phát hiện các tuần có lượng mưa tăng đột biến (vượt 150% mức trung bình tuần).

     * `cau_5.csv`: Nhận diện các khung giờ tích tụ bụi mịn nghiêm trọng ($PM_{2.5} > 75\ \mu g/m^3$) khi lặng gió và độ ẩm cao.

     * `cau_6.csv`: So sánh hiệu ứng gột rửa ô nhiễm giữa trạng thái khô ráo lặng gió và trạng thái mưa lớn/gió mạnh.

     * `cau_7.csv`: Thống kê tổng hợp và xếp hạng mức độ biến động thời tiết – ô nhiễm theo từng phường.

## 2. Cấu trúc thư mục

```
Nhom 8 btl Python/
├── README.md                               # Tài liệu hướng dẫn dự án
├── requirements.txt                        # Danh sách thư viện Python cần cài đặt
│
├── Collect data/                           # Module 1: Thu thập dữ liệu từ API
│   ├── main.py                             # Điểm khởi chạy chương trình thu thập
│   ├── collector.py                        # Lớp OpenMeteoCollector xử lý API và kiểm thử
│   ├── DATA_raw/                           # Dữ liệu thô thu thập đầy đủ (61 ngày)
│   │   ├── AIRQUALITY_RECORD.csv
│   │   ├── AQI_STANDARD.csv
│   │   ├── LOCATION.csv
│   │   ├── WARD.csv
│   │   └── WEATHER_RECORD.csv
│   └── test_output/                        # Dữ liệu chạy thử nghiệm (1 ngày)
│
├── Clean and visual data/                  # Module 2: Làm sạch & Trực quan hóa
│   ├── CLEAN.py                            # Script làm sạch dữ liệu thô
│   ├── TrucQuan.py                         # Script vẽ 4 biểu đồ trực quan hóa
│   ├── WEATHER_RECORD.csv                  # Dữ liệu thời tiết đầu vào
│   ├── AIRQUALITY_RECORD.csv               # Dữ liệu không khí đầu vào
│   ├── WEATHER_CLEAN.csv                   # Dữ liệu thời tiết sau khi làm sạch
│   ├── AIRQUALITY_CLEAN.csv                # Dữ liệu không khí sau khi làm sạch
│   ├── LOCATION.csv                        # Danh mục điểm đo
│   ├── WARD.csv                            # Danh mục phường
│   ├── AQI_STANDARD.csv                    # Bảng quy chuẩn AQI
│   └── output/                             # Thư mục lưu 4 biểu đồ PNG đầu ra
│       ├── Biểu đồ 1 - Line chart.png
│       ├── Biểu đồ 2 - Horizontal bar chart.png
│       ├── Biểu đồ 3 - Histogram.png
│       └── Biểu đồ 4 - Scatter plot.png
│
└── Câu hỏi phân tích/                      # Module 3: Phân tích 7 câu hỏi nghiên cứu
    ├── Analyst.py                          # Script chạy phân tích dữ liệu
    ├── WEATHER_CLEAN.csv                   # Dữ liệu thời tiết đã làm sạch
    ├── AIRQUALITY_CLEAN.csv                # Dữ liệu không khí đã làm sạch
    ├── LOCATION.csv                        # Danh mục điểm đo
    ├── WARD.csv                            # Danh mục phường
    └── output/                             # Thư mục lưu kết quả phân tích
        ├── cau_1.csv
        ├── cau_2.csv
        ├── cau_3.csv
        ├── cau_4.csv
        ├── cau_5.csv
        ├── cau_6.csv
        └── cau_7.csv

```

## 3. Yêu cầu hệ thống & Cài đặt thư viện

### Yêu cầu

* **Python 3.8** trở lên.

* **pip** (trình quản lý gói của Python).

### Bước 1: Tạo và kích hoạt môi trường ảo (Khuyến nghị)

Mở Terminal tại thư mục gốc `Nhom 8 btl Python/` và chạy:

```
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo (Windows)
venv\Scripts\activate

# Kích hoạt môi trường ảo (macOS/Linux)
source venv/bin/activate

```

### Bước 2: Cài đặt thư viện

Chạy lệnh sau ngay tại thư mục gốc `Nhom 8 btl Python/`:

```
pip install -r requirements.txt

```

### Bước 3: Cấu hình biến môi trường (Tùy chọn)

Chương trình thu thập dữ liệu đã có sẵn cấu hình mặc định trong `Collect data/main.py` nên có thể chạy trực tiếp mà không cần cấu hình thêm. Nếu muốn tùy chỉnh khoảng thời gian, múi giờ hoặc thời gian lưu cache, bạn có thể tạo tệp `.env` bên trong thư mục `Collect data/` với các biến sau:

```
DATA_DIR=./DATA_raw
START_DATE=2026-09-01
END_DATE=2026-10-31
TIMEZONE=Asia/Ho_Chi_Minh
CACHE_EXPIRE_SECONDS=3600

```

## 4. Hướng dẫn chạy chương trình

> **Quan trọng:** Vì các tệp Python sử dụng đường dẫn tương đối, bạn cần dùng lệnh `cd` di chuyển vào **đúng thư mục chứa tệp `.py`** (giữ dấu ngoặc kép `""` do tên thư mục có dấu cách) trước khi chạy.

### Bước 1: Thu thập dữ liệu (Bỏ qua nếu dùng sẵn dữ liệu có trong repo)

Từ thư mục gốc `Nhom 8 btl Python/`:

```
cd "Collect data"
python main.py

```

* Chọn chế độ chạy (thử nghiệm 1 ngày hoặc đầy đủ 61 ngày) theo hướng dẫn trên màn hình.

* Dữ liệu sau khi tải sẽ được lưu vào `Collect data/DATA_raw/` (hoặc `Collect data/test_output/`).

### Bước 2: Làm sạch và trực quan hóa dữ liệu

Quay lại thư mục gốc (`cd ..`), sau đó chuyển sang thư mục `Clean and visual data`:

```
cd "Clean and visual data"
python CLEAN.py
python TrucQuan.py

```

* `CLEAN.py` xuất `WEATHER_CLEAN.csv` và `AIRQUALITY_CLEAN.csv` ngay trong thư mục `Clean and visual data/`.

* `TrucQuan.py` xuất 4 biểu đồ PNG vào `Clean and visual data/output/`.

### Bước 3: Chạy phân tích 7 câu hỏi

Quay lại thư mục gốc (`cd ..`), sau đó chuyển sang thư mục `Câu hỏi phân tích`:

```
cd "Câu hỏi phân tích"
python Analyst.py

```

* Kết quả của 7 câu hỏi sẽ được xuất vào `Câu hỏi phân tích/output/` (`cau_1.csv` đến `cau_7.csv`).

  ## 