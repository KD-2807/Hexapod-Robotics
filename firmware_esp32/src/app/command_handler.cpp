#include "command_handler.h"

#include <stdio.h>

namespace hexapod {

// Giống bản tham chiếu Python: thiếu tham số bắt buộc hoặc sai kiểu -> BAD_PARAMS.
bool CommandHandler::number(const char* key, bool hasDefault, float def, float& out, Result& err) {
    char path[32];
    snprintf(path, sizeof(path), "params.%s", key);
    if (!reader_.has(path)) {
        if (hasDefault) { out = def; return true; }
    } else if (reader_.getNumber(path, out)) {
        return true;
    }
    snprintf(msg_, sizeof(msg_), "Thiếu/sai tham số số: %s", key);
    err = Result::fail(ErrorCode::BadParams, msg_);
    return false;
}

Result CommandHandler::dispatch(const Command& cmd) {
    Result err;
    switch (cmd.type) {
        case CommandType::Enable: return mc_.enable();
        case CommandType::Disable: return mc_.disable();
        case CommandType::StandUp: return mc_.standUp();
        case CommandType::SitDown: return mc_.sitDown();
        case CommandType::Stop: return mc_.stop();
        case CommandType::Reset: return mc_.reset();
        case CommandType::Heartbeat:
        case CommandType::GetStatus: return Result::success();
        case CommandType::EmergencyStop: mc_.emergencyStop(); return Result::success();
        case CommandType::Move: {
            float vx, vy, wz, speed = 0.0f;
            if (!number("vx", true, 0.0f, vx, err) || !number("vy", true, 0.0f, vy, err) ||
                !number("wz", true, 0.0f, wz, err)) return err;
            const bool hasSpeed = reader_.has("params.speed");
            if (hasSpeed && !number("speed", false, 0.0f, speed, err)) return err;
            return mc_.move(vx, vy, wz, hasSpeed, speed);
        }
        case CommandType::SetGait: {
            const char* name = nullptr;
            GaitType gait;
            if (!reader_.getString("params.gait", name) || !gaitFromString(name, gait)) {
                return Result::fail(ErrorCode::BadParams, "gait không hợp lệ");
            }
            return mc_.setGait(gait);
        }
        case CommandType::SetSpeed: {
            float speed;
            if (!number("speed", false, 0.0f, speed, err)) return err;
            return mc_.setSpeed(speed);
        }
        case CommandType::SetPose: {
            float z, roll, pitch, yaw;
            if (!number("z", true, 0.0f, z, err) || !number("roll", true, 0.0f, roll, err) ||
                !number("pitch", true, 0.0f, pitch, err) || !number("yaw", true, 0.0f, yaw, err)) return err;
            return mc_.setPose(z, roll, pitch, yaw);
        }
        case CommandType::Action: {
            const char* name = "";
            reader_.getString("params.name", name);
            return mc_.runAction(name);
        }
        case CommandType::SetServo: {
            float leg, joint, angle;
            if (!number("leg", false, 0.0f, leg, err) || !number("joint", false, 0.0f, joint, err) ||
                !number("angle", false, 0.0f, angle, err)) return err;
            bool raw = false;
            float rawNumber = 0.0f;
            if (!reader_.getBool("params.raw", raw) && reader_.getNumber("params.raw", rawNumber)) raw = rawNumber != 0.0f;
            return mc_.setServo(static_cast<int>(leg), static_cast<int>(joint), angle, raw);
        }
    }
    return Result::fail(ErrorCode::BadCommand, "Lệnh không tồn tại");
}

size_t CommandHandler::handleLine(const char* line, char* out, size_t capacity) {
    Command cmd;
    const DecodeStatus decoded = decodeCommand(line, reader_, cmd);
    if (!decoded.ok()) return encodeError(out, capacity, decoded.seq, decoded.code, decoded.message);
    watchdog_.feed();                                    // gói hợp lệ nào cũng tính là heartbeat
    const Result r = dispatch(cmd);
    if (!r.ok()) return encodeError(out, capacity, cmd.seq, r.code, r.message);
    if (cmd.type == CommandType::GetStatus) return reporter_.encode(out, capacity, cmd.seq);
    return encodeAck(out, capacity, cmd.seq);
}

}  // namespace hexapod
