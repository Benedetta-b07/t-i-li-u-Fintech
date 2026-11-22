# Bài Tập Lớn Python - Nhóm 8: Thu thập, Xử lý và Phân tích Dữ liệu Thời tiết & Chất lượng Không khí

Dự án thực hiện quy trình hoàn chỉnh từ thu thập dữ liệu thời tiết và chất lượng không khí (AQI), làm sạch dữ liệu, trực quan hóa bằng biểu đồ cho đến phân tích chuyên sâu theo các câu hỏi đặt ra.

---

## 1. Mô tả chức năng chính

Dự án được chia thành 4 giai đoạn xử lý chính:

1. **Thu thập dữ liệu (`Data collect/Source_code_collector`)**:
   - Thu thập dữ liệu thời tiết (`WEATHER_RECORD.csv`), chất lượng không khí (`AIRQUALITY_RECORD.csv`), thông tin địa điểm (`LOCATION.csv`, `WARD.csv`) và tiêu chuẩn AQI (`AQI_STANDARD.csv`).
   - Hỗ trợ lưu bộ nhớ đệm (`.cache.sqlite`) giúp giảm số lần gọi API trùng lặp và cấu hình thông qua tệp `.env` cùng `settings.json`.
2. **Làm sạch dữ liệu (`CLEAN.py`)**:
   - Đọc dữ liệu thô từ thư mục `DATA_raw/`, xử lý các giá trị thiếu, trùng lặp hoặc sai định dạng.
   - Xuất các bộ dữ liệu đã được chuẩn hóa sang thư mục `Data_clean/`.
3. **Trực quan hóa dữ liệu (`TrucQuan.py`)**:
   - Tạo 4 loại biểu đồ trực quan từ dữ liệu đã làm sạch và lưu vào thư mục `Output_chart/`:
     - **Biểu đồ 1**: Line chart (Biểu đồ đường)
     - **Biểu đồ 2**: Horizontal bar chart (Biểu đồ cột ngang)
     - **Biểu đồ 3**: Histogram (Biểu đồ phân phối)
     - **Biểu đồ 4**: Scatter plot (Biểu đồ phân tán)
4. **Phân tích dữ liệu (`Analyst.py`)**:
   - Thực hiện phân tích dữ liệu để trả lời 7 câu hỏi nghiên cứu và xuất kết quả chi tiết ra các tệp từ `cau_1.csv` đến `cau_7.csv` trong thư mục `Output_question/`.

---

## 2. Cấu trúc thư mục

```text
Nhom_8_btl_python/
├── Cleaning data/
│   ├── Output_chart/                       # Chứa 4 biểu đồ PNG sau khi trực quan hóa
│   │   ├── Biểu đồ 1 - Line chart.png
│   │   ├── Biểu đồ 2 - Horizontal bar chart.png
│   │   ├── Biểu đồ 3 - Histogram.png
│   │   └── Biểu đồ 4 - Scatter plot.png
│   └── Source_code_clean/
│       ├── CLEAN.py                        # Script làm sạch dữ liệu
│       ├── TrucQuan.py                     # Script vẽ biểu đồ trực quan hóa
│       ├── requirements.txt                # Thư viện cần thiết cho làm sạch & trực quan hóa
│       ├── Data_clean/                     # Dữ liệu CSV sau khi làm sạch
│       ├── output/                         # Thư mục lưu kết quả đầu ra phụ
│       └── Data collect/
│           └── Source_code_collector/
│               ├── main.py                 # Điểm khởi chạy quá trình thu thập dữ liệu
│               ├── collector.py            # Module xử lý logic thu thập dữ liệu
│               ├── requirements.txt        # Thư viện cần thiết cho thu thập dữ liệu
│               ├── .env.example            # Mẫu file cấu hình biến môi trường (API key...)
│               ├── Document JSON/
│               │   └── settings.json       # Cấu hình tham số thu thập
│               ├── DATA_raw/               # Dữ liệu CSV thô thu thập được
│               ├── test_output/            # Dữ liệu kiểm thử
│               └── Cache API/              # Bộ nhớ đệm API (.cache.sqlite)
│
└── Câu hỏi phân tích/
    ├── Analyst.py                          # Script trả lời 7 câu hỏi phân tích
    └── Output_question/                    # Kết quả phân tích (cau_1.csv -> cau_7.csv)
```

---

## 3. Yêu cầu hệ thống & Cài đặt thư viện

### Yêu cầu
- **Python 3.8** trở lên.
- **pip** (trình quản lý gói của Python).

### Bước 1: Tạo môi trường ảo (Khuyến nghị)
Mở Terminal tại thư mục gốc `Nhom_8_btl_python/` và chạy:

```bash
# Tạo môi trường ảo
python -m venv venv

# Kích hoạt môi trường ảo (Windows)
venv\Scripts\activate

# Kích hoạt môi trường ảo (macOS/Linux)
source venv/bin/activate
```

### Bước 2: Cài đặt các thư viện cần thiết
Dự án có 2 tệp `requirements.txt` cho phần thu thập và phần xử lý dữ liệu. Chạy lần lượt 2 lệnh sau từ thư mục gốc `Nhom_8_btl_python/`:

```bash
pip install -r "Cleaning data/Source_code_clean/Data collect/Source_code_collector/requirements.txt"
pip install -r "Cleaning data/Source_code_clean/requirements.txt"
```

### Bước 3: Cấu hình biến môi trường (nếu chạy lại phần thu thập dữ liệu)
1. Truy cập thư mục `Cleaning data/Source_code_clean/Data collect/Source_code_collector/`.
2. Sao chép tệp `.env.example` thành `.env`.
3. Điền các thông tin cấu hình / API key cần thiết vào tệp `.env`.

---

## 4. Hướng dẫn chạy chương trình

Bạn có thể chạy toàn bộ quy trình theo thứ tự từ Bước 1 đến Bước 4 (hoặc bỏ qua Bước 1 nếu muốn dùng sẵn dữ liệu trong `DATA_raw/`):

### Bước 1: Thu thập dữ liệu
```bash
cd "Cleaning data/Source_code_clean/Data collect/Source_code_collector"
python main.py
```
> Kết quả sẽ được lưu vào thư mục `DATA_raw/`.

### Bước 2: Làm sạch dữ liệu
Mở Terminal tại thư mục `Cleaning data/Source_code_clean/`:
```bash
cd "Cleaning data/Source_code_clean"
python CLEAN.py
```
> Kết quả các tệp `*_CLEAN.csv` sẽ được lưu vào thư mục `Data_clean/`.

### Bước 3: Trực quan hóa dữ liệu
Tại thư mục `Cleaning data/Source_code_clean/`:
```bash
python TrucQuan.py
```
> 4 biểu đồ sẽ được xuất ra dưới dạng tệp `.png` trong thư mục `Cleaning data/Output_chart/`.

### Bước 4: Chạy phân tích câu hỏi
Chuyển sang thư mục `Câu hỏi phân tích/` và chạy:
```bash
cd "Câu hỏi phân tích"
python Analyst.py
```
> Kết quả của 7 câu hỏi sẽ được xuất vào thư mục `Output_question/` (`cau_1.csv` đến `cau_7.csv`).

---
