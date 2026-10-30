#include "wifi_manager.h"

#include <Arduino.h>
#include <WiFi.h>
#include <stdio.h>

#include "../../include/generated_config.h"

namespace hexapod {

WifiManager::Mode WifiManager::begin(char* ip, unsigned ipCapacity) {
    WiFi.persistent(false);
    WiFi.setSleep(false);                     // giảm trễ gói tin
    WiFi.mode(WIFI_STA);
    WiFi.setHostname(cfg::kHostname);
    WiFi.begin(cfg::kWifiSsid, cfg::kWifiPassword);
    const unsigned long start = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - start < cfg::kWifiTimeoutS * 1000UL) delay(100);

    if (WiFi.status() == WL_CONNECTED) {
        snprintf(ip, ipCapacity, "%s", WiFi.localIP().toString().c_str());
        return Mode::Station;
    }
    WiFi.disconnect(true);
    WiFi.mode(WIFI_AP);
    if (!WiFi.softAP(cfg::kApSsid, cfg::kApPassword)) return Mode::None;
    snprintf(ip, ipCapacity, "%s", WiFi.softAPIP().toString().c_str());
    return Mode::AccessPoint;
}

}  // namespace hexapod
