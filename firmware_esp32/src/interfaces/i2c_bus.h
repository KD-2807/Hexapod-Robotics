#pragma once
#include <stddef.h>
#include <stdint.h>

namespace hexapod {

class I2CBus {
public:
    virtual ~I2CBus() {}
    virtual bool write(uint8_t address, const uint8_t* data, size_t length) = 0;
    virtual bool readRegister(uint8_t address, uint8_t reg, uint8_t* out, size_t length) = 0;
    virtual bool probe(uint8_t address) = 0;
};

}  // namespace hexapod
