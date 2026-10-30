#pragma once
#include <stddef.h>

namespace hexapod {

// Kênh truyền dạng dòng (mỗi gói là một dòng kết thúc '\n'): TCP hoặc Serial.
class Transport {
public:
    virtual ~Transport() {}
    virtual bool begin() = 0;
    virtual void poll() = 0;                                   // nhận kết nối mới, gom byte vào bộ đệm
    virtual bool readLine(char* buffer, size_t capacity) = 0;  // true nếu lấy được 1 dòng (không gồm '\n')
    virtual void sendLine(const char* line) = 0;
    virtual bool isConnected() const = 0;
    virtual bool takeDisconnectEvent() = 0;                    // true đúng 1 lần sau khi client vừa rớt
};

}  // namespace hexapod
