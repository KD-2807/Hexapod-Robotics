#pragma once
#include "../interfaces/transport.h"

namespace hexapod {

// Transport qua cổng USB-Serial của ESP32 (cùng giao thức dòng JSON). Khi dùng, KHÔNG in log ra Serial.
class SerialTransport : public Transport {
public:
    explicit SerialTransport(unsigned long baud) : baud_(baud) {}
    bool begin() override;
    void poll() override;
    bool readLine(char* buffer, size_t capacity) override;
    void sendLine(const char* line) override;
    bool isConnected() const override { return true; }          // không biết được đầu kia: dựa vào watchdog
    bool takeDisconnectEvent() override { return false; }

private:
    unsigned long baud_;
    char line_[256];
    size_t length_ = 0;
    bool overflow_ = false;
    bool ready_ = false;
};

}  // namespace hexapod
