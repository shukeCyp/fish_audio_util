#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件处理器模块

处理文本文件的读取、音频文件的保存等文件操作
"""

import os
import glob
from typing import List, Optional
from pathlib import Path
from loguru import logger


class FileProcessor:
    """文件处理器类"""
    
    def __init__(self):
        """初始化文件处理器"""
        # 支持的文本文件扩展名
        self.text_extensions = ['.txt', '.md', '.text']
        
        # 支持的音频格式
        self.audio_formats = {
            'wav': 'audio/wav',
            'mp3': 'audio/mpeg',
            'm4a': 'audio/mp4'
        }
        
        logger.info("文件处理器初始化完成")
    
    def scan_text_files(self, folder_path: str) -> List[str]:
        """
        扫描文件夹中的文本文件
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            文本文件路径列表
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"文件夹不存在: {folder_path}")
        
        if not os.path.isdir(folder_path):
            raise ValueError(f"路径不是文件夹: {folder_path}")
        
        text_files = []
        
        try:
            # 遍历所有支持的文本文件扩展名
            for ext in self.text_extensions:
                pattern = os.path.join(folder_path, f"*{ext}")
                files = glob.glob(pattern)
                text_files.extend(files)
            
            # 去重并排序
            text_files = sorted(list(set(text_files)))
            
            logger.info(f"在 {folder_path} 中找到 {len(text_files)} 个文本文件")
            
            # 过滤掉空文件
            valid_files = []
            for file_path in text_files:
                try:
                    if os.path.getsize(file_path) > 0:
                        valid_files.append(file_path)
                    else:
                        logger.warning(f"跳过空文件: {file_path}")
                except OSError as e:
                    logger.warning(f"无法检查文件大小: {file_path}, {e}")
            
            logger.info(f"有效文本文件数量: {len(valid_files)}")
            return valid_files
            
        except Exception as e:
            logger.exception(f"扫描文本文件失败: {e}")
            raise
    
    def read_text_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        读取文本文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码，默认为utf-8
            
        Returns:
            文件内容
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        encodings_to_try = [encoding, 'utf-8', 'gbk', 'gb2312', 'latin1']
        
        for enc in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read().strip()
                
                if content:
                    logger.debug(f"成功读取文件 {file_path} (编码: {enc})")
                    return content
                else:
                    logger.warning(f"文件内容为空: {file_path}")
                    return ""
                    
            except UnicodeDecodeError:
                logger.debug(f"编码 {enc} 读取失败，尝试下一个编码")
                continue
            except Exception as e:
                logger.error(f"读取文件失败 {file_path}: {e}")
                raise
        
        raise ValueError(f"无法使用任何编码读取文件: {file_path}")
    
    def get_output_path(self, input_file_path: str, audio_format: str = 'wav') -> str:
        """
        根据输入文件路径生成输出音频文件路径
        
        Args:
            input_file_path: 输入文本文件路径
            audio_format: 音频格式
            
        Returns:
            输出音频文件路径
        """
        if audio_format not in self.audio_formats:
            raise ValueError(f"不支持的音频格式: {audio_format}")
        
        # 获取文件信息
        file_path = Path(input_file_path)
        file_dir = file_path.parent
        file_stem = file_path.stem  # 不包含扩展名的文件名
        
        # 生成输出文件路径
        output_filename = f"{file_stem}.{audio_format}"
        output_path = file_dir / output_filename
        
        logger.debug(f"输出路径: {input_file_path} -> {output_path}")
        return str(output_path)
    
    def save_audio(self, audio_data: bytes, output_path: str):
        """
        保存音频数据到文件
        
        Args:
            audio_data: 音频数据
            output_path: 输出文件路径
        """
        if not audio_data:
            raise ValueError("音频数据不能为空")
        
        try:
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 写入音频文件
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            # 验证文件是否写入成功
            if not os.path.exists(output_path):
                raise IOError(f"文件保存失败: {output_path}")
            
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise IOError(f"保存的文件为空: {output_path}")
            
            logger.info(f"音频文件保存成功: {output_path} ({file_size} bytes)")
            
        except Exception as e:
            logger.exception(f"保存音频文件失败: {output_path}, {e}")
            raise
    
    def validate_input_file(self, file_path: str) -> bool:
        """
        验证输入文件是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否有效
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在: {file_path}")
                return False
            
            # 检查是否是文件
            if not os.path.isfile(file_path):
                logger.warning(f"路径不是文件: {file_path}")
                return False
            
            # 检查文件扩展名
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.text_extensions:
                logger.warning(f"不支持的文件类型: {file_path}")
                return False
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.warning(f"文件为空: {file_path}")
                return False
            
            # 检查文件是否可读
            content = self.read_text_file(file_path)
            if not content.strip():
                logger.warning(f"文件内容为空: {file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证文件失败: {file_path}, {e}")
            return False
    
    def get_file_info(self, file_path: str) -> dict:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            stat = os.stat(file_path)
            file_path_obj = Path(file_path)
            
            # 读取文件内容以获取文本长度
            try:
                content = self.read_text_file(file_path)
                text_length = len(content)
                char_count = len(content.strip())
            except Exception:
                text_length = 0
                char_count = 0
            
            return {
                'path': file_path,
                'name': file_path_obj.name,
                'stem': file_path_obj.stem,
                'suffix': file_path_obj.suffix,
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'text_length': text_length,
                'char_count': char_count,
                'is_valid': self.validate_input_file(file_path)
            }
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {file_path}, {e}")
            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'error': str(e),
                'is_valid': False
            }
    
    def clean_temp_files(self, temp_dir: str = "temp"):
        """
        清理临时文件
        
        Args:
            temp_dir: 临时文件目录
        """
        try:
            if not os.path.exists(temp_dir):
                return
            
            # 删除临时文件
            temp_files = glob.glob(os.path.join(temp_dir, "*"))
            for temp_file in temp_files:
                try:
                    if os.path.isfile(temp_file):
                        os.remove(temp_file)
                        logger.debug(f"删除临时文件: {temp_file}")
                except Exception as e:
                    logger.warning(f"无法删除临时文件 {temp_file}: {e}")
            
            logger.info(f"临时文件清理完成: {temp_dir}")
            
        except Exception as e:
            logger.error(f"清理临时文件失败: {e}")
    
    def create_backup(self, file_path: str) -> str:
        """
        创建文件备份
        
        Args:
            file_path: 要备份的文件路径
            
        Returns:
            备份文件路径
        """
        try:
            import shutil
            from datetime import datetime
            
            file_path_obj = Path(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path_obj.stem}_backup_{timestamp}{file_path_obj.suffix}"
            backup_path = file_path_obj.parent / backup_name
            
            shutil.copy2(file_path, backup_path)
            logger.info(f"文件备份成功: {file_path} -> {backup_path}")
            
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"创建文件备份失败: {file_path}, {e}")
            raise
    
    def batch_validate_files(self, file_paths: List[str]) -> dict:
        """
        批量验证文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            验证结果字典
        """
        results = {
            'valid_files': [],
            'invalid_files': [],
            'total_count': len(file_paths),
            'valid_count': 0,
            'invalid_count': 0
        }
        
        for file_path in file_paths:
            if self.validate_input_file(file_path):
                results['valid_files'].append(file_path)
                results['valid_count'] += 1
            else:
                results['invalid_files'].append(file_path)
                results['invalid_count'] += 1
        
        logger.info(f"批量验证完成: 总数 {results['total_count']}, "
                   f"有效 {results['valid_count']}, 无效 {results['invalid_count']}")
        
        return results 