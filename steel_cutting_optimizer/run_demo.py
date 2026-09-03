"""Chạy nhanh demo với data mặc định trong thư mục data/.

Cách dùng:
    python run_demo.py                # chạy + tự mở file Excel kết quả
    python run_demo.py --no-open      # chạy nhưng không tự mở Excel
    python run_demo.py --restarts 200 # tăng số lần tối ưu để kết quả tốt hơn
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent

if __name__ == "__main__":
    extra = [a for a in sys.argv[1:] if a != __file__]
    cmd = [sys.executable, str(BASE / "main.py"), "--out", str(BASE / "output")]
    cmd.extend(extra)
    subprocess.run(cmd, check=True)
