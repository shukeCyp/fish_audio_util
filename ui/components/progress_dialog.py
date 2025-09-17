#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
进度对话框组件

提供一个模态对话框来显示长时间操作的进度
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QPushButton, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class ProgressDialog(QDialog):
    """进度对话框类"""
    
    def __init__(self, title="处理进度", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(500, 300)
        
        self.init_ui()
        
        # 定时器用于更新界面
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题标签
        self.title_label = QLabel("正在处理...")
        self.title_label.setAlignment(Qt.AlignCenter)
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.title_label.setFont(font)
        layout.addWidget(self.title_label)
        
        # 当前文件标签
        self.current_file_label = QLabel("")
        self.current_file_label.setAlignment(Qt.AlignCenter)
        self.current_file_label.setWordWrap(True)
        layout.addWidget(self.current_file_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)
        
        # 进度信息
        progress_info_layout = QHBoxLayout()
        
        self.progress_label = QLabel("0/0")
        progress_info_layout.addWidget(self.progress_label)
        
        progress_info_layout.addStretch()
        
        self.percentage_label = QLabel("0%")
        progress_info_layout.addWidget(self.percentage_label)
        
        layout.addLayout(progress_info_layout)
        
        # 详细信息文本框
        self.details_text = QTextEdit()
        self.details_text.setMaximumHeight(100)
        self.details_text.setReadOnly(True)
        # 使用系统等宽字体
        font = QFont()
        font.setFamily("monospace")
        font.setPointSize(8)
        self.details_text.setFont(font)
        layout.addWidget(self.details_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("取消")
        self.cancel_button.setMinimumWidth(80)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def set_range(self, minimum: int, maximum: int):
        """设置进度条范围"""
        self.progress_bar.setRange(minimum, maximum)
    
    def set_value(self, value: int):
        """设置进度条当前值"""
        self.progress_bar.setValue(value)
        self.update_progress_info()
    
    def set_title(self, title: str):
        """设置标题"""
        self.title_label.setText(title)
    
    def set_current_file(self, filename: str):
        """设置当前处理的文件名"""
        self.current_file_label.setText(f"正在处理: {filename}")
    
    def add_detail(self, message: str):
        """添加详细信息"""
        self.details_text.append(message)
        # 自动滚动到底部
        scrollbar = self.details_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_progress_info(self):
        """更新进度信息"""
        current = self.progress_bar.value()
        maximum = self.progress_bar.maximum()
        
        # 更新进度标签
        self.progress_label.setText(f"{current}/{maximum}")
        
        # 更新百分比
        if maximum > 0:
            percentage = int((current / maximum) * 100)
            self.percentage_label.setText(f"{percentage}%")
        else:
            self.percentage_label.setText("0%")
    
    def start_update_timer(self, interval: int = 100):
        """启动更新定时器"""
        self.update_timer.start(interval)
    
    def stop_update_timer(self):
        """停止更新定时器"""
        self.update_timer.stop()
    
    def update_display(self):
        """更新显示（由定时器调用）"""
        # 这里可以添加定期更新的逻辑
        pass
    
    def set_completed(self):
        """设置为完成状态"""
        self.set_title("处理完成")
        self.current_file_label.setText("所有文件处理完成")
        self.cancel_button.setText("关闭")
        self.stop_update_timer()
    
    def set_cancelled(self):
        """设置为取消状态"""
        self.set_title("处理已取消")
        self.current_file_label.setText("用户取消了处理")
        self.cancel_button.setText("关闭")
        self.stop_update_timer()
    
    def set_error(self, error_message: str):
        """设置为错误状态"""
        self.set_title("处理出错")
        self.current_file_label.setText(f"错误: {error_message}")
        self.cancel_button.setText("关闭")
        self.stop_update_timer()
    
    def closeEvent(self, event):
        """关闭事件"""
        self.stop_update_timer()
        super().closeEvent(event) 