#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
设置对话框组件

提供用户设置界面，包括API密钥配置等
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QTabWidget, QWidget,
    QGroupBox, QSpinBox, QComboBox, QCheckBox, QMessageBox,
    QTextEdit, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from loguru import logger

from core.config_manager import ConfigManager


class SettingsDialog(QDialog):
    """设置对话框类"""
    
    # 信号：设置已更新
    settings_updated = pyqtSignal()
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setWindowTitle("设置")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        
        self.init_ui()
        self.load_current_settings()
        
        logger.info("设置对话框初始化完成")
    
    def init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # API设置标签页
        self.create_api_tab()
        
        # 音频设置标签页
        self.create_audio_tab()
        
        # 界面设置标签页
        self.create_ui_tab()
        
        # 处理设置标签页
        self.create_processing_tab()
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 测试连接按钮
        self.test_connection_btn = QPushButton("测试连接")
        self.test_connection_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_connection_btn)
        
        # 重置按钮
        self.reset_btn = QPushButton("恢复默认")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        # 确定按钮
        self.ok_btn = QPushButton("确定")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self.accept_settings)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def create_api_tab(self):
        """创建API设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # API配置组
        api_group = QGroupBox("Fish Audio API 配置")
        api_layout = QFormLayout(api_group)
        
        # API密钥输入
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("请输入您的 Fish Audio API 密钥")
        api_layout.addRow("API 密钥:", self.api_key_edit)
        
        # 显示/隐藏密钥按钮
        show_key_layout = QHBoxLayout()
        self.show_key_btn = QPushButton("显示密钥")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self.toggle_api_key_visibility)
        show_key_layout.addWidget(self.show_key_btn)
        show_key_layout.addStretch()
        api_layout.addRow("", show_key_layout)
        
        # API超时设置
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setSuffix(" 秒")
        self.timeout_spin.setValue(30)
        api_layout.addRow("请求超时:", self.timeout_spin)
        
        # 最大重试次数
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(0, 10)
        self.max_retries_spin.setValue(3)
        api_layout.addRow("最大重试次数:", self.max_retries_spin)
        
        layout.addWidget(api_group)
        
        # 帮助信息
        help_group = QGroupBox("获取API密钥")
        help_layout = QVBoxLayout(help_group)
        
        help_text = QTextEdit()
        help_text.setMaximumHeight(100)
        help_text.setReadOnly(True)
        help_text.setPlainText(
            "1. 访问 Fish Audio 官网 (https://fish.audio/)\n"
            "2. 注册账号并登录\n"
            "3. 在用户中心获取API密钥\n"
            "4. 将API密钥粘贴到上方输入框中"
        )
        help_layout.addWidget(help_text)
        
        layout.addWidget(help_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "API 设置")
    
    def create_audio_tab(self):
        """创建音频设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 音频格式组
        format_group = QGroupBox("音频格式设置")
        format_layout = QFormLayout(format_group)
        
        # 默认音频格式
        self.format_combo = QComboBox()
        self.format_combo.addItems(["wav", "mp3", "m4a"])
        format_layout.addRow("默认格式:", self.format_combo)
        
        # 采样率
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(["22050", "44100", "48000"])
        self.sample_rate_combo.setCurrentText("44100")
        format_layout.addRow("采样率:", self.sample_rate_combo)
        
        # 位深度
        self.bit_depth_combo = QComboBox()
        self.bit_depth_combo.addItems(["16", "24", "32"])
        self.bit_depth_combo.setCurrentText("16")
        format_layout.addRow("位深度:", self.bit_depth_combo)
        
        layout.addWidget(format_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "音频设置")
    
    def create_ui_tab(self):
        """创建界面设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 界面设置组
        ui_group = QGroupBox("界面设置")
        ui_layout = QFormLayout(ui_group)
        
        # 主题选择
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["默认", "暗色"])
        ui_layout.addRow("主题:", self.theme_combo)
        
        # 语言选择
        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        ui_layout.addRow("语言:", self.language_combo)
        
        # 窗口大小设置
        window_layout = QHBoxLayout()
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 2000)
        self.window_width_spin.setValue(1200)
        window_layout.addWidget(self.window_width_spin)
        
        window_layout.addWidget(QLabel("×"))
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 1500)
        self.window_height_spin.setValue(800)
        window_layout.addWidget(self.window_height_spin)
        
        ui_layout.addRow("默认窗口大小:", window_layout)
        
        layout.addWidget(ui_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "界面设置")
    
    def create_processing_tab(self):
        """创建处理设置标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 处理设置组
        processing_group = QGroupBox("处理设置")
        processing_layout = QFormLayout(processing_group)
        
        # 最大并发数
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 16)
        self.max_concurrent_spin.setValue(4)
        processing_layout.addRow("最大并发数:", self.max_concurrent_spin)
        
        # 文本块大小
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(100, 5000)
        self.chunk_size_spin.setValue(1000)
        processing_layout.addRow("文本块大小:", self.chunk_size_spin)
        
        # 自动保存
        self.auto_save_check = QCheckBox("启用自动保存")
        self.auto_save_check.setChecked(True)
        processing_layout.addRow("", self.auto_save_check)
        
        layout.addWidget(processing_group)
        
        # 路径设置组
        paths_group = QGroupBox("路径设置")
        paths_layout = QFormLayout(paths_group)
        
        # 默认输出文件夹
        output_layout = QHBoxLayout()
        self.output_folder_edit = QLineEdit()
        self.output_folder_edit.setPlaceholderText("默认与输入文件同级")
        output_layout.addWidget(self.output_folder_edit)
        
        self.browse_output_btn = QPushButton("浏览")
        self.browse_output_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(self.browse_output_btn)
        
        paths_layout.addRow("默认输出文件夹:", output_layout)
        
        # 临时文件夹
        temp_layout = QHBoxLayout()
        self.temp_folder_edit = QLineEdit()
        self.temp_folder_edit.setText("temp")
        temp_layout.addWidget(self.temp_folder_edit)
        
        self.browse_temp_btn = QPushButton("浏览")
        self.browse_temp_btn.clicked.connect(self.browse_temp_folder)
        temp_layout.addWidget(self.browse_temp_btn)
        
        paths_layout.addRow("临时文件夹:", temp_layout)
        
        layout.addWidget(paths_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "处理设置")
    
    def toggle_api_key_visibility(self):
        """切换API密钥显示/隐藏"""
        if self.show_key_btn.isChecked():
            self.api_key_edit.setEchoMode(QLineEdit.Normal)
            self.show_key_btn.setText("隐藏密钥")
        else:
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.show_key_btn.setText("显示密钥")
    
    def browse_output_folder(self):
        """浏览输出文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择默认输出文件夹", self.output_folder_edit.text()
        )
        if folder:
            self.output_folder_edit.setText(folder)
    
    def browse_temp_folder(self):
        """浏览临时文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择临时文件夹", self.temp_folder_edit.text()
        )
        if folder:
            self.temp_folder_edit.setText(folder)
    
    def load_current_settings(self):
        """加载当前设置"""
        try:
            # 加载API设置
            self.api_key_edit.setText(self.config_manager.get_api_key() or "")
            self.timeout_spin.setValue(self.config_manager.getint('api', 'api_timeout', 30))
            self.max_retries_spin.setValue(self.config_manager.getint('api', 'max_retries', 3))
            
            # 加载音频设置
            audio_config = self.config_manager.get_audio_config()
            self.format_combo.setCurrentText(audio_config['default_format'])
            self.sample_rate_combo.setCurrentText(str(audio_config['sample_rate']))
            self.bit_depth_combo.setCurrentText(str(audio_config['bit_depth']))
            
            # 加载界面设置
            ui_config = self.config_manager.get_ui_config()
            self.theme_combo.setCurrentIndex(0 if ui_config['theme'] == 'default' else 1)
            self.language_combo.setCurrentIndex(0 if ui_config['language'] == 'zh_CN' else 1)
            self.window_width_spin.setValue(ui_config['window_width'])
            self.window_height_spin.setValue(ui_config['window_height'])
            
            # 加载处理设置
            processing_config = self.config_manager.get_processing_config()
            self.max_concurrent_spin.setValue(processing_config['max_concurrent'])
            self.chunk_size_spin.setValue(processing_config['chunk_size'])
            self.auto_save_check.setChecked(processing_config['auto_save'])
            
            # 加载路径设置
            paths_config = self.config_manager.get_paths_config()
            self.output_folder_edit.setText(paths_config['default_output_folder'])
            self.temp_folder_edit.setText(paths_config['temp_folder'])
            
            logger.info("设置加载完成")
            
        except Exception as e:
            logger.error(f"加载设置失败: {e}")
            QMessageBox.warning(self, "错误", f"加载设置失败:\n{str(e)}")
    
    def save_settings(self):
        """保存设置"""
        try:
            # 保存API设置
            api_key = self.api_key_edit.text().strip()
            if api_key:
                self.config_manager.set_api_key(api_key)
            self.config_manager.set('api', 'api_timeout', self.timeout_spin.value())
            self.config_manager.set('api', 'max_retries', self.max_retries_spin.value())
            
            # 保存音频设置
            self.config_manager.set('audio', 'default_format', self.format_combo.currentText())
            self.config_manager.set('audio', 'sample_rate', self.sample_rate_combo.currentText())
            self.config_manager.set('audio', 'bit_depth', self.bit_depth_combo.currentText())
            
            # 保存界面设置
            theme = 'default' if self.theme_combo.currentIndex() == 0 else 'dark'
            language = 'zh_CN' if self.language_combo.currentIndex() == 0 else 'en_US'
            self.config_manager.set('ui', 'theme', theme)
            self.config_manager.set('ui', 'language', language)
            self.config_manager.set('ui', 'window_width', self.window_width_spin.value())
            self.config_manager.set('ui', 'window_height', self.window_height_spin.value())
            
            # 保存处理设置
            self.config_manager.set('processing', 'max_concurrent', self.max_concurrent_spin.value())
            self.config_manager.set('processing', 'chunk_size', self.chunk_size_spin.value())
            self.config_manager.set('processing', 'auto_save', self.auto_save_check.isChecked())
            
            # 保存路径设置
            self.config_manager.set('paths', 'default_output_folder', self.output_folder_edit.text())
            self.config_manager.set('paths', 'temp_folder', self.temp_folder_edit.text())
            
            # 保存配置文件
            self.config_manager.save_config()
            
            logger.info("设置保存成功")
            return True
            
        except Exception as e:
            logger.error(f"保存设置失败: {e}")
            QMessageBox.critical(self, "错误", f"保存设置失败:\n{str(e)}")
            return False
    
    def test_connection(self):
        """测试API连接"""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "警告", "请先输入API密钥")
            return
        
        try:
            # 临时创建音频生成器测试连接
            from core.audio_generator import AudioGenerator
            temp_generator = AudioGenerator(api_key=api_key)
            
            # 测试连接
            if temp_generator.test_connection():
                QMessageBox.information(self, "成功", "API连接测试成功！")
            else:
                QMessageBox.warning(self, "失败", "API连接测试失败，请检查密钥是否正确")
                
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            QMessageBox.critical(self, "错误", f"连接测试失败:\n{str(e)}")
    
    def reset_to_defaults(self):
        """重置为默认设置"""
        reply = QMessageBox.question(
            self, "确认", "确定要重置所有设置为默认值吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.config_manager.reset_to_default()
                self.load_current_settings()
                QMessageBox.information(self, "成功", "设置已重置为默认值")
            except Exception as e:
                logger.error(f"重置设置失败: {e}")
                QMessageBox.critical(self, "错误", f"重置设置失败:\n{str(e)}")
    
    def accept_settings(self):
        """接受设置"""
        if self.save_settings():
            self.settings_updated.emit()
            self.accept()
    
    def validate_settings(self) -> bool:
        """验证设置的有效性"""
        # 验证API密钥
        api_key = self.api_key_edit.text().strip()
        if api_key and len(api_key) < 10:
            QMessageBox.warning(self, "警告", "API密钥似乎太短，请检查是否正确")
            return False
        
        # 验证文件夹路径
        temp_folder = self.temp_folder_edit.text().strip()
        if temp_folder and not temp_folder.replace('/', '').replace('\\', '').replace('.', '').isalnum():
            QMessageBox.warning(self, "警告", "临时文件夹路径包含无效字符")
            return False
        
        return True
    
    def closeEvent(self, event):
        """关闭事件"""
        # 检查是否有未保存的更改
        # 这里可以添加检查逻辑
        event.accept() 