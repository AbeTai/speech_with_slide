#!/usr/bin/env python3
"""
プロンプト管理システム
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PromptManager:
    """プロンプト管理クラス"""
    
    def __init__(self, config_path: str = "prompts.yaml"):
        """
        プロンプト管理システムを初期化
        
        Args:
            config_path: プロンプト設定ファイルのパス
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"Loaded prompt config from: {self.config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"Prompt config file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML config: {e}")
            raise
    
    def get_script_generation_prompts(self, page_num: int) -> Dict[str, str]:
        """
        原稿生成用のプロンプトを取得
        
        Args:
            page_num: ページ番号
            
        Returns:
            system_promptとuser_promptを含む辞書
        """
        script_config = self.config.get("script_generation", {})
        
        system_prompt = script_config.get("system_prompt", "")
        user_prompt = script_config.get("user_prompt", "").format(page_num=page_num)
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }
    
    def get_claude_config(self) -> Dict[str, Any]:
        """Claude APIの設定を取得"""
        return self.config.get("model_config", {}).get("claude", {})
    
    def get_gemini_tts_config(self) -> Dict[str, Any]:
        """Gemini TTSの設定を取得"""
        return self.config.get("model_config", {}).get("gemini_tts", {})
    
    def get_customization_config(self) -> Dict[str, Any]:
        """カスタマイゼーション設定を取得"""
        return self.config.get("customization", {})
    
    def get_presentation_style(self) -> Dict[str, str]:
        """プレゼンテーションスタイルの設定を取得"""
        return self.get_customization_config().get("presentation_style", {})
    
    def get_script_length_config(self) -> Dict[str, int]:
        """原稿の長さに関する設定を取得"""
        return self.get_customization_config().get("script_length", {})
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        設定を更新してファイルに保存
        
        Args:
            new_config: 新しい設定辞書
        """
        self.config.update(new_config)
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self.config, f, allow_unicode=True, default_flow_style=False)
                logger.info(f"Updated prompt config: {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    def reload_config(self) -> None:
        """設定ファイルを再読み込み"""
        self.config = self._load_config()