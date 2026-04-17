"""
视频下载模块
使用 yt-dlp 下载视频
"""

import os
import yt_dlp

class VideoDownloader:
    """视频下载器"""
    
    SUPPORTED_SITES = [
        'bilibili.com',
        'youtube.com',
        'youtu.be',
        'twitter.com',
        'x.com',
    ]
    
    @staticmethod
    def download(url, output_dir="F:/下载", format_type="best"):
        """
        下载视频
        
        Args:
            url: 视频 URL
            output_dir: 输出目录
            format_type: 下载格式 (best/bestvideo/bestaudio/worst)
        
        Returns:
            下载的文件路径
        """
        os.makedirs(output_dir, exist_ok=True)
        
        ydl_opts = {
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'format': format_type,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
        
        return file_path
    
    @staticmethod
    def download_video_audio_separate(url, output_dir="F:/下载"):
        """
        分别下载视频和音频（用于需要合并的情况）
        
        Returns:
            (video_path, audio_path)
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # 下载视频（无音频）
        ydl_opts_video = {
            'outtmpl': os.path.join(output_dir, '%(title)s_video_only.%(ext)s'),
            'format': 'bestvideo',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
            info = ydl.extract_info(url, download=True)
            video_path = ydl.prepare_filename(info)
        
        # 下载音频
        ydl_opts_audio = {
            'outtmpl': os.path.join(output_dir, '%(title)s_audio_only.%(ext)s'),
            'format': 'bestaudio',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
            info = ydl.extract_info(url, download=True)
            audio_path = ydl.prepare_filename(info)
        
        return video_path, audio_path
    
    @staticmethod
    def get_video_info(url):
        """获取视频信息（不下载）"""
        ydl_opts = {'quiet': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        return {
            'title': info.get('title'),
            'duration': info.get('duration'),
            'uploader': info.get('uploader'),
            'formats': len(info.get('formats', [])),
        }
