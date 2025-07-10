#!/usr/bin/env python3
"""
Test script to combine existing videos into final presentation
"""

import os
import sys
from pathlib import Path
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def combine_videos(video_paths, output_path):
    """複数の動画を結合して最終的なプレゼン動画を作成"""
    logger.info(f"Combining {len(video_paths)} videos into final presentation")
    
    try:
        output_dir = Path("output")
        
        # 入力リストファイルを作成
        input_list_path = output_dir / "input_list.txt"
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
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, ffmpeg_cmd, result.stderr)
        
        # クリーンアップ
        os.unlink(input_list_path)
        
        logger.info(f"Final presentation video created: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Error combining videos: {e}")
        raise

def main():
    # 既存の動画ファイルを取得
    output_dir = Path("output")
    video_files = sorted(output_dir.glob("slide_*_video.mp4"))
    
    if not video_files:
        print("No video files found in output directory")
        return
    
    logger.info(f"Found {len(video_files)} video files:")
    for video_file in video_files:
        logger.info(f"  - {video_file}")
    
    # 動画を結合
    output_path = "test_presentation.mp4"
    try:
        final_video = combine_videos([str(f) for f in video_files], output_path)
        print(f"✅ Test presentation video created: {final_video}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    main()