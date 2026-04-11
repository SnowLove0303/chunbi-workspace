#!/usr/bin/env python3
"""
Video Workflow - Installation Script
Auto-configure environment and install dependencies
"""

import subprocess
import sys

def install_requirements():
    """Install Python dependencies"""
    packages = ['yt-dlp', 'requests', 'urllib3']
    
    for package in packages:
        print(f"[Install] {package}...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', package])
    
    print("[OK] Dependencies installed")

def setup_ffmpeg():
    """Pre-download ffmpeg"""
    sys.path.insert(0, r'F:\openclaw1\.openclaw\workspace\skills\video-workflow')
    from video_workflow import FFmpegManager
    
    if FFmpegManager.is_installed():
        print("[OK] ffmpeg already installed")
        return
    
    print("[Setup] Installing ffmpeg...")
    if FFmpegManager.download():
        print("[OK] ffmpeg installed successfully")
    else:
        print("[WARN] ffmpeg auto-install failed, will retry on first use")

def main():
    print("=" * 50)
    print("Video Workflow Installer")
    print("=" * 50)
    print()
    
    # Install dependencies
    install_requirements()
    
    # Try to install ffmpeg
    setup_ffmpeg()
    
    print()
    print("=" * 50)
    print("Installation Complete!")
    print("=" * 50)
    print()
    print("Usage:")
    print("  from video_workflow import process_bilibili_video")
    print("  process_bilibili_video('https://www.bilibili.com/video/BVxxxxx')")

if __name__ == '__main__':
    main()
