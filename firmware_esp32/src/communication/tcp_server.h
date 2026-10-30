#pragma once
#include <WiFi.h>

#include "../interfaces/transport.h"

namespace hexapod {

// TCP server 1 client: mỗi gói là một dòng JSON. Client mới thay client cũ.
class TcpServer : public Transport {
public:
    explicit TcpServer(uint16_t port) : server_(port) {}
    bool begin() override;
    void poll() override;
    bool readLine(char* buffer, size_t capacity) override;
    void sendLine(const char* line) override;
    bool isConnected() const override { return connected_; }
    bool takeDisconnectEvent() override;

private:
    WiFiServer server_;
    WiFiClient client_;
    bool connected_ = false;
    bool dropped_ = false;
    char line_[256];
    size_t length_ = 0;
    bool overflow_ = false;
    bool ready_ = false;

    void dropClient();
};

}  // namespace hexapod
