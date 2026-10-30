#include "robot_app.h"

namespace hexapod {

constexpr int RobotApp::kMaxLinesPerStep;
constexpr size_t RobotApp::kRxCapacity;
constexpr size_t RobotApp::kTxCapacity;

void RobotApp::step(float dt) {
    transport_.poll();
    for (int i = 0; i < kMaxLinesPerStep && transport_.readLine(rx_, sizeof(rx_)); ++i) {
        const size_t n = handler_.handleLine(rx_, tx_, sizeof(tx_));
        if (n > 0) transport_.sendLine(tx_);
    }
    if (transport_.takeDisconnectEvent()) watchdog_.trigger();
    watchdog_.update(dt);
    controller_.update(dt);
    reporter_.setConnected(transport_.isConnected());
    if (transport_.isConnected() && reporter_.due(dt)) {
        if (reporter_.encode(tx_, sizeof(tx_), 0) > 0) transport_.sendLine(tx_);
    }
}

}  // namespace hexapod
