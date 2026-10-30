#include "command_codec.h"

#include <math.h>

namespace hexapod {

DecodeStatus decodeCommand(const char* line, JsonReader& reader, Command& out) {
    DecodeStatus st;
    if (!reader.parse(line)) {
        st.code = ErrorCode::BadFormat;
        st.message = "JSON hỏng";
        return st;
    }
    float seq = 0;
    if (!reader.getNumber("seq", seq) || seq != floorf(seq)) {
        st.code = ErrorCode::BadFormat;
        st.message = "Thiếu trường seq";
        return st;
    }
    st.seq = static_cast<long>(seq);
    out.seq = st.seq;
    const char* name = nullptr;
    if (!reader.getString("cmd", name) || !commandFromString(name, out.type)) {
        st.code = ErrorCode::BadCommand;
        st.message = "Lệnh không tồn tại";
        return st;
    }
    if (reader.has("params")) {            // "params" xuất hiện như giá trị lá nghĩa là không phải object
        st.code = ErrorCode::BadFormat;
        st.message = "params phải là object";
    }
    return st;
}

void beginResponse(JsonWriter& w, long seq, const char* type) {
    w.beginObject().key("seq").integer(seq).key("type").string(type).key("data");
}

void endResponse(JsonWriter& w) { w.endObject(); }

size_t encodeAck(char* buffer, size_t capacity, long seq) {
    JsonWriter w(buffer, capacity);
    beginResponse(w, seq, "ACK");
    w.beginObject().endObject();
    endResponse(w);
    return w.length();
}

size_t encodeError(char* buffer, size_t capacity, long seq, ErrorCode code, const char* message) {
    JsonWriter w(buffer, capacity);
    beginResponse(w, seq, "ERROR");
    w.beginObject().key("code").string(toString(code)).key("message").string(message).endObject();
    endResponse(w);
    return w.length();
}

}  // namespace hexapod
