# Giao thức PC ↔ ESP32

Kênh: **TCP** (mặc định cổng `8888`, ESP32 là server) hoặc **USB-Serial** 115200. Mỗi gói là **một dòng JSON** kết thúc `\n`.
Lệnh PC→robot tối đa 256 byte; phản hồi/STATUS robot→PC tối đa ~768 byte.

```
PC -> robot : {"seq":12,"cmd":"MOVE","params":{"vx":0,"vy":1,"wz":0,"speed":0.8}}
robot -> PC : {"seq":12,"type":"ACK","data":{}}
              {"seq":12,"type":"ERROR","data":{"code":"BAD_STATE","message":"..."}}
              {"seq":0,"type":"STATUS","data":{...}}        <- robot tự đẩy ~5 Hz (seq = 0)
```
`seq` do PC tăng dần; robot trả lại đúng `seq` của lệnh. Gói nào hợp lệ cũng làm **reset watchdog**; PC gửi thêm `HEARTBEAT` mỗi 0.3 s.
Quá 1.5 s không nhận được gì, hoặc TCP bị ngắt → robot **dừng đi và tự ngồi xuống**.

## Lệnh

| Lệnh | `params` | Trạng thái chấp nhận | Tác dụng |
|---|---|---|---|
| `ENABLE` | – | IDLE | Bật servo ở tư thế ngồi → SITTING |
| `DISABLE` | – | SITTING (đã ngồi xong) | Tắt servo → IDLE |
| `STAND_UP` | – | IDLE (tự ENABLE), SITTING | Đứng lên → STANDING |
| `SIT_DOWN` | – | STANDING, WALKING (dừng rồi mới ngồi) | Ngồi xuống → SITTING |
| `MOVE` | `vx, vy, wz` ∈ [-1,1], `speed` ∈ [0.1,1] (tùy chọn) | STANDING, WALKING | Đi liên tục. `vy` tiến, `vx` sang phải, `wz` xoay ngược chiều kim đồng hồ. Gửi lặp ~10 Hz |
| `STOP` | – | mọi trạng thái | Dừng đi (vận tốc giảm dần về 0), hủy action đặc biệt |
| `SET_GAIT` | `gait`: `tripod` \| `wave` \| `ripple` | trừ ERROR | Đổi dáng đi (áp dụng khi robot đứng yên) |
| `SET_SPEED` | `speed` ∈ [0.1,1] | trừ ERROR | Tần số bước |
| `SET_POSE` | `z` mm ∈ [-25,30], `roll,pitch` ° ∈ ±15, `yaw` ° ∈ ±20 | STANDING, WALKING | Nâng/nghiêng/xoay thân. Tổ hợp không với tới → `LIMIT`. Khi **đang bước**, tư thế bị kẹp vào vùng hẹp hơn (xem dưới) |
| `ACTION` | `name`: `wave` \| `bob` \| `dance` | STANDING (đứng yên) | Hành động đặc biệt; `STOP` để hủy |
| `EMERGENCY_STOP` | – | **mọi trạng thái** | Ngắt xung servo ngay → ERROR |
| `RESET` | – | ERROR, IDLE | Thoát lỗi → IDLE |
| `HEARTBEAT` | – | mọi trạng thái | Giữ kết nối |
| `GET_STATUS` | – | mọi trạng thái | Trả gói `STATUS` với đúng `seq` của lệnh |
| `SET_SERVO` | `leg` 0..5, `joint` 0..2, `angle`, `raw` (tùy chọn) | SITTING | **Chế độ test/hiệu chỉnh**: đặt 1 servo. `raw:true` = góc servo thô 0..180 (bỏ qua calibration) |

Thứ tự chân: `0=i` giữa-phải, `1=j` sau-phải, `2=k` sau-trái, `3=l` giữa-trái, `4=m` trước-trái, `5=n` trước-phải. Khớp: `0=coxa, 1=femur, 2=tibia`.

**Vùng tư thế khi đang bước** (`config/pose_config.json`): z ∈ [-2, 10] mm, roll/pitch ±2°, yaw ±5°. Giá trị đã kiểm chứng bằng mô phỏng ngẫu nhiên không phát sinh lỗi IK; muốn nghiêng nhiều hơn hãy dừng lại.

## Mã lỗi

`BAD_FORMAT` (JSON hỏng/thiếu `seq`) · `BAD_COMMAND` (lệnh lạ) · `BAD_PARAMS` (thiếu/sai/vượt giới hạn) · `BAD_STATE` (không hợp lệ ở trạng thái hiện tại) ·
`LIMIT` (góc khớp vượt giới hạn / chân không với tới) · `HARDWARE` (lỗi I2C/PCA9685) · `ESTOP` (dừng khẩn cấp).
`LIMIT`, `HARDWARE`, `ESTOP` xảy ra trong lúc chạy đều đưa robot vào **ERROR** (servo bị ngắt) cho tới khi nhận `RESET`.

## Máy trạng thái

```
IDLE --ENABLE--> SITTING --STAND_UP--> STANDING <--MOVE/STOP--> WALKING
  ^                |  ^                    |
  +---DISABLE------+  +-----SIT_DOWN-------+      (bất kỳ) --lỗi/EMERGENCY_STOP--> ERROR --RESET--> IDLE
```
`STAND_UP` ở IDLE tự thực hiện `ENABLE` trước (tương ứng "IDLE → STANDING: ENABLE + STAND_UP" trong báo cáo).
Đổi giữa đi tịnh tiến và xoay tại chỗ: robot giảm tốc về 0 rồi mới đổi kiểu bước (tránh giật chân).

## Gói STATUS

```json
{"seq":0,"type":"STATUS","data":{
  "state":"WALKING","gait":"tripod","speed":0.60,
  "pose":{"z":0.0,"roll":0.0,"pitch":0.0,"yaw":0.0},
  "angles":[... 18 góc khớp (độ), thứ tự leg*3+joint ...],
  "error":null,                       // hoặc {"code":"LIMIT","message":"..."}
  "i2c":[64,65,104],                  // thiết bị I2C thấy lúc khởi động (0x40, 0x41, 0x68)
  "battery_v":7.84,                   // chỉ có trên robot thật
  "imu":{"roll":1.5,"pitch":-2.5},    // chỉ có trên robot thật; trục X cảm biến hướng về phía trước
  "connected":true}}
```
