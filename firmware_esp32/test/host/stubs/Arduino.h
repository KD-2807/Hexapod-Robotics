// Stub Arduino tối thiểu: chỉ để biên dịch kiểm tra firmware trên PC (không chạy được thật).
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>

#define HIGH 1
#define LOW 0
#define OUTPUT 1

inline unsigned long millis() { return 0; }
inline unsigned long micros() { return 0; }
inline void delay(unsigned long) {}
inline void pinMode(int, int) {}
inline void digitalWrite(int, int) {}
inline uint32_t analogReadMilliVolts(int) { return 0; }

struct SerialClass {
    void begin(unsigned long) {}
    int available() { return 0; }
    int read() { return -1; }
    void println(const char*) {}
    int printf(const char*, ...) { return 0; }
};
static SerialClass Serial;
