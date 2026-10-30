#include "json_mini.h"

#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

namespace hexapod {

// ------------------------------------------------------------------ JsonReader
bool JsonReader::parse(const char* text) {
    count_ = 0;
    p_ = text;
    skipWs();
    if (!parseObject("", 0)) return false;
    skipWs();
    return *p_ == '\0';
}

void JsonReader::skipWs() {
    while (*p_ == ' ' || *p_ == '\t' || *p_ == '\r' || *p_ == '\n') ++p_;
}

bool JsonReader::parseString(char* out, size_t cap) {
    if (*p_ != '"') return false;
    ++p_;
    size_t n = 0;
    while (*p_ && *p_ != '"') {
        char c = *p_++;
        if (c == '\\') {
            c = *p_++;
            if (c == 'n') c = '\n';
            else if (c == 't') c = '\t';
            else if (c != '"' && c != '\\' && c != '/') return false;
        }
        if (n + 1 >= cap) return false;     // quá dài
        out[n++] = c;
    }
    if (*p_ != '"') return false;
    ++p_;
    out[n] = '\0';
    return true;
}

JsonReader::Entry* JsonReader::addEntry(const char* key) {
    if (count_ >= kMaxEntries || strlen(key) >= sizeof(entries_[0].key)) return nullptr;
    Entry* e = &entries_[count_++];
    strcpy(e->key, key);
    e->num = 0.0f;
    e->str[0] = '\0';
    return e;
}

bool JsonReader::parseValue(const char* key, int depth) {
    skipWs();
    if (*p_ == '{') {
        if (depth >= 1) return false;
        char prefix[24];
        if (strlen(key) + 2 > sizeof(prefix)) return false;
        snprintf(prefix, sizeof(prefix), "%s.", key);
        return parseObject(prefix, depth + 1);
    }
    Entry* e = addEntry(key);
    if (!e) return false;
    if (*p_ == '"') {
        e->type = kString;
        return parseString(e->str, sizeof(e->str));
    }
    if (strncmp(p_, "true", 4) == 0)  { e->type = kBool; e->num = 1.0f; p_ += 4; return true; }
    if (strncmp(p_, "false", 5) == 0) { e->type = kBool; e->num = 0.0f; p_ += 5; return true; }
    if (strncmp(p_, "null", 4) == 0)  { e->type = kNull; p_ += 4; return true; }
    if (*p_ == '-' || isdigit(static_cast<unsigned char>(*p_))) {
        char* end = nullptr;
        e->type = kNumber;
        e->num = static_cast<float>(strtod(p_, &end));
        if (end == p_) return false;
        p_ = end;
        return true;
    }
    return false;
}

bool JsonReader::parseObject(const char* prefix, int depth) {
    if (*p_ != '{') return false;
    ++p_;
    skipWs();
    if (*p_ == '}') { ++p_; return true; }
    while (true) {
        skipWs();
        char name[20];
        if (!parseString(name, sizeof(name))) return false;
        skipWs();
        if (*p_ != ':') return false;
        ++p_;
        char full[24];
        if (strlen(prefix) + strlen(name) >= sizeof(full)) return false;
        snprintf(full, sizeof(full), "%s%s", prefix, name);
        if (!parseValue(full, depth)) return false;
        skipWs();
        if (*p_ == ',') { ++p_; continue; }
        if (*p_ == '}') { ++p_; return true; }
        return false;
    }
}

const JsonReader::Entry* JsonReader::find(const char* key) const {
    for (int i = 0; i < count_; ++i) {
        if (strcmp(entries_[i].key, key) == 0) return &entries_[i];
    }
    return nullptr;
}

bool JsonReader::has(const char* key) const { return find(key) != nullptr; }

bool JsonReader::typeOf(const char* key, Type& out) const {
    const Entry* e = find(key);
    if (!e) return false;
    out = e->type;
    return true;
}

bool JsonReader::getNumber(const char* key, float& out) const {
    const Entry* e = find(key);
    if (!e || e->type != kNumber) return false;
    out = e->num;
    return true;
}

bool JsonReader::getString(const char* key, const char*& out) const {
    const Entry* e = find(key);
    if (!e || e->type != kString) return false;
    out = e->str;
    return true;
}

bool JsonReader::getBool(const char* key, bool& out) const {
    const Entry* e = find(key);
    if (!e || e->type != kBool) return false;
    out = e->num != 0.0f;
    return true;
}

// ------------------------------------------------------------------ JsonWriter
JsonWriter::JsonWriter(char* buffer, size_t capacity) : buf_(buffer), cap_(capacity) {
    for (int i = 0; i < 8; ++i) needComma_[i] = false;
    if (cap_ > 0) buf_[0] = '\0';
}

void JsonWriter::put(char c) {
    if (len_ + 1 >= cap_) { overflow_ = true; return; }
    buf_[len_++] = c;
    buf_[len_] = '\0';
}

void JsonWriter::puts(const char* s) { while (*s) put(*s++); }

void JsonWriter::separator() {
    if (afterKey_) { afterKey_ = false; return; }
    if (needComma_[depth_]) put(',');
    needComma_[depth_] = true;
}

void JsonWriter::open(char c) {
    separator();
    put(c);
    if (depth_ < 7) ++depth_; else overflow_ = true;
    needComma_[depth_] = false;
}

void JsonWriter::close(char c) {
    if (depth_ > 0) --depth_;
    put(c);
}

JsonWriter& JsonWriter::beginObject() { open('{'); return *this; }
JsonWriter& JsonWriter::endObject() { close('}'); return *this; }
JsonWriter& JsonWriter::beginArray() { open('['); return *this; }
JsonWriter& JsonWriter::endArray() { close(']'); return *this; }

JsonWriter& JsonWriter::key(const char* name) {
    separator();
    writeString(name);
    put(':');
    afterKey_ = true;
    return *this;
}

void JsonWriter::writeString(const char* value) {
    put('"');
    for (const char* c = value; *c; ++c) {
        switch (*c) {
            case '"': puts("\\\""); break;
            case '\\': puts("\\\\"); break;
            case '\n': puts("\\n"); break;
            case '\r': puts("\\r"); break;
            case '\t': puts("\\t"); break;
            default: put(*c);
        }
    }
    put('"');
}

JsonWriter& JsonWriter::string(const char* value) {
    separator();
    writeString(value);
    return *this;
}

JsonWriter& JsonWriter::number(float value, int decimals) {
    separator();
    char tmp[24];
    snprintf(tmp, sizeof(tmp), "%.*f", decimals, isfinite(value) ? value : 0.0f);
    puts(tmp);
    return *this;
}

JsonWriter& JsonWriter::integer(long value) {
    separator();
    char tmp[16];
    snprintf(tmp, sizeof(tmp), "%ld", value);
    puts(tmp);
    return *this;
}

JsonWriter& JsonWriter::boolean(bool value) { separator(); puts(value ? "true" : "false"); return *this; }
JsonWriter& JsonWriter::null() { separator(); puts("null"); return *this; }

}  // namespace hexapod
