#pragma once

namespace hexapod {

// Kết nối WiFi (chế độ station); nếu quá thời gian chờ thì tự phát AP dự phòng.
class WifiManager {
public:
    enum class Mode { None, Station, AccessPoint };
    // Trả về chế độ đang dùng; ip nhận địa chỉ IP dạng chuỗi (đệm >= 16 byte).
    Mode begin(char* ip, unsigned ipCapacity);
};

}  // namespace hexapod
