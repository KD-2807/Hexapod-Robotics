# Biên dịch và chạy test C++ của firmware ngay trên PC (không cần ESP32).
#   make test        chạy toàn bộ unit test
#   make dump        in kết quả kịch bản (dùng cho tools/crosscheck_firmware.py)
CXX ?= g++
CXXFLAGS = -std=c++11 -O1 -Wall -Wextra -Werror -fno-exceptions -fno-rtti -I../../src -I../../include
# Mọi file nguồn trừ main.cpp và communication/ (phụ thuộc thư viện Arduino/WiFi)
SRC = $(shell find ../../src -name '*.cpp' ! -name main.cpp ! -path '*/communication/*')

host_test: host_test.cpp $(SRC) $(shell find ../../src ../../include -name '*.h')
	$(CXX) $(CXXFLAGS) host_test.cpp $(SRC) -o host_test

test: host_test
	./host_test unit

dump: host_test
	./host_test dump scenario.txt

clean:
	rm -f host_test
