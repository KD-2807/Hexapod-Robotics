#pragma once
#include <Arduino.h>

struct TwoWire {
    bool begin(int, int) { return true; }
    void setClock(uint32_t) {}
    void beginTransmission(uint8_t) {}
    size_t write(const uint8_t*, size_t n) { return n; }
    size_t write(uint8_t) { return 1; }
    uint8_t endTransmission(bool = true) { return 0; }
    size_t requestFrom(int, int n) { return static_cast<size_t>(n); }
    int read() { return 0; }
};
static TwoWire Wire;
