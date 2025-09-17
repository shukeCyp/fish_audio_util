#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Fish Audio 批量音频生成工具
主程序入口文件

作者: Fish Audio Project
版本: 1.0.0
许可证: MIT
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from loguru import logger

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow

__version__ = "1.0.0"
__author__ = "Fish Audio Project"

def setup_logging():
    """设置日志配置"""
    logger.remove()  # 移除默认处理器
    
    # 添加文件日志
    logger.add(
        "logs/fish_audio.log",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        encoding="utf-8"
    )
    
    # 添加控制台日志（仅在开发模式）
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        pass
    else:
        # 开发环境
        logger.add(
            sys.stderr,
            level="DEBUG",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
        )

def get_resource_path(relative_path):
    """获取资源文件路径，兼容打包后的环境"""
    try:
        # PyInstaller 创建临时文件夹，将路径存储在 _MEIPASS 中
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def create_directories():
    """创建必要的目录"""
    directories = ['logs', 'temp', 'output']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def main():
    """主函数"""
    try:
        # 创建必要目录
        create_directories()
        
        # 设置日志
        setup_logging()
        logger.info(f"启动 Fish Audio 批量音频生成工具 v{__version__}")
        
        # 设置高 DPI 支持（必须在创建QApplication之前）
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 创建 QApplication 实例
        app = QApplication(sys.argv)
        app.setApplicationName("Fish Audio")
        app.setApplicationVersion(__version__)
        app.setOrganizationName("Fish Audio Project")
        
        # 设置应用程序图标
        icon_path = get_resource_path("resources/icons/app.ico")
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
        
        # 设置样式表
                    # 不使用CSS样式，使用系统默认样式
            pass
        
        # 创建并显示主窗口
        window = MainWindow()
        window.show()
        
        logger.info("应用程序启动成功")
        
        # 运行应用程序
        exit_code = app.exec_()
        logger.info(f"应用程序退出，退出码: {exit_code}")
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.exception(f"应用程序启动失败: {e}")
        
        # 显示错误对话框
        if 'app' in locals():
            QMessageBox.critical(
                None,
                "启动错误",
                f"应用程序启动失败:\n{str(e)}\n\n请检查日志文件获取详细信息。"
            )
        
        sys.exit(1)

if __name__ == "__main__":
    main() 