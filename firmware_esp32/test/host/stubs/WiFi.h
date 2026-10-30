#pragma once
#include <Arduino.h>

struct String { const char* c_str() const { return ""; } };
struct IPAddress { String toString() const { return String(); } };
enum { WIFI_STA = 1, WIFI_AP = 2, WL_CONNECTED = 3 };

struct WiFiClient {
    explicit operator bool() const { return false; }
    bool connected() { return false; }
    int available() { return 0; }
    int read() { return -1; }
    size_t print(const char*) { return 0; }
    size_t print(char) { return 0; }
    void stop() {}
    void setNoDelay(bool) {}
};

struct WiFiServer {
    explicit WiFiServer(uint16_t) {}
    void begin() {}
    void setNoDelay(bool) {}
    WiFiClient available() { return WiFiClient(); }
};

struct WiFiClass {
    void persistent(bool) {}
    void setSleep(bool) {}
    void mode(int) {}
    void setHostname(const char*) {}
    void begin(const char*, const char*) {}
    int status() { return 0; }
    IPAddress localIP() { return IPAddress(); }
    IPAddress softAPIP() { return IPAddress(); }
    bool softAP(const char*, const char*) { return true; }
    void disconnect(bool) {}
};
static WiFiClass WiFi;
