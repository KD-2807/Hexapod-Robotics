#pragma once
#include <stdint.h>

namespace hexapod {

class Clock {
public:
    virtual ~Clock() {}
    virtual uint32_t millis() = 0;
    virtual uint32_t micros() = 0;
    virtual void delayMs(uint32_t ms) = 0;
};

}  // namespace hexapod
