#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
音频生成器模块

封装 Fish Audio SDK 的调用，提供文本转音频的功能
"""

import os
import time
from typing import List, Dict, Optional, Union
from loguru import logger

try:
    import fish_audio_sdk
    FISH_AUDIO_AVAILABLE = True
except ImportError:
    logger.warning("Fish Audio SDK 未安装，将使用模拟模式")
    FISH_AUDIO_AVAILABLE = False


class AudioGenerator:
    """音频生成器类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化音频生成器
        
        Args:
            api_key: Fish Audio API 密钥，如果为空则从环境变量获取
        """
        self.api_key = api_key or os.getenv('FISH_AUDIO_API_KEY')
        self.client = None
        self._voices_cache = None
        self._cache_timestamp = 0
        
        # 初始化客户端
        self.init_client()
        
        logger.info("音频生成器初始化完成")
    
    def init_client(self):
        """初始化 Fish Audio 客户端"""
        if not FISH_AUDIO_AVAILABLE:
            logger.warning("Fish Audio SDK 不可用，使用模拟模式")
            return
        
        if not self.api_key:
            logger.warning("未设置 Fish Audio API 密钥，请在设置中配置")
            self.client = None
            return
        
        try:
            # 使用正确的Fish Audio SDK API
            self.client = fish_audio_sdk.Session(apikey=self.api_key)
            logger.info("Fish Audio 客户端初始化成功")
        except Exception as e:
            logger.exception(f"Fish Audio 客户端初始化失败: {e}")
            self.client = None
    
    def get_available_voices(self) -> List[Dict[str, str]]:
        """
        获取可用的音色列表
        
        Returns:
            音色列表，每个音色包含 id 和 name
        """
        # 检查缓存是否有效（缓存5分钟）
        current_time = time.time()
        if (self._voices_cache is not None and 
            current_time - self._cache_timestamp < 300):
            return self._voices_cache
        
        if not FISH_AUDIO_AVAILABLE or not self.api_key or not self.client:
            # 模拟模式或未配置API密钥时返回示例音色
            voices = [
                {"id": "voice_1", "name": "女声-温柔"},
                {"id": "voice_2", "name": "男声-磁性"},
                {"id": "voice_3", "name": "女声-活泼"},
                {"id": "voice_4", "name": "男声-沉稳"},
                {"id": "voice_5", "name": "儿童-可爱"},
            ]
            if not self.api_key:
                logger.warning("未设置API密钥，显示示例音色")
            else:
                logger.info(f"模拟模式：返回 {len(voices)} 个示例音色")
            return voices
        
        try:
            # 获取个人模型（使用修复后的逻辑）
            user_models = self.get_user_models()
            logger.debug(f"获取到 {len(user_models)} 个个人模型")
            
            # 获取公共模型
            public_models = self.get_public_models(limit=20)
            logger.debug(f"获取到 {len(public_models)} 个公共模型")
            
            # 合并所有音色，个人模型优先
            all_voices = user_models + public_models
            
            # 按照状态和喜欢数排序
            all_voices.sort(key=lambda x: (
                x.get('visibility', '') != 'private',  # 个人模型优先
                x.get('state', '') != 'trained',  # 已训练的模型优先
                -x.get('like_count', 0)  # 然后按喜欢数排序
            ))
            
            # 更新缓存
            self._voices_cache = all_voices
            self._cache_timestamp = current_time
            
            logger.info(f"获取到 {len(all_voices)} 个音色模型（个人：{len(user_models)}，公共：{len(public_models)}）")
            return all_voices
            
        except Exception as e:
            logger.exception(f"获取音色列表失败: {e}")
            # 返回缓存的音色（如果有）
            if self._voices_cache:
                logger.info("使用缓存的音色列表")
                return self._voices_cache
            raise
    
    def generate_audio(self, text: str, voice_id: str, **kwargs) -> bytes:
        """
        生成音频
        
        Args:
            text: 要转换的文本
            voice_id: 音色ID
            **kwargs: 其他参数（如语速、音调等）
            
        Returns:
            音频数据（bytes）
        """
        if not text.strip():
            raise ValueError("文本内容不能为空")
        
        if not voice_id:
            raise ValueError("音色ID不能为空")
        
        if not FISH_AUDIO_AVAILABLE or not self.api_key or not self.client:
            # 模拟模式或未配置API密钥：生成一个假的音频数据
            if not self.api_key:
                logger.info(f"未配置API密钥，模拟生成音频：'{text[:50]}...'")
            else:
                logger.info(f"模拟模式：为文本 '{text[:50]}...' 生成音频")
            time.sleep(1)  # 模拟处理时间
            # 返回一个简单的WAV文件头（实际使用时这里应该是真实的音频数据）
            return self._generate_dummy_audio()
        
        try:
            logger.info(f"正在生成音频，文本长度: {len(text)}, 音色: {voice_id}")
            
            # 使用正确的Fish Audio SDK API进行TTS
            tts_request = fish_audio_sdk.TTSRequest(
                text=text,
                reference_id=voice_id
            )
            
            # 调用TTS API，收集所有音频块
            audio_data = b""
            for chunk in self.client.tts(tts_request):
                audio_data += chunk
            
            if not audio_data:
                raise ValueError("生成的音频数据为空")
            
            logger.info(f"音频生成成功，数据大小: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.exception(f"音频生成失败: {e}")
            raise
    
    def batch_generate(self, texts: List[str], voice_id: str, **kwargs) -> List[bytes]:
        """
        批量生成音频
        
        Args:
            texts: 文本列表
            voice_id: 音色ID
            **kwargs: 其他参数
            
        Returns:
            音频数据列表
        """
        if not texts:
            return []
        
        logger.info(f"开始批量生成 {len(texts)} 个音频")
        
        results = []
        for i, text in enumerate(texts):
            try:
                logger.info(f"正在处理第 {i+1}/{len(texts)} 个文本")
                audio_data = self.generate_audio(text, voice_id, **kwargs)
                results.append(audio_data)
            except Exception as e:
                logger.error(f"第 {i+1} 个文本处理失败: {e}")
                results.append(None)
        
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"批量生成完成，成功: {success_count}/{len(texts)}")
        
        return results
    
    def validate_voice_id(self, voice_id: str) -> bool:
        """
        验证音色ID是否有效
        
        Args:
            voice_id: 音色ID
            
        Returns:
            是否有效
        """
        try:
            voices = self.get_available_voices()
            return any(voice["id"] == voice_id for voice in voices)
        except Exception:
            logger.warning("无法验证音色ID")
            return True  # 如果无法验证，默认认为有效
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict[str, str]]:
        """
        获取音色信息
        
        Args:
            voice_id: 音色ID
            
        Returns:
            音色信息字典，如果未找到则返回None
        """
        try:
            voices = self.get_available_voices()
            for voice in voices:
                if voice["id"] == voice_id:
                    return voice
            return None
        except Exception:
            logger.warning(f"无法获取音色信息: {voice_id}")
            return None
    
    def get_user_models(self) -> List[Dict[str, str]]:
        """
        获取用户的个人音色模型
        
        Returns:
            用户个人音色模型列表
        """
        if not FISH_AUDIO_AVAILABLE or not self.api_key or not self.client:
            logger.warning("无法获取用户模型：SDK不可用或未配置API密钥")
            return []
        
        try:
            # 首先尝试获取个人模型
            user_models = []
            
            try:
                # 使用 self_only=True 参数获取个人模型（根据FishAudioService的成功实现）
                personal_models_response = self.client.list_models(self_only=True)
                logger.debug(f"个人模型API响应类型: {type(personal_models_response)}")
                
                # 按照FishAudioService的处理方式
                personal_models = []
                if hasattr(personal_models_response, 'data'):
                    personal_models = personal_models_response.data
                    logger.debug(f"使用data属性，找到 {len(personal_models)} 个个人模型")
                elif hasattr(personal_models_response, 'items'):
                    personal_models = personal_models_response.items
                    logger.debug(f"使用items属性，找到 {len(personal_models)} 个个人模型")
                else:
                    # 如果不是分页响应，直接返回
                    personal_models = list(personal_models_response) if personal_models_response else []
                    logger.debug(f"直接转换为列表，找到 {len(personal_models)} 个个人模型")
                
                # 处理个人模型
                for model in personal_models:
                    model_type = getattr(model, 'type', None)
                    if model_type == 'tts':
                        model_id = getattr(model, 'id', '')
                        title = getattr(model, 'title', '未知音色')
                        description = getattr(model, 'description', '')
                        
                        # 获取语言信息
                        languages = getattr(model, 'languages', [])
                        language_str = ", ".join(languages) if languages else ""
                        
                        # 构建显示名称
                        display_name = title
                        if language_str:
                            display_name += f" ({language_str})"
                        
                        # 获取其他属性
                        state = getattr(model, 'state', 'unknown')
                        
                        user_models.append({
                            "id": model_id,
                            "name": display_name,
                            "title": title,
                            "description": description,
                            "languages": languages,
                            "type": model_type,
                            "visibility": "private",  # 个人模型标记为private
                            "state": state
                        })
                        
                logger.info(f"从个人模型API获取到 {len(user_models)} 个个人TTS模型")
                
            except Exception as personal_error:
                logger.warning(f"获取个人模型失败，尝试从全量模型中筛选: {personal_error}")
                
                # 如果个人模型API失败，从全量模型中筛选
                all_models_response = self.client.list_models()
                logger.debug(f"全量模型API响应类型: {type(all_models_response)}")
                
                # 处理返回的模型列表
                all_models = []
                if hasattr(all_models_response, 'items'):
                    all_models = all_models_response.items
                    logger.debug(f"使用items属性，找到 {len(all_models)} 个模型")
                elif hasattr(all_models_response, 'data'):
                    all_models = all_models_response.data
                    logger.debug(f"使用data属性，找到 {len(all_models)} 个模型")
                else:
                    all_models = list(all_models_response) if all_models_response else []
                    logger.debug(f"直接转换为列表，找到 {len(all_models)} 个模型")
                
                total_models = 0
                tts_models = 0
                private_models = 0
                
                for model in all_models:
                    total_models += 1
                    
                    # 获取模型信息
                    model_id = getattr(model, 'id', '')
                    model_type = getattr(model, 'type', None)
                    visibility = getattr(model, 'visibility', None)
                    
                    logger.debug(f"模型 {model_id}: type={model_type}, visibility={visibility}")
                    
                    # 只处理TTS类型的个人模型
                    if model_type == 'tts':
                        tts_models += 1
                        
                        # 检查是否为个人模型 (visibility=private)
                        if visibility == 'private':
                            private_models += 1
                            
                            title = getattr(model, 'title', '未知音色')
                            description = getattr(model, 'description', '')
                            
                            # 获取语言信息
                            languages = getattr(model, 'languages', [])
                            language_str = ", ".join(languages) if languages else ""
                            
                            # 构建显示名称
                            display_name = title
                            if language_str:
                                display_name += f" ({language_str})"
                            
                            # 获取其他属性
                            state = getattr(model, 'state', 'unknown')
                            
                            user_models.append({
                                "id": model_id,
                                "name": display_name,
                                "title": title,
                                "description": description,
                                "languages": languages,
                                "type": model_type,
                                "visibility": visibility,
                                "state": state
                            })
                
                logger.info(f"从全量模型中筛选：扫描了 {total_models} 个模型，其中 {tts_models} 个TTS模型，{private_models} 个个人模型")
            
            # 按照状态排序（已训练的优先）
            user_models.sort(key=lambda x: x.get('state', '') != 'trained')
            
            logger.info(f"找到 {len(user_models)} 个个人音色模型")
            return user_models
            
        except Exception as e:
            logger.exception(f"获取用户模型失败: {e}")
            return []
    
    def get_public_models(self, limit: int = 50) -> List[Dict[str, str]]:
        """
        获取热门的公共音色模型
        
        Args:
            limit: 返回的模型数量限制
            
        Returns:
            公共音色模型列表
        """
        try:
            # 直接获取公共模型，不调用get_available_voices避免递归
            models_response = self.client.list_models()
            
            # 处理返回的模型列表
            models = []
            if hasattr(models_response, 'items'):
                models = models_response.items
            elif hasattr(models_response, 'data'):
                models = models_response.data
            else:
                models = list(models_response) if models_response else []
            
            # 筛选出公共TTS模型
            public_models = []
            for model in models:
                model_type = getattr(model, 'type', None)
                visibility = getattr(model, 'visibility', None)
                
                if model_type == 'tts' and visibility == 'public':
                    # 获取模型信息
                    model_id = getattr(model, 'id', '')
                    title = getattr(model, 'title', '未知音色')
                    description = getattr(model, 'description', '')
                    
                    # 获取语言信息
                    languages = getattr(model, 'languages', [])
                    language_str = ", ".join(languages) if languages else ""
                    
                    # 获取作者信息
                    author_info = ""
                    if hasattr(model, 'author') and model.author:
                        author_nickname = getattr(model.author, 'nickname', '')
                        if author_nickname:
                            author_info = f" - {author_nickname}"
                    
                    # 构建显示名称
                    display_name = title
                    if language_str:
                        display_name += f" ({language_str})"
                    display_name += author_info
                    
                    # 获取其他属性
                    like_count = getattr(model, 'like_count', 0)
                    state = getattr(model, 'state', 'unknown')
                    
                    public_models.append({
                        "id": model_id,
                        "name": display_name,
                        "title": title,
                        "description": description,
                        "languages": languages,
                        "author": author_info.replace(" - ", "") if author_info else "",
                        "type": model_type,
                        "visibility": visibility,
                        "like_count": like_count,
                        "state": state
                    })
            
            # 按喜欢数排序并限制数量
            public_models.sort(key=lambda x: x.get('like_count', 0), reverse=True)
            
            result = public_models[:limit] if len(public_models) > limit else public_models
            logger.info(f"返回 {len(result)} 个热门公共模型")
            return result
            
        except Exception as e:
            logger.exception(f"获取公共模型失败: {e}")
            return []
    
    def _generate_dummy_audio(self) -> bytes:
        """
        生成虚拟音频数据（用于测试和模拟）
        
        Returns:
            虚拟的WAV音频数据
        """
        # 简单的WAV文件头
        wav_header = (
            b'RIFF'
            b'\x24\x08\x00\x00'  # 文件大小 - 8
            b'WAVE'
            b'fmt '
            b'\x10\x00\x00\x00'  # fmt chunk 大小
            b'\x01\x00'          # 音频格式 (PCM)
            b'\x01\x00'          # 声道数
            b'\x44\xac\x00\x00'  # 采样率 (44100)
            b'\x88\x58\x01\x00'  # 字节率
            b'\x02\x00'          # 块对齐
            b'\x10\x00'          # 位深度
            b'data'
            b'\x00\x08\x00\x00'  # 数据大小
        )
        
        # 生成简单的音频数据（静音）
        audio_data = b'\x00' * 2048
        
        return wav_header + audio_data
    
    def clear_cache(self):
        """清空音色缓存"""
        self._voices_cache = None
        self._cache_timestamp = 0
    
    def set_api_key(self, api_key: str):
        """
        设置新的API密钥
        
        Args:
            api_key: 新的API密钥
        """
        self.api_key = api_key
        self.clear_cache()
        self.init_client()
        logger.info("API密钥已更新")
    
    def test_connection(self) -> bool:
        """
        测试与Fish Audio服务的连接
        
        Returns:
            连接是否正常
        """
        if not FISH_AUDIO_AVAILABLE:
            logger.info("模拟模式：连接测试通过")
            return True
        
        try:
            voices = self.get_available_voices()
            if voices:
                logger.info("连接测试成功")
                return True
            else:
                logger.warning("连接测试失败：未获取到音色列表")
                return False
        except Exception as e:
            logger.error(f"连接测试失败: {e}")
            return False 