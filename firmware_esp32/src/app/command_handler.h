#pragma once
#include <stddef.h>

#include "../common/command_codec.h"
#include "../motion_core/motion_controller.h"
#include "status_reporter.h"
#include "watchdog.h"

namespace hexapod {

// Command (JSON) -> MotionController -> Response (JSON).
class CommandHandler {
public:
    CommandHandler(MotionController& controller, StatusReporter& reporter, Watchdog& watchdog)
        : mc_(controller), reporter_(reporter), watchdog_(watchdog) {}

    // Xử lý một dòng lệnh; ghi phản hồi vào `out` và trả về độ dài (0 nếu không đủ chỗ).
    size_t handleLine(const char* line, char* out, size_t capacity);

private:
    MotionController& mc_;
    StatusReporter& reporter_;
    Watchdog& watchdog_;
    JsonReader reader_;
    char msg_[48] = {0};

    Result dispatch(const Command& cmd);
    bool number(const char* key, bool hasDefault, float def, float& out, Result& err);
};

}  // namespace hexapod
