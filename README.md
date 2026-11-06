# Hexapod - Mô hình toán và phần mềm điều khiển
HCMUT Projects

Phần mềm robot sáu chân, mỗi chân ba khớp, gồm mô hình toán, thuật toán chuyển động, ứng dụng PC và firmware ESP32. Cấu hình thống nhất: **coxa 54 mm, femur 45 mm, tibia 77 mm**.

Python đảm nhiệm tính toán, mô phỏng, giao diện và công cụ kiểm tra; firmware C/C++ chạy trên ESP32-WROOM, điều khiển 18 servo MG90S qua hai PCA9685 và đọc MPU6050. Phần Python dùng chung lõi `shared/` và cấu hình JSON tại `config/`.

## Chức năng

- Động học thuận/nghịch một chân ba khớp; đổi hệ tọa độ chân/thân và động học toàn thân.
- Dáng đi tripod, wave, ripple; tiến/lùi, đi ngang, xoay tại chỗ và đi vòng cung.
- Đứng/ngồi, điều chỉnh tư thế thân, máy trạng thái và các hành động wave/bob/dance.
- Giới hạn góc và tốc độ khớp, kiểm tra tầm với, heartbeat, dừng khẩn cấp và xử lý lỗi.
- Giao diện PC dùng Tkinter, kết nối TCP/USB Serial; robot giả lập và mô phỏng 2D/3D.
- Xuất 18 góc khớp theo thời gian ra CSV; công cụ hiệu chỉnh servo và đối chiếu Python/C++.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `config/` | Hình học, dáng đi, tư thế, giới hạn, servo, phần cứng và kết nối |
| `shared/` | Lõi Python: FK/IK, biến đổi tọa độ, gait, posture, MotionController và giao thức |
| `motion_model/` | API toán, minh họa 2D, xuất CSV, công thức và dữ liệu mẫu |
| `pc_app/` | Ứng dụng điều khiển PC |
| `simulation/` | Backend giả lập, server TCP và mô phỏng 3D |
| `firmware_esp32/` | Firmware C/C++ cho ESP32, cấu hình PlatformIO và test C++ trên PC |
| `tools/` | Công cụ kiểm tra, hiệu chỉnh và sinh cấu hình firmware |
| `tests/` | Kiểm tra Python và đối chiếu với firmware |
| `docs/` | Kiến trúc, giao thức, phần cứng và kết quả kiểm chứng |

```text
hexapod/
├── config/                     # Tệp cấu hình robot, dáng đi, phần cứng và servo (JSON)
├── docs/                       # Tài liệu (Kiến trúc, Giao thức, Thiết lập phần cứng)
├── firmware_esp32/             # Firmware ESP32 (Project PlatformIO)
│   ├── include/                # Tệp tiêu đề và cấu hình tự động tạo
│   ├── src/                    # Mã nguồn firmware (Core, App, Giao tiếp, Phần cứng)
│   ├── test/                   # Kiểm tra đơn vị firmware
│   └── tools/                  # Công cụ build dành riêng cho firmware
├── motion_model/               # Mô hình toán học và mô phỏng chuyển động
├── pc_app/                     # Ứng dụng điều khiển trên PC (Python/PyQt)
│   ├── communication/          # Client kết nối Serial và TCP
│   ├── models/                 # Mô hình dữ liệu trạng thái robot
│   └── ui/                     # Các bảng điều khiển và widget giao diện người dùng
├── shared/                     # Logic dùng chung giữa App PC và Mô phỏng
│   ├── common/                 # Hằng số, Enum, Giao thức và Tiện ích toán học
│   ├── gait_core/              # Triển khai dáng đi (Tripod, Wave, Ripple, v.v.)
│   ├── interfaces/             # Backend trừu tượng cho actuator và truyền tải
│   ├── motion_core/            # Điều khiển chuyển động và máy trạng thái
│   ├── posture_core/           # Tạo tư thế và định hướng thân
│   └── robot_core/             # Động học, Thân, Chân và logic An toàn
├── simulation/                 # Trình giả lập và trực quan hóa robot
│   └── server/                 # Server giả lập xử lý lệnh từ xa
├── tests/                      # Kiểm tra tích hợp và đơn vị cho logic dùng chung/app
└── tools/                      # Các kịch bản tiện ích (Hiệu chỉnh, quét I2C, v.v.)
```

Công thức FK/IK Python nằm tại `shared/common/leg_geometry.py`. Mô hình toán, trình xuất CSV và các giao diện mô phỏng dùng cùng MotionController. Firmware sử dụng header sinh từ cùng nguồn cấu hình JSON.

## Môi trường

- Python 3.10 trở lên; Tkinter/Tcl-Tk cho các giao diện.
- Matplotlib cho mô phỏng 3D; pyserial cho USB Serial.
- Matplotlib và Pillow cho công cụ tạo PNG/GIF.
- g++ và make cho các phép kiểm tra C++ trên PC; PlatformIO cho firmware ESP32.

```bash
python -m pip install -r requirements.txt
```

Công cụ tạo hình sử dụng `motion_model/requirements_preview.txt`. Lõi tính toán, xuất CSV và giao tiếp TCP giả lập dùng thư viện chuẩn Python.

## Thực thi

Các lệnh được thực hiện tại thư mục gốc `hexapod/`.

```bash
# Minh họa mô hình toán
python -m motion_model.simulator

# Ứng dụng PC với robot giả lập
python -m pc_app.main --sim

# Mô phỏng 3D
python -m simulation.run_sim

# Xuất góc khớp
python -m motion_model.export_motion --gait tripod --vy 1 --speed 0.6 --seconds 8

# Kiểm tra
python -m unittest discover -s tests -t . -v
```

Mô phỏng 3D sử dụng U/J để đứng/ngồi, WASD để di chuyển, Q/E để xoay, G đổi dáng, Esc dừng khẩn và R reset. Chế độ không mở giao diện:

```bash
python -m simulation.run_sim --headless --seconds 4
```

CSV mặc định tại `motion_model/output/motion.csv`; ảnh, GIF và dữ liệu kiểm chứng tại `motion_model/examples/`. Tái tạo hình minh họa:

```bash
python -m pip install -r motion_model/requirements_preview.txt
python -m motion_model.make_preview
```

## Cấu hình và quy ước

| Đại lượng | Quy ước |
|---|---|
| Chiều dài khâu | 54/45/77 mm; `config/robot_config.json` |
| Hệ tọa độ thân | +X sang phải, +Y phía trước, +Z lên trên |
| Thứ tự chân | i, j, k, l, m, n |
| Vị trí chân tương ứng | Phải giữa, phải sau, trái sau, trái giữa, trái trước, phải trước |
| Thứ tự khớp | Coxa, femur, tibia |
| Góc | FK/IK dùng radian; JointFrame, CSV và giao thức dùng độ |
| Lệnh chuyển động | vx/vy/wz chuẩn hóa trong [-1,1]; speed trong [0.1,1.0] |
| Chu kỳ cập nhật | 0.02 giây |

Tripod dùng nhóm {i,k,m}/{j,l,n}. Ripple dùng ba cặp đối diện {j,m}/{i,l}/{n,k}. Xoay thuần dùng RotationGait. Cấu hình dáng đi nằm tại `config/gait_config.json`; giới hạn và ánh xạ servo tại các JSON tương ứng trong `config/`.

Các cột góc CSV giữ đúng thứ tự JointFrame từ `i_q1_deg` đến `n_q3_deg`. `stance_phase` là lịch pha chống; `ground_local_mm` là tọa độ trong hệ nền tham chiếu cục bộ. Lệnh chuẩn hóa không có đơn vị mm/s hoặc rad/s. CSV bắt đầu t=0 sau khi robot giả lập hoàn thành đứng lên; dt và seconds là bội của 0.02 giây, seconds chia hết cho dt.

## Phần cứng và kiểm chứng

Kết nối TCP với ESP32:

```bash
python -m pc_app.main --host 192.168.4.1
```

Đấu nối, nạp firmware và hiệu chỉnh được trình bày tại `docs/hardware-setup.md`. Góc toán học được ánh xạ qua offset, chiều quay và biên xung của từng servo trước khi xuất PWM.

Bản hợp nhất đã qua 93 phép kiểm tra trên PC, gồm đối chiếu trạng thái/góc/PWM giữa Python và C++. Kết quả không thay thế việc xác nhận vị trí gắn chân, hiệu chỉnh servo hoặc thử nghiệm trên ESP32/robot thật. Chưa kiểm chứng tải trọng, lực tiếp xúc, ma sát, tự va chạm hoặc ổn định động; biên chống sử dụng COM giả định.

## Tài liệu

- [Mô hình toán và thuật toán](motion_model/MO_HINH_TOAN.md)
- [Kiến trúc](docs/architecture.md)
- [Giao thức](docs/protocol.md)
- [Phần cứng](docs/hardware-setup.md)
- [Kiểm chứng và giới hạn](docs/verification.md)

## Tham khảo

- [RobotLK - 18DOF Hexapod](https://robotlk.com/build-your-own-18dof-hexapod-robot/)
- [Make Your Pet - Hexapod](https://github.com/MakeYourPet/hexapod)
- [ROSBug - Hexapod](https://github.com/A7med205/ROSBug-Hexapod)
