#include "status_reporter.h"

#include "../common/command_codec.h"

namespace hexapod {

constexpr int StatusReporter::kMaxDevices;

void StatusReporter::setI2cDevices(const uint8_t* addresses, int count) {
    i2cCount_ = count > kMaxDevices ? kMaxDevices : count;
    for (int i = 0; i < i2cCount_; ++i) i2c_[i] = addresses[i];
}

size_t StatusReporter::encode(char* buffer, size_t capacity, long seq) const {
    JsonWriter w(buffer, capacity);
    beginResponse(w, seq, "STATUS");
    const BodyPose& pose = controller_.pose();
    w.beginObject();
    w.key("state").string(toString(controller_.state()));
    w.key("gait").string(toString(controller_.gait()));
    w.key("speed").number(controller_.speed(), 2);
    w.key("pose").beginObject().key("z").number(pose.z).key("roll").number(pose.roll)
        .key("pitch").number(pose.pitch).key("yaw").number(pose.yaw).endObject();
    w.key("angles").beginArray();
    for (int i = 0; i < kNumServos; ++i) w.number(controller_.frame().angles[i]);
    w.endArray();
    w.key("error");
    if (controller_.error().active) {
        w.beginObject().key("code").string(toString(controller_.error().code))
            .key("message").string(controller_.error().message).endObject();
    } else {
        w.null();
    }
    w.key("i2c").beginArray();
    for (int i = 0; i < i2cCount_; ++i) w.integer(i2c_[i]);
    w.endArray();
    if (hasBattery_) w.key("battery_v").number(batteryV_, 2);
    if (hasImu_) w.key("imu").beginObject().key("roll").number(imuRoll_).key("pitch").number(imuPitch_).endObject();
    w.key("connected").boolean(connected_);
    w.endObject();
    endResponse(w);
    return w.ok() ? w.length() : 0;
}

}  // namespace hexapod
