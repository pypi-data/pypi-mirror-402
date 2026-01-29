#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import platform
import threading

# 确保当前目录和pyds目录在Python路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
pyds_dir = os.path.join(current_dir, 'pyds')

for path in [pyds_dir, current_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

# 尝试导入app模块，优先使用编译后的.pyd文件
try:
    import app
    print("Successfully imported app module")
except ImportError as e:
    print(f"Failed to import app module: {e}")
    sys.exit(1)


def main():
    # 创建TableProcessor实例并启动主循环
    import tkinter as tk
    root = tk.Tk()
    table_processor = app.TableProcessor(root)
    root.mainloop()

if __name__ == '__main__':
    main()
