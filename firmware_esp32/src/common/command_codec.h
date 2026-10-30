#pragma once
#include <stddef.h>

#include "enums.h"
#include "json_mini.h"

namespace hexapod {

struct Command {
    long seq = 0;
    CommandType type = CommandType::Heartbeat;
};

struct DecodeStatus {
    ErrorCode code = ErrorCode::None;
    const char* message = "";
    long seq = 0;          // seq đọc được (0 nếu chưa đọc được) để gắn vào phản hồi lỗi
    bool ok() const { return code == ErrorCode::None; }
};

// Giải mã một dòng JSON thành Command. Tham số nằm trong `reader` ("params.<tên>").
DecodeStatus decodeCommand(const char* line, JsonReader& reader, Command& out);

// Mã hóa phản hồi: {"seq":N,"type":"ACK|ERROR|STATUS","data":{...}}
void beginResponse(JsonWriter& w, long seq, const char* type);   // mở object + khóa "data" (chờ giá trị)
void endResponse(JsonWriter& w);
size_t encodeAck(char* buffer, size_t capacity, long seq);
size_t encodeError(char* buffer, size_t capacity, long seq, ErrorCode code, const char* message);

}  // namespace hexapod
