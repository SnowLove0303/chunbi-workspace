"""
Video Workflow - Full video processing pipeline
Auto-manage ffmpeg installation
"""

import os
import sys
import urllib.request
import zipfile
import subprocess
from pathlib import Path

# Config - 使用用户提供的 ffmpeg 路径
FFMPEG_DIR = Path(r"F:/依赖/ffmpeg/ffmpeg-8.1-essentials_build")
FFMPEG_BIN = FFMPEG_DIR / "bin" / "ffmpeg.exe"
FFPROBE_BIN = FFMPEG_DIR / "bin" / "ffprobe.exe"

class FFmpegManager:
    """Auto-manage ffmpeg installation"""
    
    @staticmethod
    def is_installed():
        """Check if ffmpeg is installed"""
        if FFMPEG_BIN.exists():
            return True
        # Check system PATH
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
            return True
        except:
            return False
    
    @staticmethod
    def get_ffmpeg_path():
        """Get ffmpeg path"""
        if FFMPEG_BIN.exists():
            return str(FFMPEG_BIN)
        return "ffmpeg"
    
    @staticmethod
    def get_ffprobe_path():
        """Get ffprobe path"""
        if FFPROBE_BIN.exists():
            return str(FFPROBE_BIN)
        return "ffprobe"
    
    @staticmethod
    def ensure_installed():
        """Ensure ffmpeg is installed"""
        if FFMPEG_BIN.exists():
            return True
        print("[Error] ffmpeg not found at expected path")
        print(f"[Info] Expected: {FFMPEG_BIN}")
        return False


def merge_video_audio(video_path, audio_path, output_path):
    """
    Merge video and audio
    
    Args:
        video_path: Video file path
        audio_path: Audio file path
        output_path: Output file path
    """
    if not FFmpegManager.ensure_installed():
        return False
    
    ffmpeg = FFmpegManager.get_ffmpeg_path()
    
    cmd = [
        ffmpeg,
        "-i", video_path,
        "-i", audio_path,
        "-c", "copy",
        "-y",
        output_path
    ]
    
    print(f"[Merge] Merging: {os.path.basename(output_path)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"[OK] Merge successful: {output_path}")
        return True
    else:
        print(f"[Error] Merge failed: {result.stderr}")
        return False


def process_bilibili_video(url, output_dir="F:/下载"):
    """
    Process Bilibili video: download and merge
    
    Args:
        url: Bilibili video URL
        output_dir: Output directory
    """
    import yt_dlp
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Download video and audio
    print("[Download] Downloading video...")
    
    ydl_opts_video = {
        'outtmpl': os.path.join(output_dir, '%(title)s_video.%(ext)s'),
        'format': 'bestvideo',
    }
    
    ydl_opts_audio = {
        'outtmpl': os.path.join(output_dir, '%(title)s_audio.%(ext)s'),
        'format': 'bestaudio',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
        info = ydl.extract_info(url, download=True)
        video_file = ydl.prepare_filename(info)
    
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_file = ydl.prepare_filename(info)
    
    # Merge
    base_name = os.path.splitext(video_file)[0].replace("_video", "")
    output_file = base_name + "_full.mp4"
    
    if merge_video_audio(video_file, audio_file, output_file):
        # Delete temp files
        os.remove(video_file)
        os.remove(audio_file)
        print(f"[Done] Output: {output_file}")
        return output_file
    
    return None


# Convenient functions
__all__ = [
    'FFmpegManager',
    'merge_video_audio',
    'process_bilibili_video',
]
