# HỆ THỐNG AI AGENT PHÂN TÍCH & ĐIỀU HÀNH DOANH NGHIỆP SAO VIỆT

Hệ thống AI Agent hoàn chỉnh vận hành cục bộ tại `http://localhost:5000` phục vụ quản trị và điều hành doanh nghiệp hằng ngày.

---

## 1. CÁC TÍNH NĂNG VÀ NGUYÊN TẮC CỐT LÕI

- **Vận hành thật, không phải bản demo**: Chạy `python server.py` là ứng dụng hoạt động ngay lập tức tại `http://localhost:5000`.
- **Tuyệt đối không dùng tên công ty thật**: Toàn bộ dữ liệu mẫu, bối cảnh và mã nguồn sử dụng pháp nhân hư cấu (*Tập đoàn Sản xuất Thiết bị Gia dụng Sao Việt*, *Đại lý An Khang*, *Đại lý Thành Đạt*...).
- **Không bịa số liệu (Không hallucinate)**: Mọi con số trong bằng chứng 5 Whys và báo cáo được tính toán trực tiếp bằng code Python (`numpy`, `pandas`, `openpyxl`). Khi thiếu dữ liệu thì nêu rõ thiếu; suy luận ghi rõ là suy luận kèm căn cứ.
- **Toàn bộ giao diện và kết quả bằng tiếng Việt**: Thiết kế SaaS Dashboard chuyên nghiệp với Tailwind CSS + Lucide Icons.
- **Xử lý phản hồi đa vòng (B5)**: Có phiên bản v1, v2, v3..., báo cáo "Điều đã thay đổi" (Diff), so sánh và khôi phục (rollback), không chiều lòng mù quáng (đối chiếu số liệu thực tế trước khi override).

---

## 2. KIẾN TRÚC VÀ MODULE LĨNH VỰC (DOMAIN MODULES)

1. **Module `generic_analysis` (Mặc định)**:
   - Áp dụng cho mọi dữ liệu kinh doanh: Doanh thu, hàng tồn kho, công nợ, khách hàng, vận hành.
   - Lập hồ sơ dữ liệu (Profiling): Đếm dòng/cột, tỷ lệ thiếu, trùng lặp, phát hiện ngoại lai (IQR) và định dạng bất thường.
   - Làm sạch & Chuẩn hóa: Dấu tiếng Việt Unicode NFC, tiền tệ VNĐ/triệu/tỷ, ghi vết kiểm toán (Audit Change Log) từng dòng, cột.
   - Phân tích 5 Whys và đề xuất tối thiểu 3 giải pháp ưu tiên có KPI, đơn vị chịu trách nhiệm, chi phí và rủi ro tồn đọng.

2. **Module `distribution_partner` (Chuyên sâu ngành gia dụng)**:
   - Quy trình 6 bước lựa chọn & phát triển đối tác phân phối:
     - **Bước 1 - Tiếp nhận hồ sơ**: Biểu mẫu 5 nhóm trường hoặc bóc tách tự động tài liệu (.pdf, .docx, .txt).
     - **Bước 2 - Đối chiếu & Tuân thủ tự động**: Quét trùng MST/SĐT/Người đại diện nợ xấu, tính khoảng cách Geofencing Haversine (bán kính 3.5 km), soát trần công nợ tín chấp (500 triệu VNĐ) và thời hạn nợ (30-45 ngày).
     - **Bước 3 - Phối hợp & Xác minh liên phòng ban**: Tự sinh 3 phiếu khảo sát (Kinh doanh: footfall; Kỹ thuật: 2 thợ cơ hữu, xưởng >= 15m2, SLA 48h; Tài chính: CIC, bảo lãnh ngân hàng).
     - **Bước 4 - Chấm điểm 100đ & Phân hạng Tier**: Phạt **Bẫy Cam Kết Ảo** (doanh số >= 1.5 tỷ/tháng nhưng 0 thợ hoặc điểm bảo hành < 12/25 -> **trừ 25 điểm** và gắn CẢNH BÁO ĐỎ). Phân hạng Tier A (>= 80đ), Tier B (65-79đ), Tier C (50-64đ), Tier D (< 50đ).
     - **Bước 5 - Cockpit Phê duyệt Chiến lược**: Báo cáo phân tích động cơ ngầm, 3 kịch bản đàm phán, phương án giảm thiểu rủi ro và các nút quyết định của lãnh đạo: `[TIẾP TỤC]` / `[BỔ SUNG ĐIỀU KIỆN]` / `[CHƯA TIẾP TỤC]`.
     - **Bước 6 - Bàn giao & Xuất file**: Thư/Email ngoại giao gửi đối tác chuyên nghiệp (không lộ điểm nội bộ), bảng điều kiện tiên quyết (Conditions Precedent) và xuất Excel/Word/JSON.

---

## 3. MÁY TRẠNG THÁI (STATE MACHINE) & KHẢ NĂNG BỀN VỮNG

```
NHAP_LIEU ──> DANG_XU_LY ──┬─> LOI (B3a: file hỏng, thiếu cột, sai định dạng)
                           │
                           └─> CHO_DANH_GIA (B4)
                                    │   ▲
       [Phản hồi B5]                │   │ [Tạo phiên bản mới v2, v3...]
                                    ▼   │
                               DANG_XU_LY_LAI
                                    │
                               [Chấp nhận]
                                    ▼
                               DA_CHAP_NHAN
                                    │
                               [Xuất file B6]
                                    ▼
                                 DA_XUAT ──> HOAN_TAT (End)
```

- Mọi chuyển đổi trạng thái được ghi vào sổ cái kiểm toán (`audit_trail`).
- Cơ sở dữ liệu JSON (`pipeline_database.json`) áp dụng cơ chế ghi nguyên tử (**Atomic Write** - ghi file tạm rồi đổi tên), đảm bảo không bao giờ bị hỏng khi khởi động lại máy chủ.

---

## 4. HƯỚNG DẪN CÀI ĐẶT & KHỞI CHẠY

### Bước 1: Cài đặt thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### Bước 2: (Tùy chọn) Cấu hình Google Gemini API Key
Hệ thống tự động đọc API Key từ biến môi trường `GEMINI_API_KEY`:
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="AIzaSy..."

# Windows CMD
set GEMINI_API_KEY=AIzaSy...
```
*Lưu ý: Nếu không có API Key, hệ thống tự động kích hoạt bộ máy phân tích quy tắc chuyên gia (Rule-based Fallback) với đầy đủ chức năng, không bị gián đoạn hoạt động.*

### Bước 3: Khởi chạy ứng dụng
```bash
python server.py
```
Mở trình duyệt truy cập: **`http://localhost:5000`**

### Bước 4: Chạy kiểm thử tự động (Unit & Integration Tests)
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 5. DANH SÁCH TỆP DỮ LIỆU MẪU CÓ SẴN TRONG HỆ THỐNG

| Tên tệp | Mô tả kịch bản | Kết quả dự kiến |
|---|---|---|
| `ho_so_tot_an_khang.json` | Đại lý An Khang tại Long Biên, cơ sở vật chất tốt | Xếp hạng **Tier A** (>= 80đ), hợp tác ngay |
| `ho_so_no_xau_thanh_dat.json` | Trùng mã số thuế & số điện thoại đại lý cũ nợ xấu | **CẢNH BÁO ĐỎ**, Xếp hạng **Tier D** |
| `ho_so_vi_pham_dia_ban_phu_thinh.json` | Điểm bán tại Cầu Giấy cách đại lý hiện hữu 0.6 km | **CẢNH BÁO ĐỎ Geofencing** (< 3.5 km) |
| `ho_so_cam_ket_ao_viet_hung.json` | Cam kết 2.2 tỷ/tháng nhưng 0 thợ kỹ thuật | Kích hoạt **Bẫy Cam Kết Ảo, phạt -25đ**, Tier D |
| `doanh_thu_ban_hang_2024.csv` | Bảng kê doanh thu, chiết khấu và đổi trả hàng | Làm sạch dữ liệu, 5 Whys và 3 giải pháp |
| `bao_cao_cong_no_q3.xlsx` | Báo cáo công nợ khách hàng và ngày quá hạn | Phát hiện nợ quá hạn nhóm 3-5, đề xuất trần nợ |
| `file_loi_thieu_cot.csv` | Tệp CSV thiếu cột định danh bắt buộc | Báo lỗi **B3a** chỉ rõ vị trí và cách sửa |
| `file_loi_sai_dinh_dang.xlsx` | Tệp Excel có chữ báo lỗi trong cột số | Báo lỗi **B3a** định vị dòng, sheet bị lỗi |
