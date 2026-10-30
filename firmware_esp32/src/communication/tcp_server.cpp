#include "tcp_server.h"

#include <string.h>

namespace hexapod {

bool TcpServer::begin() {
    server_.begin();
    server_.setNoDelay(true);
    return true;
}

void TcpServer::dropClient() {
    client_.stop();
    if (connected_) dropped_ = true;
    connected_ = false;
    length_ = 0;
    overflow_ = false;
    ready_ = false;
}

void TcpServer::poll() {
    WiFiClient incoming = server_.available();
    if (incoming) {                                   // client mới thay client cũ
        if (connected_) client_.stop();
        client_ = incoming;
        client_.setNoDelay(true);
        connected_ = true;
        length_ = 0;
        overflow_ = false;
        ready_ = false;
    }
    if (connected_ && !client_.connected()) dropClient();

    while (connected_ && !ready_ && client_.available() > 0) {
        const int c = client_.read();
        if (c < 0) break;
        if (c == '\n') {
            if (!overflow_ && length_ > 0) { line_[length_] = '\0'; ready_ = true; }
            else { length_ = 0; overflow_ = false; }
        } else if (c != '\r') {
            if (length_ + 1 < sizeof(line_)) line_[length_++] = static_cast<char>(c);
            else overflow_ = true;                    // dòng quá dài: bỏ cho tới '\n'
        }
    }
}

bool TcpServer::readLine(char* buffer, size_t capacity) {
    if (!ready_) return false;
    strncpy(buffer, line_, capacity - 1);
    buffer[capacity - 1] = '\0';
    ready_ = false;
    length_ = 0;
    return true;
}

void TcpServer::sendLine(const char* line) {
    if (!connected_) return;
    client_.print(line);
    client_.print('\n');
}

bool TcpServer::takeDisconnectEvent() {
    const bool d = dropped_;
    dropped_ = false;
    return d;
}

}  // namespace hexapod
