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
    
    
    
    def get_gemini_tts_config(self) -> Dict[str, Any]:
        """Gemini TTSの設定を取得"""
        return self.config.get("model_config", {}).get("gemini_tts", {})
    
    
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