# Lắp đặt, nạp firmware và hiệu chỉnh

> ⚠️ Mọi giá trị **MẶC ĐỊNH** dưới đây (chân GPIO, chiều quay servo, vị trí chân trên thân, tỉ lệ chia áp pin) là
> suy ra từ báo cáo hoặc giả định hợp lý — **chưa được thử trên robot thật**. Hãy kiểm tra từng mục trước khi cho robot đứng.

## 1. Đấu nối

| Thiết bị | Nối với | Ghi chú |
|---|---|---|
| PCA9685 #0 (địa chỉ `0x40`) | ESP32 SDA=GPIO21, SCL=GPIO22, VCC=3.3 V | Điều khiển chân **i, j, k** (kênh 0–8) |
| PCA9685 #1 (địa chỉ `0x41`) | cùng bus I2C | Hàn cầu địa chỉ **A0**. Chân **l, m, n** (kênh 0–8) |
| MPU6050 (`0x68`) | cùng bus I2C | AD0 nối GND. Trục X hướng về phía trước robot |
| 18 × MG90S | PCA9685, chân V+ của PCA9685 | **Nguồn servo riêng** 5–6 V, dòng đủ lớn (khuyến nghị ≥ 5 A); **nối chung GND** với ESP32 |
| Pin (đo điện áp) | GPIO34 qua cầu chia áp | Tỉ lệ chia mặc định 3.13 (`hardware_config.json`) - tính lại theo điện trở thật; ADC chỉ chịu tối đa ~3.1 V |
| OE của PCA9685 (tùy chọn) | GPIO bất kỳ, đặt `servo_output_enable_pin` | Mặc định `-1` (không dùng); nếu dùng, OE kéo cao = ngắt cứng mọi servo |

Quy ước thứ tự chân (nhìn từ trên xuống, đầu robot ở phía +Y): `i` giữa-phải, rồi theo chiều kim đồng hồ `j` sau-phải, `k` sau-trái, `l` giữa-trái, `m` trước-trái, `n` trước-phải.
Nhóm tripod: **A = i, k, m**; **B = j, l, n**.

Bảng kênh mặc định (`config/servo_map.json`): chân thứ `n` (0..5) → board `n // 3`, kênh `(n % 3) * 3 + {0: coxa, 1: femur, 2: tibia}`.

## 2. Số đo cơ khí cần điền

`config/robot_config.json`: chiều dài khâu **54 / 45 / 77 mm** lấy từ báo cáo. Còn **vị trí gắn 6 chân trên thân** (`x`, `y`, `yaw_deg`) là giá trị
mặc định — hãy đo lại từ bản vẽ CAD của nhóm Mech. `stance.radius_mm` (110) và `height_mm` (60) là tư thế đứng chuẩn đã kiểm tra với giới hạn khớp.

## 3. Nạp firmware

```bash
# sửa config/network_config.json: ssid / password WiFi (nếu không vào được WiFi, ESP32 tự phát AP "Hexapod-AP", IP 192.168.4.1)
cd firmware_esp32
pio run -t upload          # PlatformIO tự sinh include/generated_config.h từ config/*.json
pio device monitor         # thấy IP, cổng TCP, số thiết bị I2C
```
Nếu không dùng PlatformIO: chạy `python -m tools.gen_firmware_config`, rồi biên dịch `src/` bằng Arduino IDE (core ESP32) với `-std=gnu++17` (hoặc ≥ gnu++11) và thư mục `include/` trong đường dẫn include.
Muốn điều khiển qua cáp USB thay cho WiFi: thêm `-DHEXAPOD_SERIAL_TRANSPORT` vào `build_flags` (khi đó log bị tắt vì Serial dùng để truyền giao thức).

## 4. Kiểm tra theo thứ tự (nhấc robot lên giá đỡ, chân không chạm đất)

```bash
python -m tools.ping_robot   --host <IP>      # thông mạng, RTT
python -m tools.scan_i2c     --host <IP>      # phải thấy 0x40, 0x41 (và 0x68 nếu có MPU6050)
python -m tools.test_all_servos --host <IP>   # từng servo nhúc nhích nhẹ: servo nào không động -> sai kênh/dây
```

## 5. Hiệu chỉnh servo (bắt buộc trước khi đứng)

`servo_deg = offset_deg + direction × joint_deg`. Với mỗi khớp, **góc khớp 0°** được định nghĩa:

| Khớp | Tư thế 0° | Chiều dương |
|---|---|---|
| coxa | chân hướng thẳng ra ngoài, vuông góc với cạnh thân tại vị trí gắn | quay ngược chiều kim đồng hồ nhìn từ trên |
| femur | đốt femur nằm ngang | nâng đầu gối lên |
| tibia | duỗi thẳng hàng với femur | tibia gập (khi đứng: tibia ≈ −100°, femur ≈ +20°, coxa 0°) |

```bash
python -m tools.calibrate_servo --host <IP>   # hướng dẫn tương tác: nhập góc thô, s = lưu offset, d = đảo chiều
python -m tools.gen_firmware_config           # sinh lại header, rồi nạp lại firmware
```
Sau đó thử `python -m tools.test_single_leg --leg 0` và xem chân có cử động đúng chiều (nâng femur lên, tibia gập vào…).
Nếu một khớp quay ngược chiều mong muốn, đảo `direction` (phím `d` trong công cụ).

## 6. Chạy lần đầu

1. Để robot ngồi trên mặt phẳng, `python -m pc_app.main --host <IP>` → **Enable** → **Đứng lên**.
2. Thử `MOVE` tốc độ thấp (thanh tốc độ ~0.3), dáng `wave` (ổn định nhất), rồi tăng dần.
3. Nếu robot báo `LIMIT`: một chân cần góc ngoài giới hạn → xem log (tên chân/khớp) và kiểm tra lại calibration & kích thước.
4. **Esc** (hoặc nút DỪNG KHẨN CẤP) luôn ngắt servo ngay.

## 7. Điều chỉnh dáng đi

Các thông số trong `config/gait_config.json` (`step_length_mm`, `step_height_mm`, `cycle_time_s` từng dáng…) được chọn để **tốc độ khớp tối đa ≈ 280–300 °/s**,
dưới ngưỡng bảo vệ 360 °/s (`safety_config.json`). Tăng tốc đi nhanh hơn sẽ bị `SafetyGuard` bóp tốc độ khớp (quỹ đạo méo) — nên kiểm tra bằng
mô phỏng (`python -m simulation.run_sim`) và `tests/` trước khi thay đổi. Sửa JSON → `python -m tools.gen_firmware_config` → nạp lại.
