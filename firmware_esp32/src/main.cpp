// Firmware hexapod cho ESP32-WROOM. Cấu hình lấy từ include/generated_config.h (sinh từ config/*.json).
#include <Arduino.h>
#include <Wire.h>

#include "app/command_handler.h"
#include "app/robot_app.h"
#include "app/sensor_hub.h"
#include "app/status_reporter.h"
#include "app/watchdog.h"
#include "communication/serial_transport.h"
#include "communication/tcp_server.h"
#include "communication/wifi_manager.h"
#include "hardware/arduino_platform.h"
#include "hardware/pca9685_backend.h"
#include "motion_core/motion_controller.h"

using namespace hexapod;

// Mặc định giao tiếp TCP qua WiFi. Build với -DHEXAPOD_SERIAL_TRANSPORT để dùng cáp USB (khi đó tắt log).
#ifdef HEXAPOD_SERIAL_TRANSPORT
#define LOG(...) ((void)0)
#else
#define LOG(...) Serial.printf(__VA_ARGS__)
#endif

namespace {

// ---- nền tảng
ArduinoClock gClock;
WireI2CBus gBus(Wire, cfg::kI2cSda, cfg::kI2cScl, cfg::kI2cFrequencyHz);
ArduinoPinOutput gOutputEnable(cfg::kServoOutputEnablePin);
ArduinoAnalogInput gBatteryInput(cfg::kBatteryAdcPin);

// ---- phần cứng robot
ServoManager gServos(gBus, gClock);
PCA9685Backend gBackend(gServos, cfg::kServoOutputEnablePin >= 0 ? &gOutputEnable : nullptr);
Mpu6050 gImu(gBus, gClock, cfg::kImuAddress);
BatteryMonitor gBattery(gBatteryInput, cfg::kBatteryDividerRatio);

// ---- lõi điều khiển
Hexapod gHexapod;
BodyKinematics gBodyKin(gHexapod);
MotionCoordinator gCoordinator(gHexapod, gBodyKin);
SafetyGuard gGuard(gHexapod);
PostureGenerator gPosture;
GaitFactory gGaits(gHexapod);
MotionController gController(gHexapod, gCoordinator, gGuard, gBackend, gPosture, gGaits);

// ---- ứng dụng
struct LinkLostAction : WatchdogListener {
    void onTimeout() override { gController.onLinkLost(); LOG("[watchdog] mat heartbeat -> dung va ngoi\n"); }
} gLinkLost;
Watchdog gWatchdog(cfg::kWatchdogTimeoutS, gLinkLost);
StatusReporter gReporter(gController, cfg::kStatusHz);
CommandHandler gHandler(gController, gReporter, gWatchdog);
#ifdef HEXAPOD_SERIAL_TRANSPORT
SerialTransport gTransport(115200);
#else
TcpServer gTransport(cfg::kTcpPort);
#endif
RobotApp gApp(gTransport, gController, gReporter, gHandler, gWatchdog);
SensorHub gSensors(cfg::kImuEnabled ? &gImu : nullptr, cfg::kImuAlpha, &gBattery, gReporter);

uint32_t gLastMicros = 0;
constexpr uint32_t kPeriodUs = 1000000UL / cfg::kLoopHz;

void scanI2c() {
    uint8_t found[8];
    int count = 0;
    for (uint8_t addr = 0x08; addr < 0x78 && count < 8; ++addr) {
        if (gBus.probe(addr)) found[count++] = addr;
    }
    gReporter.setI2cDevices(found, count);
    LOG("[i2c] tim thay %d thiet bi\n", count);
}

}  // namespace

void setup() {
#ifndef HEXAPOD_SERIAL_TRANSPORT
    Serial.begin(115200);
#endif
    delay(200);
    LOG("\n[hexapod] khoi dong\n");

    gBus.begin();
    gOutputEnable.begin();

    scanI2c();
    if (cfg::kImuEnabled && !gImu.begin()) LOG("[imu] khong thay MPU6050 (bo qua)\n");

#ifndef HEXAPOD_SERIAL_TRANSPORT
    WifiManager wifi;
    char ip[24] = "";
    const WifiManager::Mode mode = wifi.begin(ip, sizeof(ip));
    LOG("[wifi] %s, IP %s, cong TCP %d\n", mode == WifiManager::Mode::Station ? "station" :
        mode == WifiManager::Mode::AccessPoint ? "AP du phong" : "LOI", ip, cfg::kTcpPort);
#endif
    gTransport.begin();
    gLastMicros = micros();
}

void loop() {
    const uint32_t now = micros();
    if (now - gLastMicros < kPeriodUs) return;
    float dt = static_cast<float>(now - gLastMicros) * 1e-6f;
    gLastMicros = now;
    if (dt > 0.1f) dt = 0.1f;                  // sau khi bị treo lâu, không tích lũy bước nhảy lớn

    gSensors.update(dt);
    gApp.step(dt);
}
