#pragma once

namespace hexapod {

class DigitalOutput {            // chân GPIO xuất (ví dụ OE của PCA9685)
public:
    virtual ~DigitalOutput() {}
    virtual void write(bool high) = 0;
};

class AnalogInput {              // đọc ADC, trả về milivolt tại chân
public:
    virtual ~AnalogInput() {}
    virtual float readMilliVolts() = 0;
};

}  // namespace hexapod
