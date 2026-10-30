"""Script PlatformIO (pre): sinh generated_config.h từ config/*.json trước khi biên dịch."""
import os
import subprocess
import sys

Import("env")  # noqa: F821  (do PlatformIO cung cấp)

project_root = os.path.dirname(env["PROJECT_DIR"])  # noqa: F821
subprocess.check_call([sys.executable, "-m", "tools.gen_firmware_config"], cwd=project_root)
