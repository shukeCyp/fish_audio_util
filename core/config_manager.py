#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器模块

管理应用程序的配置信息，包括API密钥、用户设置等
"""

import os
import json
import configparser
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger


class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_file: str = "config.ini"):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # 默认配置
        self.default_config = {
            'api': {
                'fish_audio_api_key': '',
                'api_timeout': '30',
                'max_retries': '3'
            },
            'audio': {
                'default_format': 'wav',
                'default_voice': '',
                'sample_rate': '44100',
                'bit_depth': '16'
            },
            'ui': {
                'window_width': '1200',
                'window_height': '800',
                'theme': 'default',
                'language': 'zh_CN'
            },
            'processing': {
                'max_concurrent': '4',
                'chunk_size': '1000',
                'auto_save': 'true'
            },
            'paths': {
                'last_input_folder': '',
                'default_output_folder': '',
                'temp_folder': 'temp'
            }
        }
        
        self.load_config()
        logger.info("配置管理器初始化完成")
    
    def load_config(self):
        """加载配置文件"""
        try:
            # 如果配置文件存在，则加载
            if os.path.exists(self.config_file):
                self.config.read(self.config_file, encoding='utf-8')
                logger.info(f"配置文件加载成功: {self.config_file}")
            else:
                logger.info("配置文件不存在，使用默认配置")
            
            # 确保所有默认配置项都存在
            self._ensure_default_config()
            
            # 从环境变量加载敏感配置
            self._load_from_env()
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.info("使用默认配置")
            self._create_default_config()
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                self.config.write(f)
            logger.info(f"配置文件保存成功: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise
    
    def _ensure_default_config(self):
        """确保所有默认配置项都存在"""
        for section_name, section_config in self.default_config.items():
            if not self.config.has_section(section_name):
                self.config.add_section(section_name)
            
            for key, default_value in section_config.items():
                if not self.config.has_option(section_name, key):
                    self.config.set(section_name, key, default_value)
    
    def _create_default_config(self):
        """创建默认配置"""
        self.config.clear()
        for section_name, section_config in self.default_config.items():
            self.config.add_section(section_name)
            for key, value in section_config.items():
                self.config.set(section_name, key, value)
    
    def _load_from_env(self):
        """从环境变量加载配置"""
        # API 密钥
        api_key = os.getenv('FISH_AUDIO_API_KEY')
        if api_key:
            self.config.set('api', 'fish_audio_api_key', api_key)
            logger.info("从环境变量加载 API 密钥")
        
        # 其他环境变量
        env_mappings = {
            'FISH_AUDIO_TIMEOUT': ('api', 'api_timeout'),
            'FISH_AUDIO_MAX_RETRIES': ('api', 'max_retries'),
            'FISH_AUDIO_DEFAULT_FORMAT': ('audio', 'default_format'),
            'FISH_AUDIO_TEMP_FOLDER': ('paths', 'temp_folder'),
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                self.config.set(section, key, value)
                logger.debug(f"从环境变量加载: {env_var} -> {section}.{key}")
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """
        获取配置值
        
        Args:
            section: 配置节
            key: 配置键
            fallback: 默认值
            
        Returns:
            配置值
        """
        try:
            return self.config.get(section, key, fallback=fallback)
        except Exception as e:
            logger.warning(f"获取配置失败 {section}.{key}: {e}")
            return fallback
    
    def getint(self, section: str, key: str, fallback: int = 0) -> int:
        """
        获取整数配置值
        
        Args:
            section: 配置节
            key: 配置键
            fallback: 默认值
            
        Returns:
            整数配置值
        """
        try:
            return self.config.getint(section, key, fallback=fallback)
        except Exception as e:
            logger.warning(f"获取整数配置失败 {section}.{key}: {e}")
            return fallback
    
    def getboolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """
        获取布尔配置值
        
        Args:
            section: 配置节
            key: 配置键
            fallback: 默认值
            
        Returns:
            布尔配置值
        """
        try:
            return self.config.getboolean(section, key, fallback=fallback)
        except Exception as e:
            logger.warning(f"获取布尔配置失败 {section}.{key}: {e}")
            return fallback
    
    def set(self, section: str, key: str, value: Any):
        """
        设置配置值
        
        Args:
            section: 配置节
            key: 配置键
            value: 配置值
        """
        try:
            if not self.config.has_section(section):
                self.config.add_section(section)
            
            self.config.set(section, key, str(value))
            logger.debug(f"设置配置: {section}.{key} = {value}")
        except Exception as e:
            logger.error(f"设置配置失败 {section}.{key}: {e}")
            raise
    
    def get_api_key(self) -> Optional[str]:
        """获取 Fish Audio API 密钥"""
        api_key = self.get('api', 'fish_audio_api_key')
        if not api_key:
            # 尝试从环境变量获取
            api_key = os.getenv('FISH_AUDIO_API_KEY')
        return api_key if api_key else None
    
    def set_api_key(self, api_key: str):
        """设置 Fish Audio API 密钥"""
        self.set('api', 'fish_audio_api_key', api_key)
        self.save_config()
        logger.info("API 密钥已更新")
    
    def get_audio_config(self) -> Dict[str, Any]:
        """获取音频配置"""
        return {
            'default_format': self.get('audio', 'default_format', 'wav'),
            'default_voice': self.get('audio', 'default_voice', ''),
            'sample_rate': self.getint('audio', 'sample_rate', 44100),
            'bit_depth': self.getint('audio', 'bit_depth', 16)
        }
    
    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return {
            'window_width': self.getint('ui', 'window_width', 1200),
            'window_height': self.getint('ui', 'window_height', 800),
            'theme': self.get('ui', 'theme', 'default'),
            'language': self.get('ui', 'language', 'zh_CN')
        }
    
    def get_processing_config(self) -> Dict[str, Any]:
        """获取处理配置"""
        return {
            'max_concurrent': self.getint('processing', 'max_concurrent', 4),
            'chunk_size': self.getint('processing', 'chunk_size', 1000),
            'auto_save': self.getboolean('processing', 'auto_save', True)
        }
    
    def get_paths_config(self) -> Dict[str, str]:
        """获取路径配置"""
        return {
            'last_input_folder': self.get('paths', 'last_input_folder', ''),
            'default_output_folder': self.get('paths', 'default_output_folder', ''),
            'temp_folder': self.get('paths', 'temp_folder', 'temp')
        }
    
    def update_last_input_folder(self, folder_path: str):
        """更新最后使用的输入文件夹"""
        self.set('paths', 'last_input_folder', folder_path)
        self.save_config()
    
    def update_ui_config(self, width: int, height: int, theme: str = None):
        """更新UI配置"""
        self.set('ui', 'window_width', width)
        self.set('ui', 'window_height', height)
        if theme:
            self.set('ui', 'theme', theme)
        self.save_config()
    
    def reset_to_default(self):
        """重置为默认配置"""
        logger.info("重置配置为默认值")
        self._create_default_config()
        self._load_from_env()
        self.save_config()
    
    def export_config(self, export_path: str):
        """
        导出配置到JSON文件
        
        Args:
            export_path: 导出文件路径
        """
        try:
            config_dict = {}
            for section_name in self.config.sections():
                config_dict[section_name] = dict(self.config.items(section_name))
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置导出成功: {export_path}")
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            raise
    
    def import_config(self, import_path: str):
        """
        从JSON文件导入配置
        
        Args:
            import_path: 导入文件路径
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # 清空现有配置
            self.config.clear()
            
            # 导入配置
            for section_name, section_config in config_dict.items():
                self.config.add_section(section_name)
                for key, value in section_config.items():
                    self.config.set(section_name, key, str(value))
            
            # 确保默认配置项存在
            self._ensure_default_config()
            
            # 保存配置
            self.save_config()
            
            logger.info(f"配置导入成功: {import_path}")
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            raise
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置的有效性
        
        Returns:
            验证结果字典
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # 检查API密钥
        api_key = self.get_api_key()
        if not api_key:
            results['warnings'].append("未设置 Fish Audio API 密钥")
        
        # 检查路径配置
        paths_config = self.get_paths_config()
        temp_folder = paths_config['temp_folder']
        if temp_folder and not os.path.exists(temp_folder):
            try:
                os.makedirs(temp_folder, exist_ok=True)
            except Exception as e:
                results['errors'].append(f"无法创建临时文件夹: {e}")
                results['is_valid'] = False
        
        # 检查处理配置
        processing_config = self.get_processing_config()
        max_concurrent = processing_config['max_concurrent']
        if max_concurrent < 1 or max_concurrent > 16:
            results['warnings'].append("并发数量建议设置在1-16之间")
        
        logger.info(f"配置验证完成: {'通过' if results['is_valid'] else '失败'}")
        return results
    
    def get_all_config(self) -> Dict[str, Dict[str, str]]:
        """获取所有配置"""
        config_dict = {}
        for section_name in self.config.sections():
            config_dict[section_name] = dict(self.config.items(section_name))
        return config_dict 