#pragma once

namespace hexapod {

class WatchdogListener {
public:
    virtual ~WatchdogListener() {}
    virtual void onTimeout() = 0;
};

// Mất heartbeat quá timeout -> báo listener một lần (robot dừng và ngồi xuống).
class Watchdog {
public:
    Watchdog(float timeoutS, WatchdogListener& listener) : timeout_(timeoutS), listener_(listener) {}

    void feed() { elapsed_ = 0.0f; armed_ = true; fired_ = false; }    // nhận bất kỳ gói hợp lệ nào từ PC
    void disarm() { armed_ = false; }
    void trigger() {                                                    // kích hoạt ngay (mất kết nối TCP)
        if (armed_ && !fired_) { fired_ = true; listener_.onTimeout(); }
    }
    void update(float dt) {
        if (!armed_ || fired_) return;
        elapsed_ += dt;
        if (elapsed_ > timeout_) trigger();
    }

private:
    float timeout_;
    WatchdogListener& listener_;
    float elapsed_ = 0.0f;
    bool armed_ = false;
    bool fired_ = false;
};

}  // namespace hexapod
