#include "serial_transport.h"

#include <Arduino.h>
#include <string.h>

namespace hexapod {

bool SerialTransport::begin() {
    Serial.begin(baud_);
    return true;
}

void SerialTransport::poll() {
    while (!ready_ && Serial.available() > 0) {
        const int c = Serial.read();
        if (c < 0) break;
        if (c == '\n') {
            if (!overflow_ && length_ > 0) { line_[length_] = '\0'; ready_ = true; }
            else { length_ = 0; overflow_ = false; }
        } else if (c != '\r') {
            if (length_ + 1 < sizeof(line_)) line_[length_++] = static_cast<char>(c);
            else overflow_ = true;       // dòng quá dài: bỏ cho tới '\n'
        }
    }
}

bool SerialTransport::readLine(char* buffer, size_t capacity) {
    if (!ready_) return false;
    strncpy(buffer, line_, capacity - 1);
    buffer[capacity - 1] = '\0';
    ready_ = false;
    length_ = 0;
    return true;
}

void SerialTransport::sendLine(const char* line) { Serial.println(line); }

}  // namespace hexapod
