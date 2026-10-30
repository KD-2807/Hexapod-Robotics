# Lệnh tắt cho các tác vụ thường dùng (Linux/macOS; trên Windows chạy trực tiếp các lệnh python bên dưới).
.PHONY: test test-py test-cpp crosscheck gen-config sim app clean

test: test-py                       ## toàn bộ test (Python + C++ + đối chiếu chéo)

test-py:
	python3 -m unittest discover -s tests -t .

test-cpp:
	$(MAKE) -C firmware_esp32/test/host test

crosscheck:
	python3 -m tools.crosscheck_firmware

gen-config:                         ## sinh lại firmware_esp32/include/generated_config.h từ config/*.json
	python3 -m tools.gen_firmware_config

sim:                                ## mô phỏng 3D, không cần robot
	python3 -m simulation.run_sim

app:                                ## ứng dụng điều khiển, kết nối robot giả lập cục bộ
	python3 -m pc_app.main --sim

clean:
	$(MAKE) -C firmware_esp32/test/host clean
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
