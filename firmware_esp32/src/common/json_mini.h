#pragma once
#include <stddef.h>

namespace hexapod {

// Bộ đọc JSON tối giản cho lệnh PC -> robot: object phẳng, cho phép 1 cấp object lồng (params).
// Giá trị: số, chuỗi, true/false, null. Không hỗ trợ mảng. Khóa lồng truy cập dạng "params.vx".
class JsonReader {
public:
    enum Type { kNumber, kString, kBool, kNull };

    bool parse(const char* text);
    bool has(const char* key) const;
    bool getNumber(const char* key, float& out) const;
    bool getString(const char* key, const char*& out) const;
    bool getBool(const char* key, bool& out) const;
    bool typeOf(const char* key, Type& out) const;

private:
    struct Entry {
        char key[24];
        Type type;
        float num;
        char str[20];
    };
    static const int kMaxEntries = 16;

    Entry entries_[kMaxEntries];
    int count_ = 0;
    const char* p_ = nullptr;

    const Entry* find(const char* key) const;
    void skipWs();
    bool parseObject(const char* prefix, int depth);
    bool parseString(char* out, size_t cap);
    bool parseValue(const char* key, int depth);
    Entry* addEntry(const char* key);
};

// Bộ ghi JSON vào bộ đệm cố định. Kiểm tra ok() sau khi ghi xong.
class JsonWriter {
public:
    JsonWriter(char* buffer, size_t capacity);
    JsonWriter& beginObject();
    JsonWriter& endObject();
    JsonWriter& beginArray();
    JsonWriter& endArray();
    JsonWriter& key(const char* name);
    JsonWriter& number(float value, int decimals = 1);
    JsonWriter& integer(long value);
    JsonWriter& string(const char* value);
    JsonWriter& boolean(bool value);
    JsonWriter& null();
    bool ok() const { return !overflow_; }
    size_t length() const { return len_; }

private:
    char* buf_;
    size_t cap_;
    size_t len_ = 0;
    bool overflow_ = false;
    bool afterKey_ = false;
    bool needComma_[8];
    int depth_ = 0;

    void put(char c);
    void puts(const char* s);
    void separator();
    void writeString(const char* value);
    void open(char c);
    void close(char c);
};

}  // namespace hexapod
