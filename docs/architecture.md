# Kiến trúc

Hệ thống bám theo báo cáo thiết kế (Plan / class_diagram / functionality / directory_tree), với **một thay đổi có chủ đích**: firmware ESP32 viết bằng **C/C++** (theo yêu cầu),
không phải MicroPython như báo cáo; phần Python chạy trên PC.

```
 ┌────────────────────────── PC (Python) ──────────────────────────┐        ┌──────────────── ESP32 (C++) ────────────────┐
 │ pc_app/ui (Tkinter) → AppController → RobotClient → TcpClient    │  TCP   │ TcpServer → RobotApp → CommandHandler        │
 │   Movement/Action/Gait/Pose/Status/Log panels                    │ ◄────► │   Watchdog · StatusReporter · SensorHub      │
 │                                                                  │ JSON   │ MotionController (StateMachine, Actions)     │
 │ simulation/ : SimRobot (cùng giao thức) + Visualizer 3D          │ dòng   │   Gait · Posture · MotionCoordinator         │
 │ shared/     : lõi chuyển động bản Python (mô phỏng + kiểm chứng) │        │   BodyKinematics · LegKinematics · SafetyGuard│
 └──────────────────────────────────────────────────────────────────┘        │ PCA9685Backend → ServoManager → PCA9685 ×2   │
                                                                              └──────────────────────────────────────────────┘
```

## Mô hình toán và phần dùng chung

`motion_model/` là lớp API toán, hiển thị và xuất CSV trên cùng MotionController của `shared/`. Cả FK và IK Python dùng `shared/common/leg_geometry.py`; `LegKinematics` và API toán gọi cùng hàm. GaitEngine gọi `build_motion_controller`, không giữ một bộ sinh dáng đi độc lập. Tất cả đọc cấu hình 54/45/77 mm trong `config/robot_config.json`; thứ tự chân i,j,k,l,m,n, +X phải/+Y tiến/+Z lên, lệnh chuẩn hóa [-1,1]. Không có cấu hình JSON riêng trong motion_model. Firmware C++ giữ hành vi và nguồn JSON tương ứng, kiểm chứng bằng đối chiếu kịch bản.

## Luồng dữ liệu một chu kỳ điều khiển (50 Hz)

`lệnh MOVE` → `CommandHandler` → `MotionController` → (làm mượt vận tốc) → `Walk/Strafe/Turn` → `BaseGait` (độ dịch từng bàn chân theo quỹ đạo Bézier) +
`PostureGenerator` (tư thế thân) → `MotionCoordinator` (`BodyKinematics` → IK từng chân) → `JointFrame` 18 góc → `SafetyGuard`
(NaN, giới hạn góc, giới hạn tốc độ khớp) → `ActuatorBackend` → `ServoManager` (góc khớp → góc servo → µs → tick) → 2 × `PCA9685` (mỗi board 1 lần ghi 65 byte).

## Bản đồ thư mục

| Thư mục | Nội dung |
|---|---|
| `config/` | **Nguồn cấu hình duy nhất** (JSON): hình học, servo map, calibration, dáng đi, tư thế, an toàn, phần cứng, mạng, PC |
| `motion_model/` | API toán, adapter của MotionController, minh họa và xuất CSV |
| `shared/` | Lõi chuyển động bản Python: `robot_core` (Hexapod, Leg, Joint, FK/IK, SafetyGuard, MotionCoordinator), `gait_core` (Tripod/Wave/Ripple/Rotation), `posture_core`, `motion_core` (StateMachine, actions, MotionController), `common`, `interfaces` |
| `firmware_esp32/` | Firmware C++ (PlatformIO): cùng cấu trúc `robot_core/gait_core/posture_core/motion_core` + `hardware/` (PCA9685, Servo, ServoBoard, ServoManager, MPU6050), `communication/` (WiFi, TCP, Serial), `app/` (CommandHandler, Watchdog, StatusReporter, RobotApp) |
| `firmware_esp32/include/generated_config.h` | **Tự sinh** từ `config/*.json` bởi `tools/gen_firmware_config.py` (PlatformIO gọi trước mỗi lần build) |
| `firmware_esp32/test/host/` | Test C++ chạy trên PC + `scenario.txt` (kịch bản đối chiếu) |
| `pc_app/` | Ứng dụng điều khiển: `communication` (TcpClient, SerialClient), `RobotClient`, `AppController`, `ui/` |
| `simulation/` | `SimBackend`, `SimRobot` (server TCP giả lập nói đúng giao thức), `Visualizer`, `run_sim.py` |
| `tools/` | ping, quét I2C, test servo/chân, hiệu chỉnh, sinh config, đối chiếu chéo |
| `tests/` | Các test Python (lõi, giao thức, PC app ↔ SimRobot qua TCP, công cụ, đồng bộ firmware) |

## Quyết định thiết kế chính

- **Một nguồn cấu hình (DRY):** Python đọc JSON; firmware dùng header sinh từ cùng JSON. Test `test_header_matches_json` báo nếu header cũ.
- **Hai bản cài đặt, một hành vi:** lõi chuyển động có bản Python (mô phỏng, test nhanh) và bản C++ (chạy trên ESP32). `tools/crosscheck_firmware.py` chạy cùng kịch bản
  trên cả hai và so sánh từng bước 20 ms (trạng thái + 18 góc + tick PWM) — đây là lưới an toàn chống lệch hành vi.
- **Ranh giới trừu tượng (DIP/ISP):** `ActuatorBackend`, `Transport`, `I2CBus`, `Clock`, `DigitalOutput`, `AnalogInput`. Lõi không biết Arduino; mọi thứ phụ thuộc phần cứng nằm sau interface → test được trên PC bằng đối tượng giả.
- **Mở rộng không sửa code cũ (OCP):** thêm dáng đi = một lớp con `BaseGait` (+ một mục trong `gait_config.json`); thêm hành động = một lớp con `SpecialAction`; thêm transport = một lớp `Transport`.
- **Firmware phù hợp ESP32:** không exception, không RTTI, không cấp phát heap ở vòng điều khiển (mọi đối tượng cấp phát tĩnh), kết quả lỗi trả bằng `Result`. Một vòng lặp 50 Hz đơn luồng, không khóa.
- **An toàn nhiều lớp:** `SafetyGuard` (kẹp giới hạn + giới hạn tốc độ khớp, vi phạm → ERROR), kiểm tra tầm với IK, watchdog heartbeat (mất kết nối → dừng và ngồi), `EMERGENCY_STOP` nhận ở mọi trạng thái, lỗi I2C → ERROR.
- **Chuyển động mượt:** vận tốc đi được tăng/giảm có dốc (không giật), độ nhấc chân giảm dần theo sải bước, tư thế thân nội suy có giới hạn tốc độ, và vùng tư thế khi bước hẹp hơn khi đứng yên.

## Khác biệt so với báo cáo thiết kế

| Báo cáo | Bản này | Lý do |
|---|---|---|
| Firmware MicroPython dùng chung `shared/` | Firmware C/C++; `shared/` chỉ chạy trên PC | Yêu cầu của đề bài; hành vi được khóa bằng đối chiếu chéo |
| `deploy_to_esp32.py` (đẩy file Python) | `gen_firmware_config.py` + PlatformIO | Firmware biên dịch, không đẩy file |
| `Body` có ước lượng tư thế (BodyPose) | Firmware dùng `AttitudeEstimator` (bộ lọc bù từ MPU6050) báo `imu.roll/pitch` trong STATUS | Tách rõ "tư thế mong muốn" và "tư thế đo được" |
| Gait panel: thanh trượt tốc độ **và bước dài** | Chỉ thanh tốc độ; bước dài đặt trong `gait_config.json` | Bước dài ảnh hưởng tầm với IK/an toàn nên không cho đổi tức thời |
| `SET_POSE` có dịch thân ngang | Chỉ `z, roll, pitch, yaw` | Giao thức trong báo cáo chỉ liệt kê 4 tham số này |
| Action "nhảy" | Chỉ `wave`, `bob`, `dance` | MG90S không đủ lực/tốc độ, nhảy dễ làm hỏng servo/hộp số |
| Cảm biến MPU6500 (trong tài liệu) | MPU6050 (theo hình đề bài) | Cùng giao tiếp I2C, cùng thanh ghi cần dùng |
| `ENABLE + STAND_UP` từ IDLE | `STAND_UP` ở IDLE tự `ENABLE`; `ENABLE` riêng đưa robot về tư thế ngồi | Có thể bật servo mà chưa đứng (phục vụ test servo) |
