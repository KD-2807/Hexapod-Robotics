# Kiểm chứng và giới hạn

Ngày kiểm tra: 29/10/2026. Cấu hình: `config/robot_config.json`, 54/45/77 mm. Kiểm tra thực hiện trên PC; không sử dụng robot thật.

## Kết quả

| Hạng mục | Kết quả |
|---|---|
| Toàn bộ Python và đối chiếu C++ | 93 test đạt, không bỏ qua test |
| Mô hình toán và tích hợp | 16 test: hình học, dùng chung cấu hình, đổi hệ, lệnh chuẩn hóa, thời gian, CSV và vùng chống giả định |
| Adapter với controller độc lập | 6 lệnh x 3 dáng x 600 bước, dt=0.02 s; 18 góc bằng nhau ở từng bước |
| CSV với controller | Giá trị cột góc bằng đúng JointFrame, giữ thứ tự i,j,k,l,m,n |
| Backend mô phỏng | Góc hiển thị lấy từ khung đã áp dụng sau SafetyGuard |
| Cấu hình thay thế | Thay cùng thư mục config làm cả mô hình lẫn controller đổi theo |
| C++ trên PC | Unit test và kịch bản Python/C++ đạt; góc trong sai số 0.05 độ, PWM trong 1 tick |
| Header firmware | Khớp JSON, đã sinh lại sau cập nhật lịch ripple |
| Mô phỏng headless | Kịch bản tiến 4 giây hoàn thành ở trạng thái WALKING |
| Hình minh họa | PNG/GIF được tạo lại từ khung góc của lõi chung |

Chạy lại tại thư mục hexapod:

```bash
python -m unittest discover -s tests -t . -v
python -m simulation.run_sim --headless --seconds 4
python -m tools.gen_firmware_config --check
```

## Cấu hình và lịch pha

Không còn cấu hình riêng trong motion_model. Tất cả Python đọc `config/`; C++ dùng header sinh từ các JSON đó. Lõi dáng đi, máy trạng thái, giới hạn, giao tiếp, ánh xạ chân và đơn vị theo bộ điều khiển.

Lịch ripple cũ dùng các chân đơn nối tiếp và có trường hợp COM giả định nằm ngoài đa giác theo lịch chống. Bản này dùng ba cặp đối diện {j,m}, {i,l}, {n,k}; cập nhật đồng thời Python/firmware qua nguồn JSON. Không đổi chiều dài 54/45/77 mm, vị trí gắn chân, hiệu chỉnh servo hay giao thức.

Biên chống nhỏ nhất trong 601 mẫu/12 giây cho từng trường hợp, speed=0.6:

| Lệnh | Tripod / Wave / Ripple |
|---|---|
| forward | 53.08 / 79.99 / 65.30 mm |
| backward | 53.08 / 62.97 / 65.30 mm |
| right | 65.55 / 69.95 / 71.07 mm |
| left | 65.77 / 69.91 / 71.07 mm |
| rotate | 79.59 / 79.59 / 79.59 mm |
| arc | 55.60 / 79.41 / 70.34 mm |

Các cờ chống là lịch pha, không đo lực hoặc tiếp xúc. Tại đầu phiên, robot đã đứng và có thể có sáu chân ở lịch chống trong khi lệnh đang tăng dần. Xoay thuần sử dụng RotationGait, lịch tripod, nhất quán với firmware. duty wave/ripple là xấp xỉ thập phân nên có khoảng giao pha ngắn.

CSV và validation.json ở motion_model/examples. Bộ dữ liệu mẫu không còn đại diện cho hình học trước khi hợp nhất. Không so sánh CSV mới với CSV cũ theo từng byte vì hình học, quy ước, quỹ đạo và lược đồ CSV đã thống nhất lại.

## Giới hạn

1. Chưa build với toolchain PlatformIO/Arduino-ESP32 thật hoặc nạp lên ESP32; đối chiếu C++ chạy trên PC với phần cứng giả.
2. Giao diện điều khiển có test với đối tượng giả; bố cục Tkinter/2D chưa mở trên màn hình thật trong môi trường kiểm tra này. Hình minh họa matplotlib đã được xem kiểm tra.
3. Vị trí chân, chiều quay, offset và xung servo chưa được đo/hiệu chỉnh với CAD và robot thực tế.
4. Chưa mô phỏng lực, tải, ma sát, trượt, độ rơ, tự va chạm hoặc ổn định động. Biên dương tại các mẫu chỉ là kiểm tra hình học với COM giả định ở tâm thân.
5. ground_local_mm là hệ nền tham chiếu cục bộ, không phải odometry toàn cục. Quỹ đạo Bézier nối liên tục vị trí; chưa bảo đảm liên tục vận tốc/jerk tại chuyển pha. Khung sau giới hạn tốc độ có thể khác mục tiêu IK tức thời.
6. Góc JointFrame/CSV là góc toán học theo độ; không phải xung PWM đã hiệu chỉnh cho robot cụ thể.
