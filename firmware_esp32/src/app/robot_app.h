#pragma once
#include "../interfaces/transport.h"
#include "command_handler.h"
#include "watchdog.h"

namespace hexapod {

// Một chu kỳ của vòng lặp firmware: nhận lệnh -> xử lý -> watchdog -> điều khiển -> đẩy STATUS.
// Tách khỏi main.cpp để chạy thử được trên PC với Transport/ActuatorBackend giả.
class RobotApp {
public:
    RobotApp(Transport& transport, MotionController& controller, StatusReporter& reporter,
             CommandHandler& handler, Watchdog& watchdog)
        : transport_(transport), controller_(controller), reporter_(reporter), handler_(handler),
          watchdog_(watchdog) {}

    void step(float dt);

private:
    static constexpr int kMaxLinesPerStep = 8;
    static constexpr size_t kRxCapacity = 256, kTxCapacity = 768;
    Transport& transport_;
    MotionController& controller_;
    StatusReporter& reporter_;
    CommandHandler& handler_;
    Watchdog& watchdog_;
    char rx_[kRxCapacity];
    char tx_[kTxCapacity];
};

}  // namespace hexapod
