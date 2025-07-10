#!/usr/bin/env python3
"""
AI-powered presentation video generator from PDF slides
"""

import os
import sys
from pathlib import Path
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from pdf2image import convert_from_path
from PIL import Image
import anthropic
from google import genai
from google.genai import types
import wave
import cv2
import numpy as np
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips
    from moviepy.audio.io.AudioFileClip import AudioFileClip
except ImportError:
    VideoFileClip = None
    concatenate_videoclips = None
    AudioFileClip = None
import tempfile
import shutil
from prompt_manager import PromptManager

# Load environment variables
load_dotenv()

class PresentationVideoGenerator:
    def __init__(self, project_name: str):
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        self.project_name = project_name
        self.prompt_manager = PromptManager()
        
        # プロジェクトごとのディレクトリ構造を作成
        self.base_output_dir = Path("output") / project_name
        self.txt_dir = self.base_output_dir / "txt"
        self.wav_dir = self.base_output_dir / "wav"
        self.mp4_dir = self.base_output_dir / "mp4"
        
        # ディレクトリを作成
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.txt_dir.mkdir(exist_ok=True)
        self.wav_dir.mkdir(exist_ok=True)
        self.mp4_dir.mkdir(exist_ok=True)
        
    def extract_images_from_pdf(self, pdf_path: str) -> List[Image.Image]:
        """PDFから各ページの画像を抽出"""
        logger.info(f"Extracting images from PDF: {pdf_path}")
        try:
            images = convert_from_path(pdf_path, dpi=300)
            logger.info(f"Extracted {len(images)} pages from PDF")
            return images
        except Exception as e:
            logger.error(f"Error extracting images from PDF: {e}")
            raise
    
    def generate_script_for_slide(self, pdf_path: str, page_num: int) -> str:
        """Claudeを使用してスライドの説明原稿を生成"""
        logger.info(f"Generating script for slide {page_num}")
        
        try:
            # プロンプトを取得
            prompts = self.prompt_manager.get_script_generation_prompts(page_num)
            claude_config = self.prompt_manager.get_claude_config()
            
            # PDFを読み込んでbase64エンコード
            import base64
            with open(pdf_path, 'rb') as f:
                pdf_data = base64.b64encode(f.read()).decode('utf-8')
            
            # システムプロンプトがある場合は使用
            messages = []
            if prompts.get("system_prompt"):
                messages.append({
                    "role": "system",
                    "content": prompts["system_prompt"]
                })
            
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": pdf_data
                        }
                    },
                    {
                        "type": "text",
                        "text": prompts["user_prompt"]
                    }
                ]
            })
            
            message = self.anthropic_client.messages.create(
                model=claude_config.get("model", "claude-3-7-sonnet-20250219"),
                max_tokens=claude_config.get("max_tokens", 1000),
                temperature=claude_config.get("temperature", 0.1),
                messages=messages
            )
            
            script = message.content[0].text
            logger.info(f"Generated script for slide {page_num}: {len(script)} characters")
            return script
            
        except Exception as e:
            logger.error(f"Error generating script for slide {page_num}: {e}")
            raise
    
    def text_to_speech(self, text: str, output_path: str) -> str:
        """GeminiのTTSを使用してテキストを音声に変換"""
        logger.info(f"Converting text to speech: {len(text)} characters")
        
        try:
            # Gemini TTS設定を取得
            tts_config = self.prompt_manager.get_gemini_tts_config()
            
            # Gemini TTSの実装
            response = self.genai_client.models.generate_content(
                model=tts_config.get("model", "gemini-2.5-flash-preview-tts"),
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=tts_config.get("voice_name", "Kore"),
                            )
                        )
                    ),
                )
            )
            
            # 音声データを取得
            audio_data = response.candidates[0].content.parts[0].inline_data.data
            
            # WAVファイルとして保存
            with wave.open(output_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(24000)
                wf.writeframes(audio_data)
            
            logger.info(f"Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {e}")
            raise
    
    def create_video_from_slide_and_audio(self, image: Image.Image, audio_path: str, output_path: str) -> str:
        """スライド画像と音声を合成して動画を作成"""
        logger.info(f"Creating video from slide and audio: {output_path}")
        
        try:
            # 画像を一時ファイルに保存（サイズ調整）
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                # 高さを2で割り切れるように調整
                width, height = image.size
                if height % 2 != 0:
                    height -= 1
                if width % 2 != 0:
                    width -= 1
                
                # 画像をリサイズ
                resized_image = image.resize((width, height), Image.LANCZOS)
                resized_image.save(temp_file.name)
                temp_image_path = temp_file.name
            
            # FFmpegを使用して動画を作成
            import subprocess
            
            # 音声の長さを取得（ffprobeを使用）
            duration_cmd = [
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
            ]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(duration_result.stdout.strip())
            
            # FFmpegで画像と音声を合成
            ffmpeg_cmd = [
                'ffmpeg', '-y',  # -y for overwrite
                '-loop', '1',    # Loop the image
                '-i', temp_image_path,  # Input image
                '-i', audio_path,       # Input audio
                '-c:v', 'libx264',      # Video codec
                '-c:a', 'aac',          # Audio codec
                '-t', str(duration),    # Duration
                '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
                '-r', '1',              # Frame rate (1fps for static image)
                '-shortest',            # Stop encoding when the shortest input ends
                output_path
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, ffmpeg_cmd, result.stderr)
            
            # クリーンアップ
            os.unlink(temp_image_path)
            
            logger.info(f"Video created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            raise
    
    def combine_videos(self, video_paths: List[str], output_path: str) -> str:
        """複数の動画を結合して最終的なプレゼン動画を作成"""
        logger.info(f"Combining {len(video_paths)} videos into final presentation")
        
        try:
            # FFmpegを使用して動画を結合
            import subprocess
            
            # 入力リストファイルを作成
            input_list_path = self.base_output_dir / "input_list.txt"
            with open(input_list_path, 'w') as f:
                for video_path in video_paths:
                    f.write(f"file '{os.path.abspath(video_path)}'\n")
            
            # FFmpegで動画を結合
            ffmpeg_cmd = [
                'ffmpeg', '-y',  # -y for overwrite
                '-f', 'concat',  # Concat format
                '-safe', '0',    # Allow absolute paths
                '-i', str(input_list_path),  # Input list
                '-c', 'copy',    # Copy streams without re-encoding
                output_path
            ]
            
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
            
            # クリーンアップ
            os.unlink(input_list_path)
            
            logger.info(f"Final presentation video created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error combining videos: {e}")
            raise
    
    def generate_presentation_video(self, pdf_path: str) -> str:
        """PDFからプレゼン動画を生成するメイン処理"""
        logger.info(f"Starting presentation video generation from: {pdf_path}")
        
        try:
            # 1. PDFから画像を抽出
            images = self.extract_images_from_pdf(pdf_path)
            
            video_paths = []
            
            # 2. 各スライドに対して処理
            for i, image in enumerate(images, 1):
                logger.info(f"Processing slide {i}/{len(images)}")
                
                # 3. 原稿生成
                script = self.generate_script_for_slide(pdf_path, i)
                
                # 原稿をファイルに保存
                script_path = self.txt_dir / f"slide_{i:03d}_script.txt"
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(script)
                logger.info(f"Script saved to: {script_path}")
                
                # 4. 音声生成
                audio_path = self.wav_dir / f"slide_{i:03d}_audio.wav"
                self.text_to_speech(script, str(audio_path))
                
                # 5. 動画生成
                video_path = self.mp4_dir / f"slide_{i:03d}_video.mp4"
                self.create_video_from_slide_and_audio(image, str(audio_path), str(video_path))
                video_paths.append(str(video_path))
            
            # 6. 動画を結合して最終出力
            final_video_name = f"{self.project_name}.mp4"
            final_video_path = self.base_output_dir / final_video_name
            self.combine_videos(video_paths, str(final_video_path))
            
            logger.info(f"Presentation video generation completed: {final_video_path}")
            return str(final_video_path)
            
        except Exception as e:
            logger.error(f"Error in presentation video generation: {e}")
            raise


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("Usage: python main.py <pdf_path>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    # プロジェクト名をPDFファイル名から生成
    project_name = Path(pdf_path).stem
    
    # 必要なAPI KEYの確認
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY not found in environment variables")
        sys.exit(1)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in environment variables")
        sys.exit(1)
    
    generator = PresentationVideoGenerator(project_name)
    
    try:
        final_video = generator.generate_presentation_video(pdf_path)
        print(f"✅ Presentation video generated successfully: {final_video}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()