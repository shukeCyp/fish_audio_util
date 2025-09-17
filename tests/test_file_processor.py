#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件处理器测试模块
"""

import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.file_processor import FileProcessor


class TestFileProcessor(unittest.TestCase):
    """文件处理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.processor = FileProcessor()
        
        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp()
        
        # 创建测试文件
        self.test_files = {
            'test1.txt': '这是第一个测试文件的内容',
            'test2.txt': '这是第二个测试文件的内容\n包含多行文本',
            'test3.md': '# 这是一个Markdown文件\n\n内容测试',
            'empty.txt': '',  # 空文件
            'test.log': '这是一个不支持的文件类型',  # 不支持的类型
        }
        
        for filename, content in self.test_files.items():
            file_path = os.path.join(self.test_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.processor, FileProcessor)
        self.assertIn('.txt', self.processor.text_extensions)
        self.assertIn('.md', self.processor.text_extensions)
        self.assertIn('wav', self.processor.audio_formats)
    
    def test_scan_text_files(self):
        """测试扫描文本文件"""
        files = self.processor.scan_text_files(self.test_dir)
        
        # 应该找到3个有效的文本文件（排除空文件和不支持的文件）
        expected_files = ['test1.txt', 'test2.txt', 'test3.md']
        found_basenames = [os.path.basename(f) for f in files]
        
        for expected_file in expected_files:
            if expected_file != 'empty.txt':  # 空文件会被过滤掉
                self.assertIn(expected_file, found_basenames)
        
        self.assertNotIn('test.log', found_basenames)  # 不支持的文件类型
    
    def test_scan_text_files_nonexistent_folder(self):
        """测试扫描不存在的文件夹"""
        with self.assertRaises(FileNotFoundError):
            self.processor.scan_text_files('/nonexistent/folder')
    
    def test_scan_text_files_not_a_folder(self):
        """测试扫描非文件夹路径"""
        test_file = os.path.join(self.test_dir, 'test1.txt')
        with self.assertRaises(ValueError):
            self.processor.scan_text_files(test_file)
    
    def test_read_text_file(self):
        """测试读取文本文件"""
        test_file = os.path.join(self.test_dir, 'test1.txt')
        content = self.processor.read_text_file(test_file)
        
        self.assertEqual(content, self.test_files['test1.txt'])
    
    def test_read_text_file_multiline(self):
        """测试读取多行文本文件"""
        test_file = os.path.join(self.test_dir, 'test2.txt')
        content = self.processor.read_text_file(test_file)
        
        self.assertEqual(content, self.test_files['test2.txt'])
    
    def test_read_text_file_nonexistent(self):
        """测试读取不存在的文件"""
        with self.assertRaises(FileNotFoundError):
            self.processor.read_text_file('/nonexistent/file.txt')
    
    def test_read_text_file_empty(self):
        """测试读取空文件"""
        empty_file = os.path.join(self.test_dir, 'empty.txt')
        content = self.processor.read_text_file(empty_file)
        
        self.assertEqual(content, '')
    
    def test_get_output_path(self):
        """测试获取输出路径"""
        input_file = os.path.join(self.test_dir, 'test1.txt')
        
        # 测试默认格式
        output_path = self.processor.get_output_path(input_file)
        expected_path = os.path.join(self.test_dir, 'test1.wav')
        self.assertEqual(output_path, expected_path)
        
        # 测试指定格式
        output_path_mp3 = self.processor.get_output_path(input_file, 'mp3')
        expected_path_mp3 = os.path.join(self.test_dir, 'test1.mp3')
        self.assertEqual(output_path_mp3, expected_path_mp3)
    
    def test_get_output_path_unsupported_format(self):
        """测试不支持的输出格式"""
        input_file = os.path.join(self.test_dir, 'test1.txt')
        
        with self.assertRaises(ValueError):
            self.processor.get_output_path(input_file, 'unsupported')
    
    def test_save_audio(self):
        """测试保存音频文件"""
        # 创建虚拟音频数据
        audio_data = b'fake_audio_data_for_testing'
        output_path = os.path.join(self.test_dir, 'output.wav')
        
        # 保存文件
        self.processor.save_audio(audio_data, output_path)
        
        # 验证文件是否创建
        self.assertTrue(os.path.exists(output_path))
        
        # 验证文件内容
        with open(output_path, 'rb') as f:
            saved_data = f.read()
        self.assertEqual(saved_data, audio_data)
    
    def test_save_audio_empty_data(self):
        """测试保存空音频数据"""
        output_path = os.path.join(self.test_dir, 'output.wav')
        
        with self.assertRaises(ValueError):
            self.processor.save_audio(b'', output_path)
        
        with self.assertRaises(ValueError):
            self.processor.save_audio(None, output_path)
    
    def test_save_audio_nested_directory(self):
        """测试保存到嵌套目录"""
        nested_dir = os.path.join(self.test_dir, 'nested', 'folder')
        output_path = os.path.join(nested_dir, 'output.wav')
        audio_data = b'test_audio_data'
        
        # 保存文件（应该自动创建目录）
        self.processor.save_audio(audio_data, output_path)
        
        # 验证目录和文件都被创建
        self.assertTrue(os.path.exists(nested_dir))
        self.assertTrue(os.path.exists(output_path))
    
    def test_validate_input_file(self):
        """测试验证输入文件"""
        # 测试有效文件
        valid_file = os.path.join(self.test_dir, 'test1.txt')
        self.assertTrue(self.processor.validate_input_file(valid_file))
        
        # 测试不存在的文件
        nonexistent_file = os.path.join(self.test_dir, 'nonexistent.txt')
        self.assertFalse(self.processor.validate_input_file(nonexistent_file))
        
        # 测试不支持的文件类型
        unsupported_file = os.path.join(self.test_dir, 'test.log')
        self.assertFalse(self.processor.validate_input_file(unsupported_file))
        
        # 测试空文件
        empty_file = os.path.join(self.test_dir, 'empty.txt')
        self.assertFalse(self.processor.validate_input_file(empty_file))
    
    def test_get_file_info(self):
        """测试获取文件信息"""
        test_file = os.path.join(self.test_dir, 'test1.txt')
        file_info = self.processor.get_file_info(test_file)
        
        # 验证返回的信息
        self.assertEqual(file_info['path'], test_file)
        self.assertEqual(file_info['name'], 'test1.txt')
        self.assertEqual(file_info['stem'], 'test1')
        self.assertEqual(file_info['suffix'], '.txt')
        self.assertGreater(file_info['size'], 0)
        self.assertGreater(file_info['text_length'], 0)
        self.assertTrue(file_info['is_valid'])
    
    def test_get_file_info_nonexistent(self):
        """测试获取不存在文件的信息"""
        nonexistent_file = '/nonexistent/file.txt'
        file_info = self.processor.get_file_info(nonexistent_file)
        
        self.assertEqual(file_info['path'], nonexistent_file)
        self.assertIn('error', file_info)
        self.assertFalse(file_info['is_valid'])
    
    def test_batch_validate_files(self):
        """测试批量验证文件"""
        all_files = [
            os.path.join(self.test_dir, 'test1.txt'),
            os.path.join(self.test_dir, 'test2.txt'),
            os.path.join(self.test_dir, 'empty.txt'),
            os.path.join(self.test_dir, 'nonexistent.txt'),
        ]
        
        results = self.processor.batch_validate_files(all_files)
        
        # 验证结果结构
        self.assertIn('valid_files', results)
        self.assertIn('invalid_files', results)
        self.assertIn('total_count', results)
        self.assertIn('valid_count', results)
        self.assertIn('invalid_count', results)
        
        # 验证统计数据
        self.assertEqual(results['total_count'], len(all_files))
        self.assertEqual(results['valid_count'] + results['invalid_count'], results['total_count'])
        
        # 验证有效文件
        self.assertGreater(results['valid_count'], 0)
        self.assertIn(os.path.join(self.test_dir, 'test1.txt'), results['valid_files'])
        self.assertIn(os.path.join(self.test_dir, 'test2.txt'), results['valid_files'])
    
    def test_clean_temp_files(self):
        """测试清理临时文件"""
        # 创建临时目录和文件
        temp_dir = os.path.join(self.test_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_files = ['temp1.txt', 'temp2.wav']
        for temp_file in temp_files:
            temp_path = os.path.join(temp_dir, temp_file)
            with open(temp_path, 'w') as f:
                f.write('temp content')
        
        # 验证文件存在
        for temp_file in temp_files:
            temp_path = os.path.join(temp_dir, temp_file)
            self.assertTrue(os.path.exists(temp_path))
        
        # 清理临时文件
        self.processor.clean_temp_files(temp_dir)
        
        # 验证文件被删除
        for temp_file in temp_files:
            temp_path = os.path.join(temp_dir, temp_file)
            self.assertFalse(os.path.exists(temp_path))
    
    def test_create_backup(self):
        """测试创建文件备份"""
        original_file = os.path.join(self.test_dir, 'test1.txt')
        
        # 创建备份
        backup_path = self.processor.create_backup(original_file)
        
        # 验证备份文件存在
        self.assertTrue(os.path.exists(backup_path))
        
        # 验证备份文件内容
        original_content = self.processor.read_text_file(original_file)
        backup_content = self.processor.read_text_file(backup_path)
        self.assertEqual(original_content, backup_content)
        
        # 验证备份文件名包含时间戳
        self.assertIn('backup', os.path.basename(backup_path))


class TestFileProcessorIntegration(unittest.TestCase):
    """文件处理器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.processor = FileProcessor()
        self.test_dir = tempfile.mkdtemp()
        
        # 创建测试文件
        test_content = "这是一个集成测试文件的内容"
        self.test_file = os.path.join(self.test_dir, 'integration_test.txt')
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 扫描文件
        files = self.processor.scan_text_files(self.test_dir)
        self.assertIn(self.test_file, files)
        
        # 2. 验证文件
        self.assertTrue(self.processor.validate_input_file(self.test_file))
        
        # 3. 读取文件内容
        content = self.processor.read_text_file(self.test_file)
        self.assertGreater(len(content), 0)
        
        # 4. 生成输出路径
        output_path = self.processor.get_output_path(self.test_file)
        self.assertTrue(output_path.endswith('.wav'))
        
        # 5. 模拟保存音频文件
        fake_audio = b'fake_audio_data'
        self.processor.save_audio(fake_audio, output_path)
        
        # 6. 验证输出文件
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'rb') as f:
            saved_data = f.read()
        self.assertEqual(saved_data, fake_audio)


if __name__ == '__main__':
    unittest.main() 