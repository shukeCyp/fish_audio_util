#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口界面模块

包含应用程序的主要用户界面，提供文件夹选择、音色选择、
批量处理控制等功能。
"""

import os
import sys
from typing import List, Optional
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QComboBox, QTextEdit, QProgressBar,
    QFileDialog, QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
    QSplitter, QStatusBar, QMenuBar, QAction, QApplication, QDialog,
    QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt5.QtGui import QFont, QIcon, QPixmap, QTextCursor
from loguru import logger

from core.audio_generator import AudioGenerator
from core.file_processor import FileProcessor
from core.config_manager import ConfigManager
from ui.components.progress_dialog import ProgressDialog
from ui.components.settings_dialog import SettingsDialog


class ApiTestThread(QThread):
    """API测试线程，避免阻塞UI"""
    test_completed = pyqtSignal(bool, str)  # 成功与否，消息
    
    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key
    
    def run(self):
        """执行API测试"""
        try:
            from core.audio_generator import AudioGenerator
            temp_generator = AudioGenerator(api_key=self.api_key)
            
            if temp_generator.test_connection():
                self.test_completed.emit(True, "连接成功")
            else:
                self.test_completed.emit(False, "连接失败，请检查密钥是否正确")
                
        except Exception as e:
            self.test_completed.emit(False, f"测试过程中出错: {str(e)}")


class VoiceLoadThread(QThread):
    """音色加载线程，避免阻塞UI"""
    voices_loaded = pyqtSignal(list)  # 音色列表
    load_error = pyqtSignal(str)  # 错误消息
    
    def __init__(self, audio_generator):
        super().__init__()
        self.audio_generator = audio_generator
    
    def run(self):
        """执行音色加载"""
        try:
            voices = self.audio_generator.get_available_voices()
            self.voices_loaded.emit(voices)
        except Exception as e:
            self.load_error.emit(str(e))


class BatchProcessThread(QThread):
    """批量处理线程"""
    
    # 信号定义
    progress_updated = pyqtSignal(int, int)  # 当前进度, 总数
    file_processed = pyqtSignal(str, bool, str)  # 文件名, 成功/失败, 消息
    finished = pyqtSignal(bool, str)  # 是否成功, 消息
    log_message = pyqtSignal(str)  # 日志消息
    
    def __init__(self, files: List[str], voice_id: str, output_format: str = "wav", api_key: str = None):
        super().__init__()
        self.files = files
        self.voice_id = voice_id
        self.output_format = output_format
        self.is_cancelled = False
        
        # 初始化处理器
        self.audio_generator = AudioGenerator(api_key=api_key)
        self.file_processor = FileProcessor()
    
    def run(self):
        """运行批量处理"""
        try:
            total_files = len(self.files)
            success_count = 0
            failed_count = 0
            
            self.log_message.emit(f"开始批量处理 {total_files} 个文件")
            
            for i, file_path in enumerate(self.files):
                if self.is_cancelled:
                    self.log_message.emit("用户取消了批量处理")
                    break
                
                try:
                    # 更新进度
                    self.progress_updated.emit(i, total_files)
                    
                    # 读取文本文件
                    text_content = self.file_processor.read_text_file(file_path)
                    if not text_content.strip():
                        self.file_processed.emit(
                            os.path.basename(file_path), 
                            False, 
                            "文件内容为空"
                        )
                        failed_count += 1
                        continue
                    
                    self.log_message.emit(f"正在处理: {os.path.basename(file_path)}")
                    
                    # 生成音频
                    audio_data = self.audio_generator.generate_audio(text_content, self.voice_id)
                    
                    # 保存音频文件
                    output_path = self.file_processor.get_output_path(file_path, self.output_format)
                    self.file_processor.save_audio(audio_data, output_path)
                    
                    self.file_processed.emit(
                        os.path.basename(file_path), 
                        True, 
                        f"已保存到: {os.path.basename(output_path)}"
                    )
                    success_count += 1
                    
                except Exception as e:
                    logger.exception(f"处理文件失败 {file_path}: {e}")
                    self.file_processed.emit(
                        os.path.basename(file_path), 
                        False, 
                        f"处理失败: {str(e)}"
                    )
                    failed_count += 1
            
            # 更新最终进度
            self.progress_updated.emit(total_files, total_files)
            
            # 发送完成信号
            if self.is_cancelled:
                self.finished.emit(False, "处理已取消")
            elif failed_count == 0:
                self.finished.emit(True, f"全部 {success_count} 个文件处理成功")
            else:
                self.finished.emit(
                    success_count > 0, 
                    f"处理完成: 成功 {success_count} 个，失败 {failed_count} 个"
                )
                
        except Exception as e:
            logger.exception(f"批量处理异常: {e}")
            self.finished.emit(False, f"处理异常: {str(e)}")
    
    def cancel(self):
        """取消处理"""
        self.is_cancelled = True


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.settings = QSettings()
        
        # 初始化组件（优先获取API密钥）
        api_key = self.config_manager.get_api_key()
        self.audio_generator = AudioGenerator(api_key=api_key if api_key else None)
        self.file_processor = FileProcessor()
        
        # 界面状态
        self.current_folder = ""
        self.text_files = []
        self.batch_thread = None
        self.progress_dialog = None
        self.all_voices = []  # 存储所有音色数据
        
        # 初始化界面
        self.init_ui()
        self.load_settings()
        self.refresh_voices()
        
        # 检查API密钥设置
        self.check_api_key_setup()
        
        # 加载已保存的API密钥
        self.load_saved_api_key()
        
        logger.info("主窗口初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Fish Audio 批量音频生成工具 v1.0.0")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割器比例
        splitter.setSizes([400, 800])
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建菜单栏
        self.create_menu_bar()
    
    def create_left_panel(self) -> QWidget:
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # API密钥设置组
        api_group = QGroupBox("API 密钥设置")
        api_layout = QVBoxLayout(api_group)
        
        api_layout.addWidget(QLabel("Fish Audio API 密钥:"))
        
        api_input_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("请输入您的 Fish Audio API 密钥")
        self.api_key_edit.textChanged.connect(self.on_api_key_changed)
        api_input_layout.addWidget(self.api_key_edit)
        
        self.show_api_key_btn = QPushButton("👁")
        self.show_api_key_btn.setCheckable(True)
        self.show_api_key_btn.setMaximumWidth(30)
        self.show_api_key_btn.setToolTip("显示/隐藏API密钥")
        self.show_api_key_btn.clicked.connect(self.toggle_api_key_visibility)
        api_input_layout.addWidget(self.show_api_key_btn)
        
        self.save_api_key_btn = QPushButton("保存")
        self.save_api_key_btn.setMaximumWidth(60)
        self.save_api_key_btn.clicked.connect(self.save_api_key)
        api_input_layout.addWidget(self.save_api_key_btn)
        
        self.test_api_key_btn = QPushButton("测试")
        self.test_api_key_btn.setMaximumWidth(60)
        self.test_api_key_btn.clicked.connect(self.test_api_key)
        api_input_layout.addWidget(self.test_api_key_btn)
        
        api_layout.addLayout(api_input_layout)
        
        # API状态显示
        self.api_status_label = QLabel("未设置API密钥")
        self.api_status_label.setStyleSheet("color: orange; font-weight: bold;")
        api_layout.addWidget(self.api_status_label)
        
        layout.addWidget(api_group)
        
        # 文件夹选择组
        folder_group = QGroupBox("文件夹选择")
        folder_layout = QVBoxLayout(folder_group)
        
        self.folder_label = QLabel("未选择文件夹")
        self.folder_label.setWordWrap(True)
        self.folder_label.setStyleSheet("QLabel { color: #666; }")
        folder_layout.addWidget(self.folder_label)
        
        self.select_folder_btn = QPushButton("选择文件夹")
        self.select_folder_btn.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.select_folder_btn)
        
        self.refresh_btn = QPushButton("刷新文件列表")
        self.refresh_btn.clicked.connect(self.refresh_file_list)
        self.refresh_btn.setEnabled(False)
        folder_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(folder_group)
        
        # 音色选择组
        voice_group = QGroupBox("音色选择")
        voice_layout = QVBoxLayout(voice_group)
        
        voice_layout.addWidget(QLabel("选择音色:"))
        
        self.voice_combo = QComboBox()
        self.voice_combo.setMinimumHeight(30)
        voice_layout.addWidget(self.voice_combo)
        
        # 音色类型选择
        voice_type_layout = QHBoxLayout()
        voice_type_layout.addWidget(QLabel("显示类型:"))
        
        self.voice_type_combo = QComboBox()
        self.voice_type_combo.addItems(["所有模型", "个人模型", "热门公共模型"])
        self.voice_type_combo.currentTextChanged.connect(self.filter_voices)
        voice_type_layout.addWidget(self.voice_type_combo)
        
        voice_layout.addLayout(voice_type_layout)
        
        self.refresh_voices_btn = QPushButton("刷新音色列表")
        self.refresh_voices_btn.clicked.connect(self.refresh_voices)
        voice_layout.addWidget(self.refresh_voices_btn)
        
        layout.addWidget(voice_group)
        
        # 输出设置组
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)
        
        output_layout.addWidget(QLabel("音频格式:"))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["wav", "mp3", "m4a"])
        output_layout.addWidget(self.format_combo)
        
        layout.addWidget(output_group)
        
        # 操作按钮组
        action_group = QGroupBox("操作")
        action_layout = QVBoxLayout(action_group)
        
        self.start_btn = QPushButton("开始生成")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.clicked.connect(self.start_batch_processing)
        self.start_btn.setEnabled(False)
        action_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止生成")
        self.stop_btn.setMinimumHeight(30)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_batch_processing)
        self.stop_btn.setEnabled(False)
        action_layout.addWidget(self.stop_btn)
        
        layout.addWidget(action_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """创建右侧信息面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 文件列表组
        file_group = QGroupBox("文本文件列表")
        file_layout = QVBoxLayout(file_group)
        
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        file_layout.addWidget(self.file_list)
        
        file_info_layout = QHBoxLayout()
        self.file_count_label = QLabel("文件数量: 0")
        file_info_layout.addWidget(self.file_count_label)
        file_info_layout.addStretch()
        file_layout.addLayout(file_info_layout)
        
        layout.addWidget(file_group, 1)
        
        # 处理进度组
        progress_group = QGroupBox("处理进度")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # 日志输出组
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        self.log_text.setReadOnly(True)
        # 使用系统等宽字体
        font = QFont()
        font.setFamily("monospace")
        font.setPointSize(9)
        self.log_text.setFont(font)
        log_layout.addWidget(self.log_text)
        
        log_controls = QHBoxLayout()
        self.clear_log_btn = QPushButton("清空日志")
        self.clear_log_btn.clicked.connect(self.clear_log)
        log_controls.addWidget(self.clear_log_btn)
        log_controls.addStretch()
        log_layout.addLayout(log_controls)
        
        layout.addWidget(log_group)
        
        return panel
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        select_folder_action = QAction('选择文件夹(&O)', self)
        select_folder_action.setShortcut('Ctrl+O')
        select_folder_action.triggered.connect(self.select_folder)
        file_menu.addAction(select_folder_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu('工具(&T)')
        
        refresh_voices_action = QAction('刷新音色列表(&R)', self)
        refresh_voices_action.triggered.connect(self.refresh_voices)
        tools_menu.addAction(refresh_voices_action)
        
        settings_action = QAction('设置(&S)', self)
        settings_action.triggered.connect(self.open_settings)
        tools_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def select_folder(self):
        """选择文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "选择包含文本文件的文件夹",
            self.current_folder or os.path.expanduser("~")
        )
        
        if folder:
            self.current_folder = folder
            self.folder_label.setText(f"已选择: {folder}")
            self.refresh_file_list()
            self.add_log(f"选择文件夹: {folder}")
    
    def refresh_file_list(self):
        """刷新文件列表"""
        if not self.current_folder:
            return
        
        try:
            self.text_files = self.file_processor.scan_text_files(self.current_folder)
            
            # 更新文件列表显示
            self.file_list.clear()
            for file_path in self.text_files:
                item = QListWidgetItem(os.path.basename(file_path))
                item.setToolTip(file_path)
                self.file_list.addItem(item)
            
            # 更新文件数量
            count = len(self.text_files)
            self.file_count_label.setText(f"文件数量: {count}")
            
            # 更新按钮状态
            self.refresh_btn.setEnabled(True)
            self.start_btn.setEnabled(count > 0 and self.voice_combo.count() > 0)
            
            self.add_log(f"找到 {count} 个文本文件")
            self.status_bar.showMessage(f"找到 {count} 个文本文件")
            
        except Exception as e:
            logger.exception(f"刷新文件列表失败: {e}")
            QMessageBox.warning(self, "错误", f"刷新文件列表失败:\n{str(e)}")
    
    def refresh_voices(self):
        """刷新音色列表（异步方式避免阻塞UI）"""
        try:
            self.add_log("正在获取音色列表...")
            self.status_bar.showMessage("正在获取音色列表...")
            
            # 使用线程进行音色加载，避免阻塞UI
            self.voice_load_thread = VoiceLoadThread(self.audio_generator)
            self.voice_load_thread.voices_loaded.connect(self.on_voices_loaded)
            self.voice_load_thread.load_error.connect(self.on_voices_load_error)
            self.voice_load_thread.start()
            
        except Exception as e:
            logger.exception(f"启动音色加载失败: {e}")
            self.add_log(f"启动音色加载失败: {str(e)}")
    
    def on_voices_loaded(self, voices):
        """音色加载完成的回调"""
        try:
            self.all_voices = voices  # 保存所有音色数据
            
            self.add_log(f"获取到 {len(voices)} 个音色模型")
            self.status_bar.showMessage(f"获取到 {len(voices)} 个音色模型")
            
            # 应用当前的过滤器
            self.filter_voices()
            
        except Exception as e:
            logger.exception(f"处理音色列表失败: {e}")
            self.add_log(f"处理音色列表失败: {str(e)}")
    
    def on_voices_load_error(self, error_message):
        """音色加载失败的回调"""
        logger.error(f"获取音色列表失败: {error_message}")
        self.add_log(f"获取音色列表失败: {error_message}")
        self.status_bar.showMessage("获取音色列表失败")
        QMessageBox.warning(self, "错误", f"获取音色列表失败:\n{error_message}")
    
    def filter_voices(self):
        """根据选择的类型过滤音色列表"""
        try:
            if not self.all_voices:
                return
            
            filter_type = self.voice_type_combo.currentText()
            filtered_voices = []
            
            if filter_type == "个人模型":
                # 筛选个人模型
                filtered_voices = [v for v in self.all_voices 
                                 if v.get('visibility') == 'private']
                self.add_log(f"显示 {len(filtered_voices)} 个个人模型")
                
            elif filter_type == "热门公共模型":
                # 筛选热门公共模型（前50个）
                public_voices = [v for v in self.all_voices 
                               if v.get('visibility') == 'public']
                public_voices.sort(key=lambda x: x.get('like_count', 0), reverse=True)
                filtered_voices = public_voices[:50]
                self.add_log(f"显示前 {len(filtered_voices)} 个热门公共模型")
                
            else:  # "所有模型"
                filtered_voices = self.all_voices
                self.add_log(f"显示所有 {len(filtered_voices)} 个模型")
            
            # 更新下拉框
            self.voice_combo.clear()
            for voice in filtered_voices:
                # 构建显示文本，包含更多信息
                display_text = voice['name']
                if voice.get('like_count', 0) > 0:
                    display_text += f" (👍{voice['like_count']})"
                
                self.voice_combo.addItem(display_text, voice['id'])
            
            # 更新开始按钮状态
            self.start_btn.setEnabled(
                len(self.text_files) > 0 and self.voice_combo.count() > 0
            )
            
            self.status_bar.showMessage(f"当前显示 {len(filtered_voices)} 个音色模型")
            
        except Exception as e:
            logger.exception(f"过滤音色列表失败: {e}")
            self.add_log(f"过滤音色列表失败: {str(e)}")
    
    def start_batch_processing(self):
        """开始批量处理"""
        if not self.text_files:
            QMessageBox.warning(self, "警告", "请先选择包含文本文件的文件夹")
            return
        
        if self.voice_combo.count() == 0:
            QMessageBox.warning(self, "警告", "请先选择音色")
            return
        
        # 获取选中的音色ID
        voice_id = self.voice_combo.currentData()
        if not voice_id:
            QMessageBox.warning(self, "警告", "请选择有效的音色")
            return
        
        # 获取输出格式
        output_format = self.format_combo.currentText()
        
        # 确认对话框
        reply = QMessageBox.question(
            self,
            "确认",
            f"即将处理 {len(self.text_files)} 个文件\n"
            f"音色: {self.voice_combo.currentText()}\n"
            f"格式: {output_format}\n\n"
            f"是否继续？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # 创建并启动处理线程
        self.batch_thread = BatchProcessThread(self.text_files, voice_id, output_format, self.config_manager.get_api_key())
        self.batch_thread.progress_updated.connect(self.on_progress_updated)
        self.batch_thread.file_processed.connect(self.on_file_processed)
        self.batch_thread.finished.connect(self.on_batch_finished)
        self.batch_thread.log_message.connect(self.add_log)
        
        self.batch_thread.start()
        
        # 更新界面状态
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.text_files))
        
        self.add_log("开始批量处理...")
        self.status_bar.showMessage("正在处理...")
    
    def stop_batch_processing(self):
        """停止批量处理"""
        if self.batch_thread and self.batch_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认",
                "确定要停止当前的处理任务吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.batch_thread.cancel()
                self.add_log("正在停止处理...")
    
    def on_progress_updated(self, current: int, total: int):
        """处理进度更新"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"进度: {current}/{total}")
        self.status_bar.showMessage(f"正在处理... ({current}/{total})")
    
    def on_file_processed(self, filename: str, success: bool, message: str):
        """单个文件处理完成"""
        status = "✓" if success else "✗"
        self.add_log(f"{status} {filename}: {message}")
    
    def on_batch_finished(self, success: bool, message: str):
        """批量处理完成"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.add_log(f"处理完成: {message}")
        self.status_bar.showMessage(message)
        
        # 显示完成对话框
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "处理完成", message)
        
        self.batch_thread = None
    
    def add_log(self, message: str):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        self.log_text.append(formatted_message)
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        
        # 处理事件以确保界面更新
        QApplication.processEvents()
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
    
    def open_settings(self):
        """打开设置对话框"""
        try:
            settings_dialog = SettingsDialog(self.config_manager, self)
            settings_dialog.settings_updated.connect(self.on_settings_updated)
            
            if settings_dialog.exec_() == QDialog.Accepted:
                self.add_log("设置已更新")
                
        except Exception as e:
            logger.exception(f"打开设置对话框失败: {e}")
            QMessageBox.critical(self, "错误", f"打开设置对话框失败:\n{str(e)}")
    
    def on_settings_updated(self):
        """设置更新后的处理"""
        try:
            # 重新初始化音频生成器（使用新的API密钥）
            api_key = self.config_manager.get_api_key()
            if api_key:
                self.audio_generator.set_api_key(api_key)
                self.add_log("API密钥已更新")
                
                # 刷新音色列表
                self.refresh_voices()
            else:
                self.add_log("未设置API密钥，将使用模拟模式")
                
        except Exception as e:
            logger.exception(f"处理设置更新失败: {e}")
            self.add_log(f"处理设置更新失败: {str(e)}")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            """
            <h3>Fish Audio 批量音频生成工具</h3>
            <p>版本: 1.0.0</p>
            <p>一个基于 PyQt 的桌面应用程序，使用 Fish Audio SDK 批量将文本文件转换为音频文件。</p>
            <p><b>主要功能:</b></p>
            <ul>
            <li>批量处理文本文件</li>
            <li>多种音色选择</li>
            <li>智能文件保存</li>
            <li>实时处理进度</li>
            </ul>
            <p><b>技术栈:</b> Python, PyQt5, Fish Audio SDK</p>
            <p><b>开源许可:</b> MIT License</p>
            """
        )
    
    def load_settings(self):
        """加载设置"""
        # 恢复窗口大小和位置
        self.restoreGeometry(self.settings.value("geometry", b""))
        self.restoreState(self.settings.value("windowState", b""))
        
        # 恢复最后选择的文件夹
        last_folder = self.settings.value("lastFolder", "")
        if last_folder and os.path.exists(last_folder):
            self.current_folder = last_folder
            self.folder_label.setText(f"已选择: {last_folder}")
            QTimer.singleShot(100, self.refresh_file_list)  # 延迟刷新
    
    def save_settings(self):
        """保存设置"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        
        if self.current_folder:
            self.settings.setValue("lastFolder", self.current_folder)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 如果有处理任务在运行，询问是否确认退出
        if self.batch_thread and self.batch_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认退出",
                "有处理任务正在运行，确定要退出吗？",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                event.ignore()
                return
            
            # 停止处理线程
            self.batch_thread.cancel()
            self.batch_thread.wait(3000)  # 等待最多3秒
        
        # 保存设置
        self.save_settings()
        
        logger.info("应用程序正常退出")
        event.accept()
    
    def check_api_key_setup(self):
        """检查API密钥设置"""
        try:
            api_key = self.config_manager.get_api_key()
            if not api_key:
                # 延迟显示提示，确保主窗口已经显示
                QTimer.singleShot(1000, self.show_api_key_setup_prompt)
        except Exception as e:
            logger.error(f"检查API密钥设置失败: {e}")
    
    def show_api_key_setup_prompt(self):
        """显示API密钥设置提示"""
        reply = QMessageBox.question(
            self,
            "API密钥设置",
            "检测到您还未设置 Fish Audio API 密钥。\n\n"
            "没有API密钥将只能使用模拟模式（生成虚拟音频文件）。\n\n"
            "您可以在主界面顶部的API密钥设置区域输入密钥。\n\n"
            "是否现在打开设置界面？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.open_settings()
        else:
            self.add_log("未设置API密钥，将使用模拟模式")
    
    def load_saved_api_key(self):
        """加载已保存的API密钥"""
        try:
            api_key = self.config_manager.get_api_key()
            if api_key:
                self.api_key_edit.setText(api_key)
                # API密钥已在初始化时设置，这里只需要更新UI状态
                self.update_api_status(True, "API密钥已加载")
                self.add_log("已加载保存的API密钥")
                # 自动刷新音色列表
                self.refresh_voices()
            else:
                self.update_api_status(False, "未设置API密钥")
        except Exception as e:
            logger.error(f"加载API密钥失败: {e}")
            self.update_api_status(False, "加载失败")
    
    def on_api_key_changed(self):
        """API密钥输入变化时的处理"""
        api_key = self.api_key_edit.text().strip()
        if api_key:
            self.update_api_status(None, "已输入密钥，请点击保存")
        else:
            self.update_api_status(False, "未设置API密钥")
    
    def toggle_api_key_visibility(self):
        """切换API密钥显示/隐藏"""
        if self.show_api_key_btn.isChecked():
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.show_api_key_btn.setText("🙈")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.show_api_key_btn.setText("👁")
    
    def save_api_key(self):
        """保存API密钥"""
        try:
            api_key = self.api_key_edit.text().strip()
            if not api_key:
                QMessageBox.warning(self, "警告", "请先输入API密钥")
                return
            
            # 保存到配置
            self.config_manager.set_api_key(api_key)
            
            # 更新音频生成器
            self.audio_generator.set_api_key(api_key)
            
            self.update_api_status(True, "API密钥已保存")
            self.add_log("API密钥已保存并更新")
            
            # 刷新音色列表
            self.refresh_voices()
            
        except Exception as e:
            logger.error(f"保存API密钥失败: {e}")
            QMessageBox.critical(self, "错误", f"保存API密钥失败:\n{str(e)}")
            self.update_api_status(False, "保存失败")
    
    def test_api_key(self):
        """测试API密钥（异步方式避免阻塞UI）"""
        try:
            api_key = self.api_key_edit.text().strip()
            if not api_key:
                QMessageBox.warning(self, "警告", "请先输入API密钥")
                return
            
            self.add_log("正在测试API连接...")
            self.update_api_status(None, "测试中...")
            
            # 禁用测试按钮防止重复点击
            self.test_api_key_btn.setEnabled(False)
            
            # 使用线程进行API测试，避免阻塞UI
            self.api_test_thread = ApiTestThread(api_key)
            self.api_test_thread.test_completed.connect(self.on_api_test_completed)
            self.api_test_thread.start()
                
        except Exception as e:
            logger.error(f"启动API连接测试失败: {e}")
            self.update_api_status(False, "测试失败")
            self.add_log(f"API连接测试失败: {str(e)}")
            self.test_api_key_btn.setEnabled(True)
    
    def on_api_test_completed(self, success, message):
        """API测试完成的回调"""
        try:
            if success:
                self.update_api_status(True, "连接成功")
                self.add_log("API连接测试成功！")
                QMessageBox.information(self, "成功", "API连接测试成功！")
                # 测试成功后自动刷新音色列表
                self.refresh_voices()
            else:
                self.update_api_status(False, "连接失败")
                self.add_log(f"API连接测试失败: {message}")
                QMessageBox.warning(self, "失败", f"API连接测试失败:\n{message}")
            
        except Exception as e:
            logger.error(f"处理API测试结果失败: {e}")
        finally:
            # 重新启用测试按钮
            self.test_api_key_btn.setEnabled(True)
    
    def update_api_status(self, status, message):
        """更新API状态显示
        
        Args:
            status: True(成功), False(失败), None(处理中)
            message: 状态消息
        """
        if status is True:
            self.api_status_label.setStyleSheet("color: green; font-weight: bold;")
        elif status is False:
            self.api_status_label.setStyleSheet("color: red; font-weight: bold;")
        else:  # None - 处理中
            self.api_status_label.setStyleSheet("color: blue; font-weight: bold;")
        
        self.api_status_label.setText(message) 