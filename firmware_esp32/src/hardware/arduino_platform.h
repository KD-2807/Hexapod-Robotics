#pragma once
// Cài đặt các interface bằng API Arduino (chỉ biên dịch trên ESP32 hoặc với stub trong test/host/stubs).
#include <Arduino.h>
#include <Wire.h>

#include "../interfaces/clock.h"
#include "../interfaces/i2c_bus.h"
#include "../interfaces/io.h"

namespace hexapod {

class ArduinoClock : public Clock {
public:
    uint32_t millis() override { return ::millis(); }
    uint32_t micros() override { return ::micros(); }
    void delayMs(uint32_t ms) override { ::delay(ms); }
};

class WireI2CBus : public I2CBus {
public:
    // Không chạm phần cứng trong constructor (biến toàn cục khởi tạo trước khi framework Arduino chạy): gọi begin() trong setup().
    WireI2CBus(TwoWire& wire, int sda, int scl, uint32_t frequencyHz)
        : wire_(wire), sda_(sda), scl_(scl), frequencyHz_(frequencyHz) {}
    void begin() {
        wire_.begin(sda_, scl_);
        wire_.setClock(frequencyHz_);
    }
    bool write(uint8_t address, const uint8_t* data, size_t length) override {
        wire_.beginTransmission(address);
        wire_.write(data, length);
        return wire_.endTransmission() == 0;
    }
    bool readRegister(uint8_t address, uint8_t reg, uint8_t* out, size_t length) override {
        wire_.beginTransmission(address);
        wire_.write(reg);
        if (wire_.endTransmission(false) != 0) return false;
        if (static_cast<size_t>(wire_.requestFrom(static_cast<int>(address), static_cast<int>(length))) != length) return false;
        for (size_t i = 0; i < length; ++i) out[i] = static_cast<uint8_t>(wire_.read());
        return true;
    }
    bool probe(uint8_t address) override {
        wire_.beginTransmission(address);
        return wire_.endTransmission() == 0;
    }

private:
    TwoWire& wire_;
    int sda_, scl_;
    uint32_t frequencyHz_;
};

class ArduinoPinOutput : public DigitalOutput {
public:
    explicit ArduinoPinOutput(int pin) : pin_(pin) {}
    void begin() { if (pin_ >= 0) { pinMode(pin_, OUTPUT); digitalWrite(pin_, HIGH); } }   // HIGH = đầu ra servo bị ngắt
    void write(bool high) override { if (pin_ >= 0) digitalWrite(pin_, high ? HIGH : LOW); }

private:
    int pin_;
};

class ArduinoAnalogInput : public AnalogInput {
public:
    explicit ArduinoAnalogInput(int pin) : pin_(pin) {}
    float readMilliVolts() override { return static_cast<float>(analogReadMilliVolts(pin_)); }

private:
    int pin_;
};

}  // namespace hexapod
