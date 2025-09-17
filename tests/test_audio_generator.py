#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音频生成器测试模块
"""

import unittest
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.audio_generator import AudioGenerator


class TestAudioGenerator(unittest.TestCase):
    """音频生成器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = AudioGenerator()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.generator, AudioGenerator)
        self.assertIsNone(self.generator._voices_cache)
    
    def test_get_available_voices_mock(self):
        """测试获取音色列表（模拟模式）"""
        voices = self.generator.get_available_voices()
        
        self.assertIsInstance(voices, list)
        self.assertGreater(len(voices), 0)
        
        # 检查音色数据格式
        for voice in voices:
            self.assertIn('id', voice)
            self.assertIn('name', voice)
            self.assertIsInstance(voice['id'], str)
            self.assertIsInstance(voice['name'], str)
    
    def test_generate_audio_mock(self):
        """测试生成音频（模拟模式）"""
        text = "这是一个测试文本"
        voice_id = "voice_1"
        
        audio_data = self.generator.generate_audio(text, voice_id)
        
        self.assertIsInstance(audio_data, bytes)
        self.assertGreater(len(audio_data), 0)
    
    def test_generate_audio_empty_text(self):
        """测试空文本生成音频"""
        with self.assertRaises(ValueError):
            self.generator.generate_audio("", "voice_1")
        
        with self.assertRaises(ValueError):
            self.generator.generate_audio("   ", "voice_1")
    
    def test_generate_audio_empty_voice_id(self):
        """测试空音色ID生成音频"""
        with self.assertRaises(ValueError):
            self.generator.generate_audio("测试文本", "")
        
        with self.assertRaises(ValueError):
            self.generator.generate_audio("测试文本", None)
    
    def test_batch_generate(self):
        """测试批量生成音频"""
        texts = ["文本1", "文本2", "文本3"]
        voice_id = "voice_1"
        
        results = self.generator.batch_generate(texts, voice_id)
        
        self.assertEqual(len(results), len(texts))
        for result in results:
            self.assertIsInstance(result, bytes)
            self.assertGreater(len(result), 0)
    
    def test_batch_generate_empty_list(self):
        """测试空列表批量生成"""
        results = self.generator.batch_generate([], "voice_1")
        self.assertEqual(results, [])
    
    def test_validate_voice_id(self):
        """测试验证音色ID"""
        # 获取可用音色
        voices = self.generator.get_available_voices()
        if voices:
            valid_voice_id = voices[0]['id']
            self.assertTrue(self.generator.validate_voice_id(valid_voice_id))
        
        # 测试无效音色ID
        self.assertFalse(self.generator.validate_voice_id("invalid_voice_id"))
    
    def test_get_voice_info(self):
        """测试获取音色信息"""
        voices = self.generator.get_available_voices()
        if voices:
            voice_id = voices[0]['id']
            voice_info = self.generator.get_voice_info(voice_id)
            
            self.assertIsNotNone(voice_info)
            self.assertEqual(voice_info['id'], voice_id)
        
        # 测试不存在的音色
        invalid_info = self.generator.get_voice_info("invalid_voice")
        self.assertIsNone(invalid_info)
    
    def test_clear_cache(self):
        """测试清空缓存"""
        # 先获取音色列表以填充缓存
        self.generator.get_available_voices()
        self.assertIsNotNone(self.generator._voices_cache)
        
        # 清空缓存
        self.generator.clear_cache()
        self.assertIsNone(self.generator._voices_cache)
        self.assertEqual(self.generator._cache_timestamp, 0)
    
    def test_test_connection(self):
        """测试连接测试"""
        result = self.generator.test_connection()
        self.assertIsInstance(result, bool)
    
    @patch.dict(os.environ, {'FISH_AUDIO_API_KEY': 'test_key'})
    def test_api_key_from_env(self):
        """测试从环境变量获取API密钥"""
        generator = AudioGenerator()
        self.assertEqual(generator.api_key, 'test_key')
    
    def test_set_api_key(self):
        """测试设置API密钥"""
        new_key = "new_test_key"
        self.generator.set_api_key(new_key)
        self.assertEqual(self.generator.api_key, new_key)


class TestAudioGeneratorIntegration(unittest.TestCase):
    """音频生成器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.generator = AudioGenerator()
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 获取音色列表
        voices = self.generator.get_available_voices()
        self.assertGreater(len(voices), 0)
        
        # 2. 选择一个音色
        voice_id = voices[0]['id']
        
        # 3. 验证音色
        self.assertTrue(self.generator.validate_voice_id(voice_id))
        
        # 4. 生成音频
        text = "这是一个集成测试文本"
        audio_data = self.generator.generate_audio(text, voice_id)
        
        # 5. 验证结果
        self.assertIsInstance(audio_data, bytes)
        self.assertGreater(len(audio_data), 0)
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试各种错误情况
        with self.assertRaises(ValueError):
            self.generator.generate_audio("", "voice_1")
        
        with self.assertRaises(ValueError):
            self.generator.generate_audio("测试", "")


if __name__ == '__main__':
    unittest.main() 